// .NET 8 executable QA for the REAL shared NinjaTrader V3 Boolean helper.
// This file is NOT copied into NinjaTrader Strategies. It compiles and runs
// NQNativeBooleanCanonicalV3.cs (unchanged) in the GitHub Actions runner.
using System;
using NinjaTrader.NinjaScript.Strategies;

public static class NQCanonicalizationConsoleTest
{
    private static int tested;
    private static void Eq<T>(T x,T y,string message)
    {
        tested++;
        if (!object.Equals(x,y))
            throw new Exception(message + ": " + x + " != " + y);
    }

    private static NQCanonicalResultV3 Run(
        int count,int[] type,int[] period,int[] ops,
        int reverse=0,int stop=20,int target=32,int daily=2)
    {
        return NQNativeBooleanCanonicalV3.Analyze(
            count,type,period,ops,reverse,stop,target,daily);
    }

    private static void ExpectArgument(Action action,string message)
    {
        tested++;
        try {action();}
        catch (ArgumentException) {return;}
        throw new Exception("Should have failed closed: "+message);
    }

    public static int Main()
    {
        // User's actual S0.48 winning *ranked* V2 genotype is a loser;
        // A=WMA slope18, B=RSI band6, C=WMA slope18, D=MA cross30.
        // ((A OR B) AND A) AND D == A AND D.
        var bad = Run(4,new[]{2,7,2,9},new[]{18,6,18,30},
                      new[]{1,0,0},1);
        var simple = Run(2,new[]{2,9},new[]{18,30},new[]{0},1);
        Eq(bad.EffectiveLeaves,2,"4 -> 2 effective leaves");
        Eq(bad.ActiveLeaves,4,"All 4 slots declared");
        Eq(bad.IsRedundant,true,"Absorption flag");
        Eq(simple.IsRedundant,false,"Simple AND is nonredundant");
        Eq(bad.BooleanKey,simple.BooleanKey,"Absorption truth signatures");
        Eq(bad.RuntimeKey,simple.RuntimeKey,"Same warmup and exits");
        Eq(bad.Fingerprint,simple.Fingerprint,"Stable id for equivalent runtime");

        // Different inactive genes must not change any identity or readiness.
        var singleA=Run(1,new[]{2,7,9,3},new[]{18,40,55,90},new[]{1,1,1});
        var singleB=Run(1,new[]{2,4,0,1},new[]{18,5,7,21},new[]{0,0,0});
        Eq(singleA.RuntimeKey,singleB.RuntimeKey,"Inactive slots irrelevant");
        Eq(singleA.EffectiveLeaves,1,"single leaf");
        Eq(singleA.WarmupBars,22,"WMA n18 readiness");

        // Commutative AND and OR are equivalent if leaves swapped.
        var ab=Run(2,new[]{2,4},new[]{18,12},new[]{0});
        var ba=Run(2,new[]{4,2},new[]{12,18},new[]{0});
        Eq(ab.RuntimeKey,ba.RuntimeKey,"AND commutation");
        var ao=Run(2,new[]{2,4},new[]{18,12},new[]{1});
        var oa=Run(2,new[]{4,2},new[]{12,18},new[]{1});
        Eq(ao.RuntimeKey,oa.RuntimeKey,"OR commutation");
        Eq(ab.BooleanKey==ao.BooleanKey,false,"AND versus OR distinct");

        // Proof is for Boolean logic only. The extra redundant long
        // lookback may delay readiness -> separate RUNTIME identity.
        var longer = Run(4,new[]{2,9,2,9},new[]{18,110,18,30},
                          new[]{1,0,0},1);
        Eq(longer.BooleanKey,simple.BooleanKey,"Bool redundant slow branch");
        Eq(longer.RuntimeKey==simple.RuntimeKey,false,
            "Different warmup does not imply same trades");
        Eq(longer.WarmupBars,224,"Slow type9 readiness 2n+4");
        Eq(longer.IsRedundant,true,"Slow redundant boolean leaf flagged");

        // Reverse, stop, target, daily risk make distinct strategy keys.
        Eq(simple.BooleanKey,Run(2,new[]{2,9},new[]{18,30},
            new[]{0},0).BooleanKey,"Signal ignores reverse");
        Eq(simple.RuntimeKey==Run(2,new[]{2,9},new[]{18,30},
            new[]{0},0).RuntimeKey,false,"Reverse trading identity");
        Eq(simple.RuntimeKey==Run(2,new[]{2,9},new[]{18,30},
            new[]{0},1,21).RuntimeKey,false,"Stop differentiates");
        Eq(simple.RuntimeKey==Run(2,new[]{2,9},new[]{18,30},
            new[]{0},1,20,33).RuntimeKey,false,"Target differentiates");
        Eq(simple.RuntimeKey==Run(2,new[]{2,9},new[]{18,30},
            new[]{0},1,20,32,1).RuntimeKey,false,"Daily cap differentiates");

        // All 4 uniquely essential leaves should remain 4.
        var full=Run(4,new[]{0,1,2,3},new[]{12,14,16,18},
                     new[]{1,1,1});
        Eq(full.EffectiveLeaves,4,"4 distinct active OR leaves");
        Eq(full.IsRedundant,false,"No over-pruning essential leaves");

        // Same slot repetition handled, no duplicate inflation.
        var twoSame=Run(2,new[]{2,2},new[]{18,18},new[]{0});
        Eq(twoSame.EffectiveLeaves,1,"A AND A = A");
        Eq(twoSame.BooleanKey,singleA.BooleanKey,"Repeated AND reduces");
        var twoSameOr=Run(2,new[]{2,2},new[]{18,18},new[]{1});
        Eq(twoSameOr.BooleanKey,singleA.BooleanKey,"A OR A = A");
        Eq(twoSame.IsRedundant,true,"Repeated leaves marked");

        // Structural gates fail closed on invalid genes.
        ExpectArgument(()=>Run(0,new[]{0},new[]{12},new[]{0}),"empty");
        ExpectArgument(()=>Run(5,new[]{0,1,2,3,4},
            new[]{8,8,8,8,8},new[]{0,0,0,0}),"5 slots");
        ExpectArgument(()=>Run(2,new[]{0,11},new[]{12,12},
            new[]{0}),"bad indicator");
        ExpectArgument(()=>Run(2,new[]{0,1},new[]{1,12},
            new[]{0}),"bad lookback");
        ExpectArgument(()=>Run(2,new[]{0,1},new[]{12,12},
            new[]{2}),"bad op");
        ExpectArgument(()=>Run(1,new[]{0},new[]{12},new int[0],
            0,0),"zero risk stop");

        // Same genes must always make the same digest across repeats.
        for(int i=0;i<1000;i++)
            Eq(Run(4,new[]{2,7,2,9},new[]{18,6,18,30},
                new[]{1,0,0},1).Fingerprint,bad.Fingerprint,
                "deterministic canonical fingerprint");

        Console.WriteLine("NQ_V3_CANONICAL_REAL_CSHARP_TESTS_PASSED="+tested);
        Console.WriteLine("NQ_V3_S048_EXAMPLE "+bad.Fingerprint);
        Console.WriteLine("V3_GENERIC_CSHARP_PROVEN_NT8_HOST_COMPILE_NOT_VERIFIED");
        return 0;
    }
}
