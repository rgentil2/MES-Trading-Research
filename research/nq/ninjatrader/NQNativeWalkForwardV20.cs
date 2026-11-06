// S0.81 V20 V19-catalog-specific TRAIN-ONLY 2020–2022 walk-forward.
// Reuses the exact V15 split windows, fold G0 score & seal rules but
// operates on EXCANv19 / 1,320 selectable conditions rather than V11.
// Existing V15 class and CI are untouched. Never reads 2023+ OOS.
using System;
using System.Collections.Generic;
using System.Linq;
namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQNativeWalkForwardV20
    {
        private readonly NQTimedBarV12[] source;
        private readonly int[] baseline;
        private readonly NQWalkForwardConfigV15 cfg;

        public NQNativeWalkForwardV20(IList<NQTimedBarV12> data,
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
                    cfg.AtrCacheBytes,NQNativeConditionCatalogV19.Count,
                    NQNativeExpandedResearchV19.Direction);
                var engine=new NQEvolutionEngineV12(
                    NQNativeExitCanonicalV19.DefaultDomains(baseline,true),
                    ConfigForFold(fold),
                    NQNativeExitCanonicalV19.Analyze);
                var fit=engine.Run(genome=>
                {
                    var t=trainCache.EvaluateExpanded(genome.Genes,
                        NQNativeExitCanonicalV19.Analyze);
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
                    trainCache.EvaluateExpanded(item.WinningGenes,
                        NQNativeExitCanonicalV19.Analyze),
                    trainFrom,trainTo);
                // Chosen winner is IMMUTABLE before validation is opened.
                var testCache=new NQNativeSignalCacheV14(
                    Segment(trainTo,testTo),cfg.SignalCacheBytes,
                    cfg.AtrCacheBytes,NQNativeConditionCatalogV19.Count,
                    NQNativeExpandedResearchV19.Direction);
                item.Validation=NQNativeFoldScoreV15.Score(
                    testCache.EvaluateExpanded(item.WinningGenes,
                    NQNativeExitCanonicalV19.Analyze),trainTo,testTo);
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
