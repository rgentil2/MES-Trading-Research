// V17 capacity proof on EXACT C# native research genome + canonical
// and TRUE fitness-guided V12 evolutionary core. This is a synthetic
// score oracle, NOT a 2020-22 NQ profitability / fill / risk backtest.
// 190 generations x 600 population, 24 survivor elites:
// 600 + (189 * 576) = 109,464 REQUIRED UNIQUE scores.
// Includes deterministic shorter-prefix replay and diversity statistics.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using NinjaTrader.NinjaScript.Strategies;

internal static class V17LargeScale
{
    static void Check(bool yes,string reason)
    {if(!yes)throw new Exception("NQ_V17_CAPACITY_FAIL "+reason);}
    static NQEvolutionConfigV12 Cfg(int generations)
    {
        return new NQEvolutionConfigV12 {
            Population=600,Generations=generations,Elites=24,
            Tournament=5,ImmigrantPercent=23,MutationPercent=19,
            Seed=20261106,MaxAttempts=1000000,
            ResetAfterStagnantGenerations=7
        };
    }
    static readonly int[] Baseline={
        2,0,12,44,12,77,12,121,12,
        0,0,0,0,20,32,2,0,14,15,25
    };
    static double Oracle(NQGenomeV11 g)
    {
        var x=g.Genes;
        // Intentionally nontrivial nonseparable interaction means genuine
        // directional selection can favor some combinations over others.
        double score=5000-38*Math.Abs(x[0]-3)
            -4*Math.Abs(x[1]-38)-4*Math.Abs(x[3]-57)
            -5*Math.Abs(x[5]-98)-4*Math.Abs(x[7]-123)
            -18*Math.Abs(x[2]-12)-14*Math.Abs(x[4]-15)
            -8*Math.Abs(x[13]-20)-3*Math.Abs(x[14]-40)
            -50*Math.Abs(x[16]-2)
            -15*Math.Abs(x[15]-2)
            -20*Math.Abs(x[9]-1);
        if(x[1]/11==x[3]/11)score-=100;
        if(x[0]>=3&&x[5]/11!=x[7]/11)score+=65;
        return score;
    }
    static string HashFirstLast(NQEvolutionSummaryV12 s)
    {
        var bytes=new StringBuilder();
        foreach(var x in s.Evaluated.Take(3).Concat(
            s.Evaluated.Skip(Math.Max(0,s.Evaluated.Count-3))))
            bytes.Append(x.Genome.Canonical.RuntimeKey).Append(':')
                 .Append(x.Score.ToString("R",
                     CultureInfo.InvariantCulture)).Append('\n');
        using(var sha=SHA256.Create())
            return BitConverter.ToString(sha.ComputeHash(
                Encoding.UTF8.GetBytes(bytes.ToString())))
                .Replace("-","").ToLowerInvariant();
    }
    public static int Main()
    {
        var domain=NQEvolutionEngineV12.DefaultDomains(Baseline,true);
        var timer=Stopwatch.StartNew();
        var big=new NQEvolutionEngineV12(domain,Cfg(190)).Run(Oracle);
        timer.Stop();
        long ms=timer.ElapsedMilliseconds;
        int planned=600+(190-1)*(600-24);
        Check(planned==109464,"planned target count");
        Check(big.Evaluated.Count==planned,
            "at least 100k canonical unique SCORED candidates");
        Check(big.GenerationBest.Count==190&&
              big.GenerationNew[0]==600&&
              big.GenerationNew.Skip(1).All(x=>x==576),
              "exact 190-generation offspring and elite retention");
        Check(big.Evaluated.Count==big.Evaluated.Select(x=>
            x.Genome.Canonical.RuntimeKey).Distinct(
            StringComparer.Ordinal).Count(),
            "global canonical runtime fingerprints 100% unique");
        Check(big.Evaluated.All(x=>
            !x.Genome.Canonical.IsRedundant&&
            !Double.IsNaN(x.Score)&&!Double.IsInfinity(x.Score)),
            "no structural redundancy and no nonfinite score");
        Check(big.CrossoverChildren>20000&&
            big.MutatedChildren>20000&&
            big.ImmigrantChildren>10000,
            "actual fitness-guided diversity sources used");
        Check(big.GenerationBest.Last()>=big.GenerationBest[0],
            "elitism never loses best-of-run");
        var distinctFamilies=new HashSet<int>();
        for(int i=0;i<big.Evaluated.Count;i++)
        {
            var x=big.Evaluated[i].Genome.Genes;
            for(int s=0;s<x[0];s++)
                distinctFamilies.Add(x[1+2*s]);
        }
        Check(distinctFamilies.Count==132,
            "all 132 directional condition IDs explored");
        Check(big.Attempts>=big.Evaluated.Count,
            "duplicates/invalid structural attempts accounted");
        Check(big.Best!=null&&big.Best.Score==
              big.GenerationBest.Last(),
            "winning fitness output equals final retained best");

        // The first generation and all subsequent children are a pure
        // function of seed + feedback, not runtime or future generations.
        var shortRun=new NQEvolutionEngineV12(domain,Cfg(4)).Run(Oracle);
        Check(shortRun.Evaluated.Count==600+3*576,
            "short reproducible prefix count");
        for(int i=0;i<shortRun.Evaluated.Count;i++)
            Check(shortRun.Evaluated[i].Genome.Canonical.RuntimeKey==
                big.Evaluated[i].Genome.Canonical.RuntimeKey &&
                shortRun.Evaluated[i].Score==big.Evaluated[i].Score,
                "exact seed/selection replay at index "+i);

        string hash=HashFirstLast(big);
        Console.WriteLine("NQ_V17_100K_CAPACITY_PASS "+
            "scoredUnique="+big.Evaluated.Count+
            " generations="+big.GenerationBest.Count+
            " seed="+Cfg(190).Seed+
            " allConditions="+distinctFamilies.Count+
            " attempts="+big.Attempts+
            " duplicate="+big.Duplicates+
            " redundant="+big.Redundant+
            " mutants="+big.MutatedChildren+
            " crossovers="+big.CrossoverChildren+
            " immigrants="+big.ImmigrantChildren+
            " elapsedMs="+ms+
            " firstBest="+big.GenerationBest[0].ToString("F2")+
            " finalBest="+big.GenerationBest.Last().ToString("F2")+
            " evidenceSHA256="+hash);
        Console.WriteLine("V17_SYNTHETIC_SCORE_ONLY_NO_REAL_NQ_MARKET_BACKTEST");
        return 0;
    }
}
