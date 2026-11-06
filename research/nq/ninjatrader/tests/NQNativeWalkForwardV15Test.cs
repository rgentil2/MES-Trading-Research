// S0.75: synthetic 2020–22 rolling genetic walk-forward tests.
// Proves selection uses ONLY each preceding training period; final
// held-out 2023–26 is never accessed. No real NQ market data.
using System;
using System.Collections.Generic;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;

internal static class V15WalkForwardTest
{
    private static void A(bool yes,string why)
    {if(!yes)throw new Exception("NQ_V15_WF_FAIL "+why);}
    private static List<NQTimedBarV12> SyntheticDevelopment(bool alterLate2022)
    {
        var result=new List<NQTimedBarV12>(60000);
        double price=15000;
        for(int year=2020;year<=2022;year++)
        for(int month=1;month<=12;month++)
        for(int day=1;day<=DateTime.DaysInMonth(year,month);day++)
        {
            var date=new DateTime(year,month,day);
            if(date.DayOfWeek!=DayOfWeek.Monday &&
               date.DayOfWeek!=DayOfWeek.Wednesday &&
               date.DayOfWeek!=DayOfWeek.Friday)continue;
            double slope=year==2020?0.7:
                year==2021?-0.7:0.5;
            if(alterLate2022 && year==2022&&month>=7)
                slope=-3.0;
            for(int i=0;i<120;i++)
            {
                double old=price;
                double drift=slope+0.7*Math.Sin(i*0.15)+
                    0.6*Math.Cos((month*17+i)*0.08);
                price+=drift;
                double high=Math.Max(old,price)+0.8;
                double low=Math.Min(old,price)-0.8;
                result.Add(new NQTimedBarV12(
                    date.AddHours(9).AddMinutes(30+i),
                    new NQBarV11(old,high,low,price,300+(i%40)*10)));
            }
        }
        return result;
    }
    private static NQWalkForwardConfigV15 Config()
    {
        return new NQWalkForwardConfigV15{
            TrainingMonths=12,ValidationMonths=6,StepMonths=6,
            MinimumFullSessionsPerMonth=10,
            SignalCacheBytes=16L*1024*1024,
            AtrCacheBytes=16L*1024*1024,
            Evolution=new NQEvolutionConfigV12{
                Population=12,Generations=2,Elites=2,Tournament=3,
                ImmigrantPercent=25,MutationPercent=18,Seed=20261106,
                MaxAttempts=10000
            }
        };
    }
    public static int Main()
    {
        int[] baseGenes={2,0,12,44,12,77,12,121,12,
            0,0,0,0,20,32,2,0,14,15,25};
        var data=SyntheticDevelopment(false);
        var plan=new NQNativeWalkForwardV15(data,baseGenes,Config());
        var original=plan.Run();
        A(original.Valid&&original.Folds.Count==4,
            "four rolling 12m train / 6m next validation folds");
        int total=0;
        for(int i=0;i<original.Folds.Count;i++)
        {
            var f=original.Folds[i];
            DateTime expectedTrain=new DateTime(2020,1,1).AddMonths(6*i);
            A(f.TrainingBegin==expectedTrain &&
              f.TrainingEnd==expectedTrain.AddMonths(12) &&
              f.ValidationBegin==f.TrainingEnd &&
              f.ValidationEnd==f.TrainingEnd.AddMonths(6),
              "no training/validation overlap fold "+i);
            A(f.ValidationEnd<=new DateTime(2023,1,1),
              "no held-out 2023+ bar used");
            A(f.EvaluatedUnique==22,"12 generation-zero + 10 selected children");
            A(f.Training!=null&&f.Validation!=null&&
              f.Training.Valid&&f.Validation.Valid,
              "period-local segment metrics available");
            A(!String.IsNullOrEmpty(f.ChosenCanonicalId)&&
              f.WinningGenes.Length==20,"one frozen winner per fold");
            total+=f.EvaluatedUnique;
        }
        A(total==88,"88 train-only candidate evaluations");

        // Same input and seed -> same four selected identities & scores.
        var replay=new NQNativeWalkForwardV15(
            SyntheticDevelopment(false),baseGenes,Config()).Run();
        A(replay.Folds.Count==4,"replayed four folds");
        for(int i=0;i<4;i++)
            A(original.Folds[i].ChosenCanonicalId==
                replay.Folds[i].ChosenCanonicalId &&
              original.Folds[i].Training.Score==
                replay.Folds[i].Training.Score &&
              original.Folds[i].Validation.Score==
                replay.Folds[i].Validation.Score,
                "exact deterministic walk-forward replay fold "+i);

        // Change ONLY the final JUL-DEC 2022 validation segment.
        // It must never alter ANY earlier training-selected genome or
        // training fitness, especially the 2022 H2 fold winner.
        var changed=new NQNativeWalkForwardV15(
            SyntheticDevelopment(true),baseGenes,Config()).Run();
        A(changed.Folds.Count==4,"perturbed run complete");
        for(int i=0;i<4;i++)
            A(original.Folds[i].ChosenCanonicalId==
                changed.Folds[i].ChosenCanonicalId &&
              original.Folds[i].Training.Score==
                changed.Folds[i].Training.Score,
                "validation future cannot influence train fold "+i);
        // Every earlier validation segment is ALSO untouched.
        for(int i=0;i<3;i++)
            A(original.Folds[i].Validation.Score==
                changed.Folds[i].Validation.Score,
                "late 2022 mutation cannot rewrite earlier validation "+i);

        var heldout=SyntheticDevelopment(false);
        heldout.Add(new NQTimedBarV12(
            new DateTime(2023,1,2,9,30,0),
            new NQBarV11(15000,15001,14999,15000,100)));
        try
        {
            new NQNativeWalkForwardV15(heldout,baseGenes,Config());
            throw new Exception("missing future lock");
        }
        catch(ArgumentException ex)
        {
            A(ex.Message.Contains("Held-out"),
                "2023+ excluded before all training");
        }
        var missing=SyntheticDevelopment(false);
        missing.RemoveAll(x=>x.Time.Year==2020&&x.Time.Month==2);
        try
        {
            new NQNativeWalkForwardV15(missing,baseGenes,Config());
            throw new Exception("missing monthly coverage");
        }
        catch(ArgumentException ex)
        {
            A(ex.Message.Contains("lacks required"),
                "no partial dataset passes month coverage");
        }
        var broken=SyntheticDevelopment(false);
        int remove=broken.FindIndex(x=>x.Time.Hour==11&&
            x.Time.Minute==29);
        A(remove>=0,"test includes 11:29 exit bar");
        broken.RemoveAt(remove);
        try
        {
            new NQNativeWalkForwardV15(broken,baseGenes,Config());
            throw new Exception("missing RTH contiguity failure");
        }
        catch(ArgumentException ex)
        {
            A(ex.Message.Contains("Incomplete 120-minute"),
                "drop last research M1 bar must fail closed");
        }

        Console.WriteLine("NQ_V15_WALK_FORWARD_PASS folds="+
            original.Folds.Count+" trainOnlyEvaluations="+total+
            " positiveValidation="+original.PositiveValidationFolds+
            " validationGatePass="+original.GatePassingValidationFolds+
            " late2022TrainingLeak=FALSE");
        Console.WriteLine("NQ_V15_WF_ONLY_SYNTHETIC_2020_22_NO_2023_26_OOS_BACKTEST");
        return 0;
    }
}
