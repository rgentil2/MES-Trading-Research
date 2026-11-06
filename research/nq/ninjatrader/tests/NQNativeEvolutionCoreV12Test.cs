// V12 genetic engine deterministic synthetic benchmark. This is NOT a
// historical NQ backtest and cannot establish financial profitability.
using System;
using System.Collections.Generic;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;
internal static class V12EvolutionTest
{
    private static void Check(bool condition,string message)
    {if(!condition)throw new Exception("V12_QA_FAILED "+message);}

    private static double SyntheticObjective(NQGenomeV11 g)
    {
        int[] x=g.Genes;
        // Separable known target validates that selection, heredity and
        // mutation truly use performance from earlier generations.
        return 10000
            - 140*Math.Abs(x[0]-3)
            - 9*Math.Abs(x[1]-77)
            - 13*Math.Abs(x[2]-12)
            - 6*Math.Abs(x[3]-35)
            - 9*Math.Abs(x[4]-18)
            - 4*Math.Abs(x[5]-94)
            - 6*Math.Abs(x[7]-21)
            - 45*Math.Abs(x[12]-1)
            - 6*Math.Abs(x[13]-20)
            - 2*Math.Abs(x[14]-40)
            - 55*Math.Abs(x[16]-1);
    }

    private static NQEvolutionConfigV12 Config(int seed=20261105)
    {
        return new NQEvolutionConfigV12{
            Population=80,Generations=14,Elites=8,Tournament=4,
            ImmigrantPercent=20,MutationPercent=16,Seed=seed,
            MaxAttempts=50000,ResetAfterStagnantGenerations=4
        };
    }

    private static NQEvolutionSummaryV12 Run(int seed,bool explore=true)
    {
        int[] baseline={2,0,12,44,12,77,12,121,12,
            0,0,0,0,20,32,2,0,14,15,25};
        var domains=NQEvolutionEngineV12.DefaultDomains(baseline,explore);
        return new NQEvolutionEngineV12(domains,Config(seed))
            .Run(SyntheticObjective);
    }

    public static int Main()
    {
        var one=Run(20261105);
        var two=Run(20261105);
        Check(one.Evaluated.Count>900,"enough evaluated distinct runs");
        Check(one.Evaluated.Select(x=>x.Genome.Canonical.RuntimeKey)
            .Distinct(StringComparer.Ordinal).Count()==one.Evaluated.Count,
            "global canonical dedup across generations");
        Check(one.Evaluated.Select(x=>x.Genome.Canonical.Fingerprint)
            .Distinct(StringComparer.Ordinal).Count()==one.Evaluated.Count,
            "unique IDs across all generations");
        Check(one.Evaluated.All(x=>!x.Genome.Canonical.IsRedundant),
            "redundant Boolean logic must never be scored");
        Check(one.GenerationBest.Count==14,
            "all 14 genetic generations completed");
        Check(one.GenerationNew[0]==80,
            "first generation is exactly random population");
        Check(one.GenerationNew.Skip(1).All(n=>n==72),
            "8 elites are cached, not re-backtested each generation");
        Check(one.GenerationBest.Zip(one.GenerationBest.Skip(1),
            (a,b)=>b>=a).All(x=>x),"best-of-run never regresses");
        Check(one.GenerationBest.Last()>one.GenerationBest[0]+40,
            "real score-guided improvement from generation zero");
        Check(one.CrossoverChildren>100,"crossover genuinely occurred");
        Check(one.MutatedChildren>100,"mutation genuinely occurred");
        Check(one.ImmigrantChildren>100,"novel immigrants genuinely occurred");
        Check(one.Evaluated.Count==two.Evaluated.Count &&
            one.Evaluated.Zip(two.Evaluated,(a,b)=>
                a.Genome.Canonical.RuntimeKey==b.Genome.Canonical.RuntimeKey &&
                a.Score==b.Score).All(x=>x),"replay identical seed and score");
        Check(Math.Abs(one.Best.Score-two.Best.Score)<1e-9,
            "deterministic best and ranking");
        Check(one.Evaluated.All(x=>x.BirthGeneration>=0 &&
            x.BirthGeneration<14),"generation metadata valid");

        var flat=Run(20261105,false);
        int[] original={2,0,12,44,12,77,12,121,12,
            0,0,0,0,20,32,2,0,14,15,25};
        Check(flat.Evaluated.All(x=>Enumerable.Range(13,7)
            .All(i=>x.Genome.Genes[i]==original[i])),
            "frozen protective exits cannot mutate or crossover");
        Check(flat.Evaluated.Count>900,"frozen 1000 unique candidates");

        // Constant-fitness experiment must cause stagnation resets,
        // proving reset logic is reachable; no false profitability claim.
        var plateau=new NQEvolutionEngineV12(
            NQEvolutionEngineV12.DefaultDomains(original,true),
            new NQEvolutionConfigV12{
                Population=32,Generations=11,Elites=4,Tournament=3,
                ImmigrantPercent=15,MutationPercent=20,Seed=20261107,
                MaxAttempts=30000,ResetAfterStagnantGenerations=2
            }).Run(x=>0);
        Check(plateau.Resets>=3,"fitness stagnation triggers genetic reset");
        Check(plateau.GenerationBest.All(x=>x==0),
            "constant synthetic fitness cannot generate fake improvement");

        // Finite-score guards prevent NaN/Inf from selecting a parent.
        var invalidScore=new NQEvolutionEngineV12(
            NQEvolutionEngineV12.DefaultDomains(original,true),
            new NQEvolutionConfigV12{
                Population=16,Generations=2,Elites=2,Tournament=3,
                Seed=20261108,MaxAttempts=3000
            }).Run(x=>Double.NaN);
        Check(invalidScore.Evaluated.All(x=>x.Score==-1e12),
            "NaN scores always receive invalid floor");
        Check(invalidScore.InvalidFitness==invalidScore.Evaluated.Count,
            "all NaN callbacks counted invalid");

        Console.WriteLine("NQ_V12_EVOLUTION_PASS generations="+
            one.GenerationBest.Count+" evaluated="+one.Evaluated.Count+
            " first="+one.GenerationBest[0].ToString("F2")+
            " last="+one.GenerationBest.Last().ToString("F2")+
            " crosses="+one.CrossoverChildren+
            " mutations="+one.MutatedChildren+
            " duplicates="+one.Duplicates+
            " frozen="+flat.Evaluated.Count+
            " plateauResets="+plateau.Resets);
        Console.WriteLine("NQ_V12_SYNTHETIC_FITNESS_ONLY_NO_NT8_REAL_BACKTEST");
        return 0;
    }
}
