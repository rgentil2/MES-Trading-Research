// S0.75 — leak-resistant, nested-development chronological walk-forward.
// 2020–2022 ONLY: four 12-month TRAIN / following 6-month VALIDATE
// folds, rolling 6 months by default. Genuine future years 2023–26
// are HELD OUT and NEVER included in this engine. A fold's V12 genetic
// selection callback reads ONLY its training cache; exactly one winning
// genome is subsequently evaluated on its following validation segment.
// Segment-local score, NOT V9's fixed 36-month G0 acceptance test.
// No actual historical NQ data are packaged in this GitHub repository.
using System;
using System.Collections.Generic;
using System.Linq;

namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQWalkForwardConfigV15
    {
        public int TrainingMonths=12;
        public int ValidationMonths=6;
        public int StepMonths=6;
        public int MinimumFullSessionsPerMonth=15;
        public long SignalCacheBytes=67108864;
        public long AtrCacheBytes=67108864;
        public NQEvolutionConfigV12 Evolution=new NQEvolutionConfigV12{
            Population=64,Generations=12,Elites=6,Tournament=4,
            ImmigrantPercent=20,MutationPercent=18,Seed=20261105,
            MaxAttempts=200000
        };
        public void Validate()
        {
            if(TrainingMonths<6||TrainingMonths>24||
               ValidationMonths<1||ValidationMonths>12||
               StepMonths<1||StepMonths>12||
               MinimumFullSessionsPerMonth<1||
               MinimumFullSessionsPerMonth>23||
               SignalCacheBytes<1||AtrCacheBytes<1||Evolution==null)
                throw new ArgumentException("Invalid V15 temporal settings");
            Evolution.Validate();
        }
    }

    public sealed class NQFoldMetricsV15
    {
        public bool Valid,PeriodGatePass;
        public string Reason;
        public int Trades,Months,MonthsBelow5;
        public double NetUSD,ProfitFactor,ClosedDDUSD,Score;
    }

    public static class NQNativeFoldScoreV15
    {
        public const double InvalidScore=-1.0e12;
        private static NQFoldMetricsV15 Bad(string reason)
        {return new NQFoldMetricsV15{
            Valid=false,PeriodGatePass=false,Reason=reason,
            Score=InvalidScore
        };}
        public static NQFoldMetricsV15 Score(NQHistoricalResultV12 tradeRun,
                                           DateTime from,DateTime until)
        {
            if(tradeRun==null||!tradeRun.Valid||
               from>=until||from.Day!=1||until.Day!=1||
               from.Hour!=0||until.Hour!=0)
                return Bad("INVALID_RUN_OR_WINDOW");
            int months=(until.Year-from.Year)*12+until.Month-from.Month;
            if(months<1||months>36)
                return Bad("INVALID_MONTH_COUNT");
            int[] counts=new int[months];
            double realized=0,peak=0,dd=0,profit=0,loss=0;
            foreach(var t in tradeRun.Trades)
            {
                if(t==null||t.EntryTime<from||t.EntryTime>=until||
                   t.ExitTime<from||t.ExitTime>=until)
                    return Bad("TRADE_OUTSIDE_WINDOW");
                int month=(t.EntryTime.Year-from.Year)*12+
                    t.EntryTime.Month-from.Month;
                if(month<0||month>=months)
                    return Bad("MONTH_INDEX");
                counts[month]++;
                double pnl=t.NetProfitUSD;
                if(Double.IsNaN(pnl)||Double.IsInfinity(pnl))
                    return Bad("NONFINITE_TRADE");
                if(pnl>0)profit+=pnl;
                if(pnl<0)loss+=pnl;
                realized+=pnl;
                peak=Math.Max(peak,realized);
                dd=Math.Max(dd,peak-realized);
            }
            if(Math.Abs(realized-tradeRun.Net)>0.03)
                return Bad("NET_MISMATCH_WITH_TRADES");
            int missing=counts.Count(x=>x<5);
            double pf=loss<0?profit/-loss:
                profit>0?100:0;
            double logPf=Math.Log(Math.Max(0.01,Math.Min(100,pf)));
            int shortfall=Math.Max(0,5*months-tradeRun.Trades.Count);
            // Rank-only, evaluated on THIS SEGMENT; no 2023+ data.
            double score=5000*logPf + 0.10*realized -0.5*dd -
                800*missing -30*shortfall -
                0.5*Math.Max(0,dd-2000);
            if(Double.IsNaN(score)||Double.IsInfinity(score))
                return Bad("NONFINITE_SCORE");
            return new NQFoldMetricsV15{
                Valid=true,Reason="FOLD_ECONOMICS_ONLY",
                Months=months,Trades=tradeRun.Trades.Count,
                NetUSD=realized,ProfitFactor=pf,ClosedDDUSD=dd,
                MonthsBelow5=missing,Score=score,
                PeriodGatePass=missing==0 && tradeRun.Trades.Count>=
                    5*months && pf>=1.25&&realized>0&&dd<=2000
            };
        }
    }

    public sealed class NQWalkForwardFoldV15
    {
        public DateTime TrainingBegin,TrainingEnd;
        public DateTime ValidationBegin,ValidationEnd;
        public string ChosenCanonicalId;
        public NQFoldMetricsV15 Training,Validation;
        public int EvaluatedUnique;
        public int[] WinningGenes;
    }

    public sealed class NQWalkForwardResultV15
    {
        public readonly List<NQWalkForwardFoldV15> Folds=
            new List<NQWalkForwardFoldV15>();
        public bool Valid;
        public string Reason;
        public int PositiveValidationFolds,GatePassingValidationFolds;
        public double AggregatedValidationNetUSD;
        public bool ProvisionalStabilityPass;
    }

    public sealed class NQNativeWalkForwardV15
    {
        private readonly NQTimedBarV12[] source;
        private readonly int[] baseline;
        private readonly NQWalkForwardConfigV15 cfg;

        public NQNativeWalkForwardV15(IList<NQTimedBarV12> data,
                                     int[] baselineGenes,
                                     NQWalkForwardConfigV15 settings)
        {
            if(data==null||baselineGenes==null||
               baselineGenes.Length!=20||settings==null)
                throw new ArgumentException("NQ development bars and 20 genes required");
            settings.Validate();
            cfg=settings;
            baseline=(int[])baselineGenes.Clone();
            source=data.ToArray();
            ValidateInput();
        }

        private void ValidateInput()
        {
            if(source.Length==0)
                throw new ArgumentException("No NQ development M1 bars");
            var fullByMonth=new int[36];
            DateTime previous=DateTime.MinValue;
            DateTime day=DateTime.MinValue;
            var times=new List<DateTime>(120);
            Action finish=()=>
            {
                if(times.Count==0)return;
                if(times.Count!=120)
                    throw new ArgumentException("Incomplete 120-minute RTH day");
                DateTime expected=times[0].Date.AddHours(9).AddMinutes(30);
                for(int k=0;k<120;k++)
                    if(times[k]!=expected.AddMinutes(k))
                        throw new ArgumentException("Discontinuous RTH session");
                int month=(day.Year-2020)*12+day.Month-1;
                fullByMonth[month]++;
            };
            foreach(var b in source)
            {
                if(b==null||b.Time.Year<2020||b.Time.Year>2022||
                   b.Time<=previous)
                    throw new ArgumentException(
                        "Held-out 2023+ or unordered M1 observations");
                if(day!=b.Time.Date)
                {
                    finish();
                    day=b.Time.Date;times.Clear();
                }
                int hh=b.Time.Hour*100+b.Time.Minute;
                if(hh>=930&&hh<=1129)
                    times.Add(b.Time);
                previous=b.Time;
            }
            finish();
            for(int m=0;m<36;m++)
                if(fullByMonth[m]<cfg.MinimumFullSessionsPerMonth)
                    throw new ArgumentException(
                        "Month "+m+" lacks required full RTH sessions");
        }

        private List<NQTimedBarV12> Segment(DateTime start,DateTime end)
        {
            // Each source was validated BEFORE any partitioning. No
            // future segment is passed to the training fitness callback.
            var x=new List<NQTimedBarV12>();
            foreach(var b in source)
                if(b.Time>=start&&b.Time<end)
                    x.Add(b);
            if(x.Count==0)
                throw new InvalidOperationException("Empty temporal segment");
            return x;
        }

        private NQEvolutionConfigV12 ConfigForFold(int fold)
        {
            var s=cfg.Evolution;
            return new NQEvolutionConfigV12{
                Population=s.Population,Generations=s.Generations,
                Elites=s.Elites,Tournament=s.Tournament,
                ImmigrantPercent=s.ImmigrantPercent,
                MutationPercent=s.MutationPercent,
                Seed=checked(s.Seed+fold),
                MaxAttempts=s.MaxAttempts,
                ResetAfterStagnantGenerations=
                    s.ResetAfterStagnantGenerations
            };
        }

        public NQWalkForwardResultV15 Run()
        {
            var result=new NQWalkForwardResultV15{
                Valid=true,Reason="NESTED_DEVELOPMENT_WALK_FORWARD_ONLY"
            };
            DateTime start=new DateTime(2020,1,1);
            DateTime developmentEnd=new DateTime(2023,1,1);
            for(int fold=0;;fold++)
            {
                DateTime trainFrom=start.AddMonths(fold*cfg.StepMonths);
                DateTime trainTo=trainFrom.AddMonths(cfg.TrainingMonths);
                DateTime testTo=trainTo.AddMonths(cfg.ValidationMonths);
                if(testTo>developmentEnd)break;
                if(trainTo<=trainFrom ||
                   testTo<=trainTo)
                    throw new InvalidOperationException("Overlapping temporal split");
                // Train-only snapshot: no validation bars in search.
                var trainCache=new NQNativeSignalCacheV14(
                    Segment(trainFrom,trainTo),cfg.SignalCacheBytes,
                    cfg.AtrCacheBytes);
                var engine=new NQEvolutionEngineV12(
                    NQEvolutionEngineV12.DefaultDomains(baseline,true),
                    ConfigForFold(fold));
                var fit=engine.Run(genome=>
                {
                    var t=trainCache.Evaluate(genome.Genes);
                    return NQNativeFoldScoreV15.Score(t,trainFrom,trainTo).Score;
                });
                var item=new NQWalkForwardFoldV15{
                    TrainingBegin=trainFrom,TrainingEnd=trainTo,
                    ValidationBegin=trainTo,ValidationEnd=testTo,
                    EvaluatedUnique=fit.Evaluated.Count
                };
                if(fit.Best==null)
                {
                    result.Valid=false;
                    result.Reason="NO_TRAINING_CANDIDATES";
                    result.Folds.Add(item);
                    break;
                }
                item.ChosenCanonicalId=fit.Best.Genome.Canonical.RuntimeKey;
                item.WinningGenes=(int[])fit.Best.Genome.Genes.Clone();
                item.Training=NQNativeFoldScoreV15.Score(
                    trainCache.Evaluate(item.WinningGenes),
                    trainFrom,trainTo);
                // Chosen winner is IMMUTABLE before validation is opened.
                var testCache=new NQNativeSignalCacheV14(
                    Segment(trainTo,testTo),cfg.SignalCacheBytes,
                    cfg.AtrCacheBytes);
                item.Validation=NQNativeFoldScoreV15.Score(
                    testCache.Evaluate(item.WinningGenes),trainTo,testTo);
                if(!item.Training.Valid||!item.Validation.Valid)
                {
                    result.Valid=false;
                    result.Reason="INVALID_SEGMENT_SCORE";
                    result.Folds.Add(item);
                    break;
                }
                result.Folds.Add(item);
                result.AggregatedValidationNetUSD+=item.Validation.NetUSD;
                if(item.Validation.NetUSD>0)
                    result.PositiveValidationFolds++;
                if(item.Validation.PeriodGatePass)
                    result.GatePassingValidationFolds++;
            }
            // A prospective stability screen, not evidence of edge.
            // Repeated validation folds use distinct, nonoverlapping
            // calendar windows. No 2023+ market data have been consumed.
            result.ProvisionalStabilityPass=result.Valid &&
                result.Folds.Count>=4 &&
                result.PositiveValidationFolds>=3 &&
                result.GatePassingValidationFolds>=3;
            return result;
        }
    }
}
