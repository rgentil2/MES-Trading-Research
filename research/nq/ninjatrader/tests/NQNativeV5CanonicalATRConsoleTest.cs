// S0.58 executable actual production C# V5 canonicalization/ATR exit tests.
using System;
using System.Collections.Generic;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;

internal static class Program
{
    private static int checks=0;
    static void T(bool x,string what)
    {
        checks++;
        if(!x)throw new Exception("V5 QA FAIL: "+what);
    }
    static int[] Base(int count=2,int mode=0)
    {
        return new int[]{count,2,18,7,6,2,18,9,30,
            1,0,0,1,20,32,2,mode,14,15,25};
    }
    static int[] Change(int[] g,int index,int value)
    {
        var k=(int[])g.Clone();k[index]=value;return k;
    }
    static string Key(int[] g){return NQNativeExitCanonicalV5.Analyze(g).RuntimeKey;}
    static void ATRCase(int mode,double atr,int stop,int target,bool accepted)
    {
        int sl,tp;
        bool ok=NQNativeATRExitMathV5.TryCompute(mode,atr,0.25,
            20,32,15,25,out sl,out tp);
        T(ok==accepted,"ATR success mode"+mode+" atr"+atr);
        if(ok){T(sl==stop,"SL "+mode+" "+atr);T(tp==target,"TP "+mode+" "+atr);}
    }
    public static int Main()
    {
        var fixedG=Base();
        var baseline=NQNativeExitCanonicalV5.Analyze(fixedG);
        var baseV3=NQNativeBooleanCanonicalV3.Analyze(2,
            new[]{2,7,2,9},new[]{18,6,18,30},
            new[]{1,0,0},1,20,32,2);
        T(baseline.BooleanKey==baseV3.BooleanKey,"V3 Boolean unchanged");
        T(baseline.WarmupBars==baseV3.WarmupBars,"mode0 V3 warmup unchanged");
        T(baseline.EffectiveLeaves==2&&!baseline.IsRedundant,"mode0 2 leaves");
        T(Key(fixedG)==Key(Change(fixedG,17,28)),"mode0 ignores ATR period");
        T(Key(fixedG)==Key(Change(fixedG,18,30)),"mode0 ignores ATR SL multiplier");
        T(Key(fixedG)==Key(Change(fixedG,19,50)),"mode0 ignores ATR TP multiplier");
        T(Key(fixedG)!=Key(Change(fixedG,13,21)),"mode0 uses fixed SL");
        T(Key(fixedG)!=Key(Change(fixedG,14,33)),"mode0 uses fixed TP");
        var m1=Base(2,1);
        T(Key(m1)!=Key(fixedG),"ATR mode 1 differs from fixed");
        T(Key(m1)==Key(Change(m1,13,21)),"mode1 ignores fixed stop");
        T(Key(m1)==Key(Change(m1,19,50)),"mode1 ignores ATR target");
        T(Key(m1)!=Key(Change(m1,14,33)),"mode1 uses fixed target");
        T(Key(m1)!=Key(Change(m1,17,28)),"mode1 uses ATR period");
        T(Key(m1)!=Key(Change(m1,18,30)),"mode1 uses ATR stop mult");
        var m2=Base(2,2);
        T(Key(m2)!=Key(m1),"ATR TP vs fixed TP");
        T(Key(m2)==Key(Change(m2,13,21)),"mode2 ignores fixed stop");
        T(Key(m2)==Key(Change(m2,14,33)),"mode2 ignores fixed target");
        T(Key(m2)!=Key(Change(m2,19,50)),"mode2 uses ATR target");
        var m3=Base(2,3);
        T(Key(m3)!=Key(m2),"NoTP vs ATR TP");
        T(Key(m3)==Key(Change(m3,14,33)),"mode3 ignores fixed target");
        T(Key(m3)==Key(Change(m3,19,50)),"mode3 ignores ATR target");
        T(Key(m3)==Key(Change(m3,13,21)),"mode3 ignores fixed stop");
        T(NQNativeExitCanonicalV5.Analyze(Base(3)).IsRedundant,
            "V3 absorption count3 survives V5");
        T(NQNativeExitCanonicalV5.Analyze(Base(4)).IsRedundant,
            "V3 absorption count4 survives V5");

        int sl,tp;
        T(NQNativeATRExitMathV5.TryCompute(0,0.0,0.25,20,32,15,25,out sl,out tp)
            && sl==20 && tp==32,"fixed 20/32 parity");
        ATRCase(1,5.0,30,32,true);
        ATRCase(2,5.0,30,50,true);
        ATRCase(3,5.0,30,0,true);
        ATRCase(2,0.0,0,0,false);
        ATRCase(2,double.NaN,0,0,false);
        ATRCase(2,double.PositiveInfinity,0,0,false);
        ATRCase(2,10.0,0,0,false); // 60 stop ticks exceed 55.
        T(NQNativeATRExitMathV5.TryCompute(2,3.375,0.25,
            20,32,15,25,out sl,out tp)&&sl==21&&tp==34,
            "ceil ATR stop 20.25->21, TP 33.75->34");
        T(!NQNativeATRExitMathV5.TryCompute(1,5,0.25,
            20,0,15,25,out sl,out tp),"mode1 requires TP");
        T(!NQNativeATRExitMathV5.TryCompute(2,5,0.0,
            20,32,15,25,out sl,out tp),"invalid tick size");
        T(!NQNativeATRExitMathV5.TryCompute(2,5,0.25,
            20,32,5,25,out sl,out tp),"invalid stop mult");

        var ranges=NQUniqueSearchV5.Smoke();
        T(ranges.Length==20&&ranges[16].Count==4,"20 genes and 4 modes");
        // Broaden a meaningful subset without expensive NinjaTrader fills.
        ranges[17]=new NQGeneRangeV5(7,28,7);
        ranges[18]=new NQGeneRangeV5(10,30,10);
        ranges[19]=new NQGeneRangeV5(10,50,10);
        var gen=new NQUniqueSearchV5(ranges,20261102);
        var unique=new HashSet<string>(StringComparer.Ordinal);
        var sequence=new List<string>();
        for(int i=0;i<25000 && sequence.Count<1000;i++)
        {
            var g=gen.TryNext();
            if(g==null)continue;
            T(!g.Canonical.IsRedundant,"accepted Boolean essential");
            T(unique.Add(g.Canonical.RuntimeKey),"unique runtime identity");
            for(int k=0;k<20;k++)
                T(g.Genes[k]>=ranges[k].Min && g.Genes[k]<=ranges[k].Max &&
                  (g.Genes[k]-ranges[k].Min)%ranges[k].Step==0,
                  "gene in user range");
            T(g.Canonical.Fingerprint.StartsWith("NQEX5_"),"V5 hash prefix");
            sequence.Add(g.Canonical.Fingerprint);
        }
        T(sequence.Count==1000,"1000 unique V5 identities generated");
        T(gen.Attempted==gen.GeneratedUnique+gen.RedundantSkipped+
          gen.DuplicateSkipped+gen.InvalidSkipped,"accounting");
        var replay=new NQUniqueSearchV5(ranges,20261102);
        foreach(var id in sequence)
        {
            NQGenomeV5 g;
            do{g=replay.TryNext();}while(g==null);
            T(g.Canonical.Fingerprint==id,"replay deterministic");
        }
        // Force fixed exit mode and vary ignored ATR genes; one actual
        // runtime identity even though many nominal random configurations.
        var domain=new NQGeneRangeV5[20];
        var genes=Base(2,0);
        for(int k=0;k<20;k++)domain[k]=NQUniqueSearchV5.Fixed(genes[k]);
        domain[17]=new NQGeneRangeV5(7,28,7);
        domain[18]=new NQGeneRangeV5(10,30,10);
        domain[19]=new NQGeneRangeV5(10,50,10);
        var inactive=new NQUniqueSearchV5(domain,1234);
        for(int i=0;i<200;i++) inactive.TryNext();
        T(inactive.GeneratedUnique==1&&inactive.DuplicateSkipped==199,
           "ignored ATR gene changes do not create false uniqueness");
        Console.WriteLine("NQ_S058_V5_PRODUCTION_CPPURE_QA_PASS="+checks);
        Console.WriteLine("UNIQUE="+gen.GeneratedUnique+" ATTEMPTS="+gen.Attempted+
            " REDUNDANT="+gen.RedundantSkipped+" DUPLICATES="+gen.DuplicateSkipped);
        Console.WriteLine("ACTUAL_NINJATRADER_NATIVE_COMPILE_BACKTEST_PENDING");
        return 0;
    }
}
