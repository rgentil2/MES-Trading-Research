// V19 full headless GA + M1 economic fill + bounded signal cache +
// resume journal; synthetic development bars only, NOT NQ market data.
// Tests old V11 and V18 trade receipts against expanded V19, plus
// direct full-source/cached parity on new 1320-condition signal set.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;

internal static class V19IntegrationTest
{
    static void A(bool yes,string detail)
    {if(!yes)throw new Exception("NQ_V19_PIPELINE_FAIL "+detail);}
    static List<NQTimedBarV12> Bars()
    {
        var b=new List<NQTimedBarV12>();
        var rng=new Random(20261106);
        double p=15000;
        DateTime first=new DateTime(2021,6,1);
        for(int d=0;d<9;d++)
            for(int k=0;k<210;k++)
            {
                double o=p;
                p+=0.35+Math.Sin((k+d*13)*0.08)*2.4+
                    (rng.NextDouble()-0.5)*4;
                b.Add(new NQTimedBarV12(
                    first.AddDays(d).AddHours(8).AddMinutes(k),
                    new NQBarV11(o,Math.Max(o,p)+0.65,
                        Math.Min(o,p)-0.65,p,50+rng.Next(1500))));
            }
        return b;
    }
    static NQEvolutionConfigV12 Cfg()
    {
        return new NQEvolutionConfigV12{
            Population=48,Generations=4,Elites=4,
            Tournament=3,ImmigrantPercent=25,
            MutationPercent=18,Seed=20261106,
            MaxAttempts=20000,ResetAfterStagnantGenerations=3
        };
    }
    static readonly int[] BaselineV19={
        2,396,12,429,12,737,12,1284,12,
        0,0,0,0,20,32,2,0,14,15,25
    };
    static readonly int[] BaselineV18={
        2,132,12,143,12,198,12,231,12,
        0,0,0,0,20,32,2,0,14,15,25
    };
    static void Compare(NQHistoricalResultV12 a,NQHistoricalResultV12 b,
                        string context)
    {
        A(a.Valid==b.Valid && a.Reason==b.Reason &&
          Math.Abs(a.Net-b.Net)<1e-7 && a.Score==b.Score &&
          a.Trades.Count==b.Trades.Count &&
          a.Executed.Count==b.Executed.Count,
          "equal M1 economics "+context);
        for(int i=0;i<a.Trades.Count;i++)
            A(a.Trades[i].EntryTime==b.Trades[i].EntryTime &&
              a.Trades[i].ExitTime==b.Trades[i].ExitTime &&
              Math.Abs(a.Trades[i].NetProfitUSD-
                       b.Trades[i].NetProfitUSD)<1e-7,
              "same M1 roundtrip and fees "+context+" #"+i);
    }
    static int DirectDirection(IList<NQTimedBarV12> all,
                               int sourceIndex,int type,int period)
    {
        DateTime day=all[sourceIndex].Time.Date;
        var prefix=new List<NQBarV11>();
        for(int j=sourceIndex;j>=0&&all[j].Time.Date==day;j--)
        {
            var t=all[j].Time;
            if(t.Hour*100+t.Minute<930)break;
            if(t.Hour*100+t.Minute<=1129)
                prefix.Add(all[j].Bar);
        }
        prefix.Reverse();
        bool bull,bear;
        if(!NQNativeConditionCatalogV19.TryEvaluate(prefix,
            type,period,out bull,out bear))
            return 0;
        A(!bull||!bear,"cannot be both bull/bear");
        return bull?1:bear?-1:0;
    }
    public static int Main()
    {
        var rows=Bars();
        var v19=new NQNativeExpandedResearchV19(
            rows,BaselineV19,Cfg(),true,false,24*1024*1024);
        var v18=new NQNativeExpandedResearchV18(
            rows,BaselineV18,Cfg(),true,false,24*1024*1024);
        var v11=new NQNativeSignalCacheV14(
            rows,24*1024*1024);

        int old=0,mid=0;
        var g11=new NQUniqueSearchV11(
            NQEvolutionEngineV12.DefaultDomains(BaselineV18,true),
            20261106);
        while(old<18)
        {
            var candidate=g11.TryNext();
            if(candidate==null)continue;
            Compare(v11.Evaluate(candidate.Genes),
                v19.Evaluate(candidate.Genes),"V11 "+old);
            old++;
            A(g11.Attempted<20000,"bounded V11 structural sample");
        }
        // V18 types 132..395 cannot enter V11's own canonicalizer.
        // Sample these via the V18 extended canonicalizer explicitly.
        var g18=new NQEvolutionEngineV12(
            NQNativeExitCanonicalV18.DefaultDomains(BaselineV18,true),
            new NQEvolutionConfigV12{
                Population=40,Generations=2,Elites=4,
                Tournament=3,Seed=20261106,MaxAttempts=5000
            },NQNativeExitCanonicalV18.Analyze)
            .Run(genome=>0);
        foreach(var candidate in g18.Evaluated)
        {
            if(mid>=18)break;
            var genes=candidate.Genome.Genes;
            bool hasNew=Enumerable.Range(0,genes[0])
                .Any(k=>genes[1+2*k]>=132);
            if(!hasNew)continue;
            Compare(v18.Evaluate(genes),v19.Evaluate(genes),
                "V18 "+mid);
            mid++;
        }
        A(old==18&&mid==18,
          "36 preserved V11/V18 economic simulation outcomes");

        // Validate the V19-only cache is not changing V12 entry/exit
        // rules compared to a direct signal calculation on RTH prefixes.
        int direct=0;
        foreach(int family in new[]{36,44,57,65,78,88,99,108,115,119})
        {
            var genes=(int[])BaselineV19.Clone();
            genes[0]=1;
            genes[1]=family*11;
            genes[2]=12;
            var cached=v19.Evaluate(genes);
            var independent=NQNativeHistoricalEvaluatorV12.EvaluateCustom(
                rows,genes,
                (index,type,period)=>DirectDirection(
                    rows,index,type,period),
                false,null,NQNativeExitCanonicalV19.Analyze);
            Compare(cached,independent,"direct vs cached family "+family);
            direct++;
        }
        A(direct==10,"direct full-source M1 parity for ten new families");

        var ga=v19.Run();
        A(ga.Evaluated.Count==180&&ga.GenerationBest.Count==4,
          "full expanded 4-generation actual V12 score callback");
        A(ga.Evaluated.Select(x=>x.Genome.Canonical.RuntimeKey)
            .Distinct(StringComparer.Ordinal).Count()==180,
          "V19 canonical dedup across generations");
        A(ga.Evaluated.All(x=>x.Genome.Canonical.RuntimeKey
            .StartsWith("EXCANv19:")),
          "all new genome IDs versioned");
        var families=new HashSet<int>();
        foreach(var candidate in ga.Evaluated)
            for(int k=0;k<candidate.Genome.Genes[0];k++)
                families.Add(candidate.Genome.Genes[1+2*k]/11);
        A(families.Count>=70&&families.Any(x=>x>=100),
          "genetic search explores new V19 families");
        foreach(var candidate in ga.Evaluated.Take(10))
            A(candidate.Score==v19.Evaluate(
                candidate.Genome.Genes).Score,
              "individual GA score is actual V12 M1 scorer");

        string path=Path.Combine(Path.GetTempPath(),
            "nq_v19_"+Guid.NewGuid().ToString("N")+".tsv");
        try
        {
            var persisted=v19.RunWithJournal(path,new string('a',64));
            A(persisted.Evaluated.Count==180&&
              File.ReadAllLines(path).Length==181,
              "all V19 GA fitness outcomes persisted");
            var replay=v19.RunWithJournal(path,new string('a',64));
            A(File.ReadAllLines(path).Length==181,
              "identical source/scores reused without appending");
            A(persisted.Evaluated.Zip(replay.Evaluated,(x,y)=>
                x.Score==y.Score&&
                x.Genome.Canonical.RuntimeKey==
                y.Genome.Canonical.RuntimeKey).All(z=>z),
              "same deterministic V19 journal replay");
            try
            {
                v19.RunWithJournal(path,new string('b',64));
                throw new Exception("SOURCE_FINGERPRINT_LEAK");
            }
            catch(InvalidOperationException e)
            {A(e.Message.Contains("MISMATCH"),
                "V19 journal refuses changed historical source");}
        }
        finally
        {if(File.Exists(path))File.Delete(path);}

        Console.WriteLine("NQ_V19_INTEGRATED_PASS families=120 "+
            "conditions=1320 legacyV11Parity="+old+
            " legacyV18Parity="+mid+
            " sourceVsCache="+direct+
            " gaUnique="+ga.Evaluated.Count+
            " uniqueFamilies="+families.Count+
            " persistedRestart=TRUE V12CostFillsUnchanged=TRUE");
        Console.WriteLine("SYNTHETIC_M1_AND_V12_SIMULATED_FILLS_NOT_NATIVE_NT8_BACKTEST");
        return 0;
    }
}
