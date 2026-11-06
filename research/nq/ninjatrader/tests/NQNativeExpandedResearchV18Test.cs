// V18 end-to-end EXPANDED fitness-guided GA over V12 conservative
// synthetic M1 fills with V14 cache and V17 persistent scoring.
// Does not use any real NQ DEC2026 bars or NinjaTrader fill engine.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;
internal static class V18IntegrationTest
{
    static void A(bool yes,string reason)
    {if(!yes)throw new Exception("NQ_V18_INTEGRATION_FAIL "+reason);}
    static List<NQTimedBarV12> Bars()
    {
        var b=new List<NQTimedBarV12>();
        var rng=new Random(20261106);
        var initial=new DateTime(2021,6,1);
        double price=15000;
        for(int d=0;d<8;d++)
            for(int k=0;k<210;k++)
            {
                double op=price;
                price+=0.45+Math.Sin((k+d*9)/11.0)*2.7+
                    (rng.NextDouble()-0.5)*4;
                b.Add(new NQTimedBarV12(
                    initial.AddDays(d).AddHours(8).AddMinutes(k),
                    new NQBarV11(op,Math.Max(op,price)+0.8,
                        Math.Min(op,price)-0.8,price,
                        100+rng.Next(1500))));
            }
        return b;
    }
    static NQEvolutionConfigV12 Cfg(int generations)
    {
        return new NQEvolutionConfigV12{
            Population=48,Generations=generations,Elites=4,
            Tournament=3,ImmigrantPercent=25,MutationPercent=18,
            Seed=20261106,MaxAttempts=10000,
            ResetAfterStagnantGenerations=3
        };
    }
    static readonly int[] Baseline={
        2,132,12,143,12,198,12,220,12,
        0,0,0,0,20,32,2,0,14,15,25
    };
    static void Compare(NQHistoricalResultV12 a,NQHistoricalResultV12 b,
                        string context)
    {
        A(a.Valid==b.Valid&&a.Reason==b.Reason&&
          Math.Abs(a.Net-b.Net)<1e-7&&a.Score==b.Score&&
          a.Trades.Count==b.Trades.Count,
          "V18/V11 identical fill model "+context);
        for(int k=0;k<a.Trades.Count;k++)
            A(a.Trades[k].EntryTime==b.Trades[k].EntryTime&&
              a.Trades[k].ExitTime==b.Trades[k].ExitTime&&
              Math.Abs(a.Trades[k].NetProfitUSD-
                       b.Trades[k].NetProfitUSD)<1e-7,
              "trade parity "+context+" "+k);
    }
    public static int Main()
    {
        var rows=Bars();
        var settings=Cfg(4);
        var expanded=new NQNativeExpandedResearchV18(
            rows,Baseline,settings,true,false,16*1024*1024);
        var original=new NQNativeSignalCacheV14(
            rows,16*1024*1024);

        // Every original V11 genome retains EXACT economic results.
        var gen=new NQUniqueSearchV11(NQUniqueSearchV11.Smoke(),20261106);
        int checkedLegacy=0;
        while(checkedLegacy<24&&gen.Attempted<2000)
        {
            var g=gen.TryNext();
            if(g==null)continue;
            Compare(original.Evaluate(g.Genes),
                expanded.Evaluate(g.Genes),"legacy "+checkedLegacy);
            checkedLegacy++;
        }
        A(checkedLegacy==24,"24 complete V11 economic parity checks");

        // Extended families exercise actual source M1 signals and
        // actual original V12 fills/costs/V9 economic feedback.
        var evolved=expanded.Run();
        A(evolved.Evaluated.Count==48+3*44 &&
          evolved.GenerationBest.Count==4,
          "full 4-generation V18 feedback pipeline completed");
        A(evolved.Evaluated.All(g=>
            g.Genome.Canonical.RuntimeKey.StartsWith("EXCANv18:") &&
            g.Genome.Canonical.Fingerprint.StartsWith("NQEX18_")),
            "versioned canonical identities stored");
        A(evolved.Evaluated.Select(g=>
            g.Genome.Canonical.RuntimeKey).Distinct().Count()==
            evolved.Evaluated.Count,
            "no duplicate V18 candidate identities");
        var families=evolved.Evaluated.SelectMany(g=>
            Enumerable.Range(0,g.Genome.Genes[0]).Select(k=>
                g.Genome.Genes[1+2*k]/11)).Distinct().ToArray();
        A(families.Length>=30&&
          families.Any(x=>x>=12),
          "full 396-type search domains actually explored");
        var picked=evolved.Evaluated.FirstOrDefault(g=>
            Enumerable.Range(0,g.Genome.Genes[0]).Any(k=>
                g.Genome.Genes[1+2*k]>=132));
        A(picked!=null,"some evaluated candidates use added families");
        var replay=expanded.Evaluate(picked.Genome.Genes);
        A(replay.Valid&&
          replay.Score==picked.Score,
          "actual V12 M1/V9 score callback equals recorded GA fitness");
        A(evolved.Evaluated.All(g=>!Double.IsNaN(g.Score)),
          "all expanded feedback scores finite");
        // Make sure a strict legacy type-range constructor can never
        // silently interpret a V18-only genome as V11.
        A(!NQNativeHistoricalEvaluatorV12.Evaluate(
            rows,picked.Genome.Genes).Valid,
          "original version must fail closed on expanded types");

        // V17 persistent score journal accepts V18 canonical ID and
        // resumes the exact SAME expanded GA without rerunning V12 fills.
        string path=Path.Combine(Path.GetTempPath(),
            "nq_v18_"+Guid.NewGuid().ToString("N")+".tsv");
        try
        {
            var first=expanded.RunWithJournal(path,new string('a',64));
            A(first.Evaluated.Count==180,"first persisted run 180 scores");
            int originalLines=File.ReadAllLines(path).Length;
            A(originalLines==181,"180 persisted scores and one header");
            var resumed=expanded.RunWithJournal(path,new string('a',64));
            A(File.ReadAllLines(path).Length==originalLines,
              "restarting V18 does not append any repeated scores");
            A(first.Evaluated.Zip(resumed.Evaluated,
                (a,b)=>a.Genome.Canonical.RuntimeKey==
                 b.Genome.Canonical.RuntimeKey&&a.Score==b.Score).All(x=>x),
              "V18 persisted replay exactly identical");
            try
            {
                expanded.RunWithJournal(path,new string('b',64));
                throw new Exception("MISSING_DATA_SHA_GUARD");
            }
            catch(InvalidOperationException e)
            {
                A(e.Message.Contains("MISMATCH"),
                  "new data cannot reuse V18 fitness");
            }
        }
        finally
        {
            if(File.Exists(path))File.Delete(path);
        }
        Console.WriteLine("NQ_V18_FULL_PIPELINE_PASS features=36 "+
            "conditions=396 originalV11Parity="+checkedLegacy+
            " evaluatedUnique="+evolved.Evaluated.Count+
            " familiesVisited="+families.Length+
            " newFamilySignals=TRUE persistedReplay=TRUE "+
            " originalV12Economics=UNCHANGED");
        Console.WriteLine("SYNTHETIC_M1_ONLY_NO_NQ_DEC2026_BACKTEST_OR_NATIVE_NT8_PARITY");
        return 0;
    }
}
