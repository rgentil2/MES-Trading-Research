// V19 large-scale capacity: evaluate 109,464 V19 canonical genomes
// with 1320 searchable directional conditions, fitness feedback and
// genetic mutations. Objective is deterministic SYNTHETIC test, never
// real NQ bars. This must pass before claiming the 1320 catalog can
// be searched at the same scale as original V17 132-condition engine.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;
internal static class V19LargeScale
{
    static void A(bool x,string why)
    {if(!x)throw new Exception("NQ_V19_100K_FAIL "+why);}
    static NQEvolutionConfigV12 Cfg()
    {
        return new NQEvolutionConfigV12{
            Population=600,Generations=190,Elites=24,Tournament=5,
            ImmigrantPercent=23,MutationPercent=19,
            Seed=20261106,MaxAttempts=300000,
            ResetAfterStagnantGenerations=7
        };
    }
    static readonly int[] Baseline={
        2,396,12,789,12,999,12,1319,12,
        0,0,0,0,20,32,2,0,14,15,25
    };
    static double Objective(NQGenomeV11 candidate)
    {
        int[] g=candidate.Genes;
        double score=10000-
            6*Math.Abs(g[1]-160)-
            6*Math.Abs(g[3]-275)-
            3*Math.Abs(g[5]-355)-
            2*Math.Abs(g[7]-389)-
            24*Math.Abs(g[0]-3)-
            13*Math.Abs(g[2]-12)-
            12*Math.Abs(g[4]-18)-
            5*Math.Abs(g[13]-24)-
            6*Math.Abs(g[16]-2);
        if(g[0]>2 && g[1]/11!=g[3]/11)
            score+=50;
        return score;
    }
    public static int Main()
    {
        var ranges=NQNativeExitCanonicalV19.DefaultDomains(
            Baseline,true);
        foreach(int slot in new[]{1,3,5,7})
            A(ranges[slot].Min==0&&ranges[slot].Max==395,
              "all 1320 conditions searchable per active leaf");
        var timer=Stopwatch.StartNew();
        var run=new NQEvolutionEngineV12(
            ranges,Cfg(),NQNativeExitCanonicalV19.Analyze)
            .Run(Objective);
        timer.Stop();
        const int Expected=109464;
        A(run.Evaluated.Count==Expected&&
          run.GenerationBest.Count==190,"complete 109464 unique scores");
        A(run.Evaluated.Select(x=>x.Genome.Canonical.RuntimeKey)
            .Distinct(StringComparer.Ordinal).Count()==Expected,
          "zero repeated canonical V19 identities");
        A(run.Evaluated.All(x=>
            x.Genome.Canonical.RuntimeKey.StartsWith("EXCANv18:")&&
            !x.Genome.Canonical.IsRedundant&&
            !Double.IsNaN(x.Score)&&!Double.IsInfinity(x.Score)),
          "valid versioned, nonredundant numeric scores");
        var types=new HashSet<int>();
        foreach(var x in run.Evaluated)
            for(int i=0;i<x.Genome.Genes[0];i++)
                types.Add(x.Genome.Genes[1+2*i]);
        A(types.Count==1320,"all 1320 conditions sampled at least once");
        A(run.CrossoverChildren>20000&&
          run.MutatedChildren>20000&&
          run.ImmigrantChildren>10000,
          "evolution has genuine mutation, mating and immigration");
        A(run.GenerationBest.Last()>=run.GenerationBest[0],
          "score-guided global elitism nonregressing");
        A(run.Best!=null&&run.Best.Score==
          run.GenerationBest.Last(),"final best score retained");
        A(run.Attempts>=run.Evaluated.Count &&
          run.Duplicates>0&&run.Redundant>0,
          "duplicate and structural redundancy measured");
        Console.WriteLine("NQ_V19_1320_CONDITIONS_100K_PASS "+
            "uniqueFitnessScores="+run.Evaluated.Count+
            " allConditions="+types.Count+
            " families="+NQNativeConditionCatalogV19.Families+
            " duplicateSkipped="+run.Duplicates+
            " redundantSkipped="+run.Redundant+
            " attempted="+run.Attempts+
            " mutationChildren="+run.MutatedChildren+
            " crossoverChildren="+run.CrossoverChildren+
            " immigrantChildren="+run.ImmigrantChildren+
            " elapsedMs="+timer.ElapsedMilliseconds);
        Console.WriteLine("V19_SYNTHETIC_100K_GENETIC_FITNESS_ONLY_NOT_REAL_NQ_BACKTEST");
        return 0;
    }
}
