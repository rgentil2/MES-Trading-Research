// S0.54 - Real executable .NET8 tests of production V3 canonicalizer
// and production V4 unique candidate generator, NO NinjaTrader assemblies.
using System;
using System.Collections.Generic;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;

internal static class Program
{
    private static int assertions;
    private static void Assert(bool ok,string text)
    {
        assertions++;
        if(!ok)throw new InvalidOperationException(text);
    }

    private static int[] Base(int count)
    {
        return new int[] {count,2,18,7,6,2,18,9,30,1,0,0,1,20,32,2};
    }

    public static int Main()
    {
        var ranges=NQUniqueSearchV4.Smoke();
        Assert(ranges.Length==16,"16 genes");
        Assert(ranges[0].Count==4,"1-4 conditions");
        Assert(ranges[2].Count==5,"periods 6,12,18,24,30");
        Assert(ranges[13].At(0)==20,"stop fixed");
        Assert(ranges[14].At(0)==32,"target fixed");

        // Crosscheck first real V2 winner's BOOLEAN redundancy:
        var known=NQUniqueSearchV4.AnalyzeGenes(Base(4));
        Assert(known.IsRedundant && known.EffectiveLeaves==2,
            "S0.48 4 leaves collapse to 2");
        var c2=NQUniqueSearchV4.AnalyzeGenes(Base(2));
        Assert(!c2.IsRedundant && c2.EffectiveLeaves==2,
            "S0.53 valid 2-leaf case");
        var c3=NQUniqueSearchV4.AnalyzeGenes(Base(3));
        Assert(c3.IsRedundant && c3.EffectiveLeaves==1,
            "S0.53 invalid 3-leaf case");

        var gen=new NQUniqueSearchV4(ranges,20261102);
        var ids=new HashSet<string>(StringComparer.Ordinal);
        var all=new List<NQGenomeV4>();
        for(int i=0;i<20000 && all.Count<1000;i++)
        {
            var g=gen.TryNext();
            if(g==null)continue;
            Assert(!g.Canonical.IsRedundant,"All produced are essential");
            Assert(ids.Add(g.Canonical.RuntimeKey),"No identical runtime keys");
            Assert(g.Canonical.EffectiveLeaves==g.Genes[0],
                "All active slots essential in returned genome");
            for(int j=0;j<16;j++)
                Assert(g.Genes[j]>=ranges[j].Min &&
                    g.Genes[j]<=ranges[j].Max &&
                    (g.Genes[j]-ranges[j].Min)%ranges[j].Step==0,
                    "Ranged parameter "+j);
            all.Add(g);
        }
        Assert(all.Count==1000,"1000 unique structures generated");
        Assert(gen.GeneratedUnique==1000,"Unique count exact");
        Assert(gen.Attempted>=1000,"Attempts >= accepted");
        Assert(gen.Attempted==gen.GeneratedUnique+
            gen.RedundantSkipped+gen.DuplicateSkipped+gen.InvalidSkipped,
            "Every attempt classified");

        // Same seed + same ranges => identical sequence and rejection profile.
        var deterministic=new NQUniqueSearchV4(ranges,20261102);
        foreach(var expected in all)
        {
            NQGenomeV4 candidate;
            do{candidate=deterministic.TryNext();}while(candidate==null);
            Assert(candidate.Canonical.Fingerprint==expected.Canonical.Fingerprint,
                "Replay seeded result exactly");
        }

        // Fixed count2, same A/B, and varying INACTIVE C/D does not yield
        // more than ONE unique runtime identity, because they cannot trade.
        var d=new NQGeneRangeV4[16];
        for(int i=0;i<16;i++)d[i]=NQUniqueSearchV4.Fixed(Base(2)[i]);
        d[5]=new NQGeneRangeV4(0,9,1);
        d[6]=new NQGeneRangeV4(6,30,6);
        d[7]=new NQGeneRangeV4(0,9,1);
        d[8]=new NQGeneRangeV4(6,30,6);
        d[10]=new NQGeneRangeV4(0,1,1);
        d[11]=new NQGeneRangeV4(0,1,1);
        var noFalseUnique=new NQUniqueSearchV4(d,123);
        for(int i=0;i<200;i++)noFalseUnique.TryNext();
        Assert(noFalseUnique.GeneratedUnique==1,
            "Inactive genes must not create false unique genotypes");
        Assert(noFalseUnique.DuplicateSkipped==199,
            "All after first are duplicates");

        // Forced A=C with count3, AB OR, BC AND: ALWAYS redundant,
        // so MUST NEVER call RunIteration in real NinjaTrader.
        var e=new NQGeneRangeV4[16];
        var fixedGenes=Base(3);
        for(int i=0;i<16;i++)e[i]=NQUniqueSearchV4.Fixed(fixedGenes[i]);
        e[4]=new NQGeneRangeV4(6,30,6); // Bperiod varies
        var alwaysBad=new NQUniqueSearchV4(e,777);
        for(int i=0;i<200;i++)Assert(alwaysBad.TryNext()==null,
            "Reject boolean absorption before execution");
        Assert(alwaysBad.GeneratedUnique==0 &&
            alwaysBad.RedundantSkipped==200,"Nothing enters expensive backtest");

        bool invalidThrown=false;
        try {new NQUniqueSearchV4(new NQGeneRangeV4[16],1);}
        catch(ArgumentException){invalidThrown=true;}
        Assert(invalidThrown,"invalid domain rejected");

        Console.WriteLine("NQ_S054_V4_PRODUCTION_CSHARP_TESTS_PASSED="+assertions);
        Console.WriteLine("UNIQUE_ACCEPTED="+gen.GeneratedUnique+
            " ATTEMPTED="+gen.Attempted+
            " DUPLICATES="+gen.DuplicateSkipped+
            " REDUNDANT="+gen.RedundantSkipped);
        Console.WriteLine("NQ_V4_NT8_ADAPTER_NOT_HOST_COMPILED_OR_BACKTESTED");
        return 0;
    }
}
