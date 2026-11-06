// V20 genuine 1320-rule source->GA->V13 robust audit->V15
// portfolio gate FAIL-CLOSED, plus independent V20 train-only 4-fold
// WF reproducibility. Source synthetic 2020-22 only; 2023+ rejected.
// No real NQ profits, no NinjaTrader native order or strategy runs.
using System;
using System.Collections.Generic;
using System.Linq;
using System.IO;
using NinjaTrader.NinjaScript.Strategies;
internal static class V22FullDevelopmentTest
{
    private static void A(bool good,string why)
    {if(!good)throw new Exception("NQ_V22_FULL_FUNNEL_FAIL "+why);}
    private static readonly string folder=Path.Combine(
        Path.GetTempPath(),"NQ_V21_FULL_"+Guid.NewGuid().ToString("N"));
    private static NQResearchRunV22 Run(
        NQDataLoadV16 source,int[] genes,NQResearchConfigV16 cfg)
    {
        Directory.CreateDirectory(folder);
        return NQNativeResearchRunnerV22.Run(source,genes,cfg,
            Path.Combine(folder,"economics.tsv"),
            Path.Combine(folder,"ranking.tsv"),
            Path.Combine(folder,"fills.tsv"),5,16*1024*1024);
    }
    private static readonly int[] Base={
        2,396,12,789,12,999,12,1319,12,
        0,0,0,0,20,32,2,0,14,15,25
    };
    private static readonly int[] Days={1,5,9,13,17,21,25,28};
    private static NQDataLoadV16 Development(bool missing=false,
        bool perturbLate=false)
    {
        var rows=new List<NQTimedBarV12>(64000);
        var monthCounts=new int[36];
        double last=15000;
        var rng=new Random(20261106);
        for(int y=2020;y<=2022;y++)
          for(int m=1;m<=12;m++)
            for(int di=0;di<Days.Length;di++)
            {
                int day=Days[di];
                if(missing&&y==2021&&m==4&&day==28)continue;
                DateTime date=new DateTime(y,m,day);
                for(int minute=0;minute<210;minute++)
                {
                    double op=last;
                    double phase=(minute+4*m+di*7)*0.14;
                    double drift=(y==2020?0.5:y==2021?-0.4:0.6)+
                        Math.Sin(phase)*1.4+(rng.NextDouble()-0.5)*1.5;
                    if(perturbLate&&y==2022&&m>=7)
                        drift=-2+Math.Sin(phase)*1.2;
                    last=Math.Max(1500,last+drift);
                    rows.Add(new NQTimedBarV12(
                        date.AddHours(8).AddMinutes(minute),
                        new NQBarV11(op,Math.Max(op,last)+0.6,
                            Math.Min(op,last)-0.6,last,200+minute%73)));
                }
                monthCounts[(y-2020)*12+m-1]++;
            }
        var manifest=new NQDataManifestV16(
            NQDataPartitionV16.Development2020_2022,
            "NQ DEC2026","NT8_SERIES_VISIBLE_2020_22_USER_CONFIRMED",
            new string('a',64),new DateTime(2020,1,1),
            new DateTime(2022,12,31),new DateTime(2020,1,1),
            new DateTime(2022,12,31),rows.Count,rows.Count,
            monthCounts.Sum(),monthCounts);
        return new NQDataLoadV16(manifest,rows.AsReadOnly());
    }
    private static NQEvolutionConfigV12 Genetic(int seed=20261106)
    {
        return new NQEvolutionConfigV12{
            Population=12,Generations=2,Elites=2,
            Tournament=3,Seed=seed,MaxAttempts=10000,
            ImmigrantPercent=20,MutationPercent=18
        };
    }
    private static NQWalkForwardConfigV15 WF()
    {
        return new NQWalkForwardConfigV15{
            MinimumFullSessionsPerMonth=8,
            SignalCacheBytes=32L*1024*1024,
            AtrCacheBytes=32L*1024*1024,
            Evolution=Genetic()
        };
    }
    private static NQResearchConfigV16 Config()
    {
        return new NQResearchConfigV16{
            Genetic=Genetic(),CandidateAuditLimit=10,
            SignalCacheBytes=32L*1024*1024,
            MinimumFullDaysPerMonth=8,
            WalkForward=WF(),
            FinalCutoffExclusive=new DateTime(2026,11,1),
            Robustness=new NQRobustnessConfigV13{
                BootstrapPaths=100,BlockLengthTrades=8,
                Seed=20261106,BaseAllInCostPerTradeUSD=24.68,
                CostMultiplier=1.5,MaxBootstrapP95ClosedDDUSD=2000
            }
        };
    }
    public static int Main()
    {
        var data=Development();
        A(data.Manifest.FullSessionsByMonth.All(x=>x==8),
          "all 36 DEV months have 8 complete observed sessions");
        var result=Run(data,Base,Config());
        A(result.Completed&&result.Genetic!=null&&
          result.GeneticEvaluated==22&&result.RobustnessChecked==10,
          "22 V19 genetic scores and 10 actual V13 robustness audits");
        A(result.Genetic.Evaluated.All(x=>
            x.Genome.Canonical.RuntimeKey.StartsWith("EXCANv19:") &&
            x.Genome.Genes[1]>=0&&x.Genome.Genes[1]<1320),
          "no V19 genotype silently interpreted as V11");
        A(result.RobustCandidateKeys.Count==result.RobustnessPassed,
          "robust candidates fully reconciled");
        A(result.Bulk!=null&&result.Bulk.NewEconomicBacktests==22&&
          result.Bulk.ReusedEconomicBacktests==0&&
          result.Bulk.FinalistBacktests==5,
          "all 22 GA economic evaluations durably recorded and 5 finalist fill audits");
        A(result.Audit==null,
          "no positive portfolio can reach V22 freeze audit after prior V15 reject");
        A(!result.HasFrozenCandidates&&result.FrozenCampaign==null &&
          result.Reason!="FROZEN_DEVELOPMENT_ONLY_READY_FOR_EXTERNAL",
          "no fake profitable portfolio from synthetic series");

        var replay=Run(data,Base,Config());
        A(replay.Bulk!=null&&
          replay.Bulk.NewEconomicBacktests==0&&
          replay.Bulk.ReusedEconomicBacktests==22,
          "full funnel restart never recalculates preexisting 22 economic backtests");
        A(replay.GeneticEvaluated==result.GeneticEvaluated &&
            replay.Genetic.Evaluated.Zip(result.Genetic.Evaluated,
                (a,b)=>a.Score==b.Score&&
                a.Genome.Canonical.RuntimeKey==
                b.Genome.Canonical.RuntimeKey).All(x=>x),
          "bitwise same GA V19 backtest sequence and canonical keys");

        var incomplete=Run(
            Development(true),Base,Config());
        A(!incomplete.Completed&&
          incomplete.Reason=="DEVELOPMENT_SOURCE_INCOMPLETE" &&
          incomplete.Genetic==null,
          "one incomplete development month rejects before GA");
        var invalid=new NQDataLoadV16(new NQDataManifestV16(
            NQDataPartitionV16.ExternalValidation2023_2024,
            "NQ DEC2026","NT8_SERIES_VISIBLE_2020_22_USER_CONFIRMED",
            new string('b',64),new DateTime(2023,1,1),
            new DateTime(2024,12,31),new DateTime(2023,1,1),
            new DateTime(2024,12,31),1,1,0,new int[24]),
            new List<NQTimedBarV12>());
        var leak=Run(invalid,Base,Config());
        A(!leak.Completed&&leak.Reason=="INVALID_DEVELOPMENT_INPUT"&&
          leak.Genetic==null,
          "2023+ data are NEVER accepted in training runner");

        // Dedicated train-only test: the run can reject false strategies,
        // but the four chronological folds and EXCANv19 identity must be
        // runnable on the same 2020–22 source WITHOUT peeking at 2023+.
        var wf=new NQNativeWalkForwardV20(data.Bars,Base,WF()).Run();
        A(wf.Valid&&wf.Folds.Count==4,
          "all four train-12month/validate-next-6month folds executed");
        int evaluated=0;
        for(int i=0;i<wf.Folds.Count;i++)
        {
            var fold=wf.Folds[i];
            A(fold.TrainingBegin==new DateTime(2020,1,1).AddMonths(6*i)
              &&fold.TrainingEnd==fold.ValidationBegin &&
              fold.ValidationEnd==fold.ValidationBegin.AddMonths(6) &&
              fold.ValidationEnd<=new DateTime(2023,1,1),
              "no forward leakage fold "+i);
            A(fold.ChosenCanonicalId.StartsWith("EXCANv19:") &&
              fold.Training.Valid&&fold.Validation.Valid,
              "versioned V19 winner scored without OOS fold "+i);
            evaluated+=fold.EvaluatedUnique;
        }
        A(evaluated==88,
          "four training-only V19 GAs each evaluate 22 unique genomes");
        var shifted=new NQNativeWalkForwardV20(
            Development(false,true).Bars,Base,WF()).Run();
        A(shifted.Valid&&shifted.Folds.Count==4,
          "independent mutated late-2022 walkforward completes");
        for(int i=0;i<4;i++)
        {
            A(shifted.Folds[i].ChosenCanonicalId==
                wf.Folds[i].ChosenCanonicalId &&
              shifted.Folds[i].Training.Score==
                wf.Folds[i].Training.Score,
              "future validation changes cannot rewrite training fold "+i);
            if(i<3)
                A(shifted.Folds[i].Validation.Score==
                  wf.Folds[i].Validation.Score,
                  "late 2022 cannot rewrite earlier valid fold "+i);
        }

        Console.WriteLine("NQ_V22_FULL_FUNNEL_PASS geneticUnique="+
            result.GeneticEvaluated+" robustAudited="+
            result.RobustnessChecked+" robustPass="+
            result.RobustnessPassed+" result="+result.Reason+
            " folds="+wf.Folds.Count+" foldedGenomes="+evaluated+
            " version=EXCANv19 noFutureLeakage=TRUE");
        Console.WriteLine("V20_SYNTHETIC_DEVELOPMENT_ONLY_NO_PROFITABILITY_CLAIM");
        return 0;
    }
}
