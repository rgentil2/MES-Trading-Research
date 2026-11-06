// Integration proof: 132-condition genome -> C# genetic evolution ->
// synthetic M1 trade simulations -> original V9/V7 discovery score.
// No genuine NQ market dataset is used in this CI scenario.
using System;
using System.Collections.Generic;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;
internal static class V12EndToEndTest
{
    private static void Check(bool b,string why)
    {if(!b)throw new Exception("V12_PIPELINE_FAIL "+why);}
    private static List<NQTimedBarV12> SyntheticDay(int year=2021)
    {
        var list=new List<NQTimedBarV12>();
        double p=15000;
        DateTime start=new DateTime(year,6,1,9,30,0);
        for(int i=0;i<130;i++)
        {
            double o=p;
            p+=0.5+Math.Sin(i*0.15)*0.8;
            list.Add(new NQTimedBarV12(start.AddMinutes(i),
                new NQBarV11(o,Math.Max(o,p)+0.3,
                           Math.Min(o,p)-0.3,p,250+i)));
        }
        return list;
    }
    public static int Main()
    {
        int[] baseGenes={2,0,12,44,12,77,12,121,12,0,0,0,0,
            20,32,2,0,14,15,25};
        var cfg=new NQEvolutionConfigV12{
            Population=24,Generations=3,Elites=3,Tournament=3,
            ImmigrantPercent=25,MutationPercent=20,Seed=20261106,
            MaxAttempts=10000
        };
        var fixture=SyntheticDay();
        var pipeline=new NQNativeResearchPipelineV12(fixture,
            baseGenes,cfg,true,false);
        var result=pipeline.Run();
        Check(result.GenerationBest.Count==3,
            "all generations complete");
        Check(result.Evaluated.Count==66,
            "gen0 24 + 2 x 21 unique evaluations");
        Check(result.Evaluated.Select(x=>x.Genome.Canonical.RuntimeKey)
            .Distinct(StringComparer.Ordinal).Count()==result.Evaluated.Count,
            "pipeline uses versioned canonical identity");
        Check(result.Evaluated.Any(x=>x.Score!=-1e12),
            "at least one synthetic-M1 economic evaluation valid");
        foreach(var ranked in result.Evaluated)
        {
            var direct=NQNativeHistoricalEvaluatorV12.Evaluate(
                fixture,ranked.Genome.Genes);
            Check(Math.Abs(direct.Score-ranked.Score)<1e-9,
                "GA must read actual simulated M1 V9 score, not fake score");
        }
        // Data-leak and incomplete-period gates. In production require
        // all 36 months of the frozen 2020-22 development sample.
        try
        {
            new NQNativeResearchPipelineV12(fixture,baseGenes,cfg,
                true,true).Run();
            throw new Exception("MISSING_FULL_PERIOD_GUARD");
        }
        catch(InvalidOperationException ex)
        {
            Check(ex.Message.Contains("Incomplete 36-month"),
                "full development window enforced");
        }
        var leak=SyntheticDay();
        leak.AddRange(SyntheticDay(2023));
        try
        {
            new NQNativeResearchPipelineV12(leak,baseGenes,cfg,
                true,false).Run();
            throw new Exception("MISSING_OOS_GUARD");
        }
        catch(InvalidOperationException ex)
        {
            Check(ex.Message.Contains("held-out"),
                "held-out 2023+ rejected before GA");
        }
        Console.WriteLine("NQ_V12_PIPELINE_PASS evaluations="+
            result.Evaluated.Count+" generations="+
            result.GenerationBest.Count+" best="+
            result.Best.Score.ToString("F2")+
            " SCORER=REAL_V9_ON_SYNTHETIC_M1_BARS");
        Console.WriteLine("NOT_REAL_NQ_HISTORY_NOT_NINJATRADER_FILL_PARITY");
        return 0;
    }
}
