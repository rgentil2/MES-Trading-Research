// S0.76 — headless research orchestration, *not* a live NT8 AddOn.
// Development NT8 UTC.Last.txt -> V14 GA/V9 fitness -> V13 robust
// 3–5 strategy selection -> V15 combined chronological floating risk ->
// V15 train-only walk-forward -> V16 immutable OOS freeze.
// If any gate fails, returns reason and NO frozen campaign. This is
// deliberately conservative. No 2023+ data passed to THIS runner.
// Native Strategy Analyzer custom-Optimizer feedback remains unavailable
// through the documented void RunIteration() API; do not pretend
// an external GA callback is native NT8 optimization feedback.
using System;
using System.Collections.Generic;
using System.Linq;

namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQResearchConfigV16
    {
        public NQEvolutionConfigV12 Genetic=new NQEvolutionConfigV12();
        public NQWalkForwardConfigV15 WalkForward=new NQWalkForwardConfigV15();
        public NQRobustnessConfigV13 Robustness=new NQRobustnessConfigV13();
        public NQPortfolioConfigV13 Portfolio=new NQPortfolioConfigV13();
        public NQChronologicalRiskConfigV15 AccountRisk=
            new NQChronologicalRiskConfigV15();
        public int CandidateAuditLimit=300;
        public long SignalCacheBytes=128L*1024*1024;
        public int MinimumFullDaysPerMonth=15;
        public DateTime FinalCutoffExclusive=new DateTime(2026,11,1);
        public void Validate()
        {
            if(Genetic==null||WalkForward==null||Robustness==null||
               Portfolio==null||AccountRisk==null||
               CandidateAuditLimit<3||CandidateAuditLimit>10000||
               SignalCacheBytes<1||MinimumFullDaysPerMonth<1||
               MinimumFullDaysPerMonth>23)
                throw new ArgumentException("Invalid V16 research settings");
            Genetic.Validate();
            WalkForward.Validate();
            Robustness.Validate();
            Portfolio.Validate();
            AccountRisk.Validate();
        }
    }

    public sealed class NQResearchRunV16
    {
        public string Reason,DevelopmentChecksum;
        public bool Completed,HasFrozenCandidates;
        public int GeneticEvaluated,RobustnessChecked,RobustnessPassed;
        public NQEvolutionSummaryV12 Genetic;
        public NQWalkForwardResultV15 WalkForward;
        public NQIntegratedPortfolioRiskResultV15 PortfolioRisk;
        public NQNativeFrozenCampaignV16 FrozenCampaign;
        public readonly List<string> RobustCandidateKeys=new List<string>();
    }

    public static class NQNativeResearchRunnerV16
    {
        public static NQResearchRunV16 Run(NQDataLoadV16 development,
            int[] baseline,NQResearchConfigV16 cfg)
        {
            var r=new NQResearchRunV16{
                Completed=false,HasFrozenCandidates=false,
                Reason="INVALID_DEVELOPMENT_INPUT"
            };
            if(development==null||development.Manifest==null||
               development.Bars==null||
               development.Manifest.Partition!=
                   NQDataPartitionV16.Development2020_2022||
               baseline==null||baseline.Length!=20||cfg==null)
                return r;
            cfg.Validate();
            r.DevelopmentChecksum=development.Manifest.Sha256;
            if(development.Manifest.FullSessionsByMonth.Length!=36 ||
               development.Manifest.FullSessionsByMonth.Any(x=>
                  x<cfg.MinimumFullDaysPerMonth))
            {
                r.Reason="DEVELOPMENT_SOURCE_INCOMPLETE";
                return r;
            }
            // No OOS data object can enter this routine. The only source
            // passed into V14/V15 is the DEVELOPMENT snapshot above.
            var pipeline=new NQNativeCachedPipelineV14(
                development.Bars,baseline,cfg.Genetic,true,true,
                cfg.SignalCacheBytes);
            r.Genetic=pipeline.Run();
            r.GeneticEvaluated=r.Genetic.Evaluated.Count;
            var qualified=new List<NQPortfolioExecutionCandidateV15>();
            var genesById=new Dictionary<string,int[]>(StringComparer.Ordinal);
            foreach(var candidate in r.Genetic.Evaluated
                .OrderByDescending(x=>x.Score)
                .ThenBy(x=>x.Genome.Canonical.RuntimeKey,
                    StringComparer.Ordinal)
                .Take(cfg.CandidateAuditLimit))
            {
                r.RobustnessChecked++;
                int[] genes=candidate.Genome.Genes;
                var run=pipeline.Cache.Evaluate(genes);
                if(!run.Valid)continue;
                var robust=NQNativeRobustnessV13.Evaluate(
                    run.Trades,cfg.Robustness);
                if(!robust.Valid||!robust.ProvisionalRobustPass)
                    continue;
                // V12's detailed fill ledger must fully reconcile with
                // closed trade list before a candidate enters the portfolio.
                if(run.Executed.Count!=run.Trades.Count)
                    throw new InvalidOperationException(
                        "V12 executed-fill ledger is incomplete");
                string key=candidate.Genome.Canonical.RuntimeKey;
                string id="NQ-"+r.RobustnessPassed.ToString("D5");
                r.RobustnessPassed++;
                qualified.Add(new NQPortfolioExecutionCandidateV15(
                    id,run.Trades,run.Executed));
                genesById.Add(id,(int[])genes.Clone());
                r.RobustCandidateKeys.Add(key);
            }
            r.Completed=true;
            if(qualified.Count<cfg.Portfolio.TargetStrategies)
            {
                r.Reason="NOT_ENOUGH_G0_ROBUST_GENOMES";
                return r;
            }
            r.PortfolioRisk=NQNativeIntegratedPortfolioRiskV15.Evaluate(
                development.Bars,qualified,cfg.Robustness,cfg.Portfolio,
                cfg.AccountRisk);
            if(!r.PortfolioRisk.Valid||!r.PortfolioRisk.ProvisionalPass)
            {
                r.Reason="PORTFOLIO_RISK_OR_DIVERSITY_REJECT";
                return r;
            }
            // Independent nested development walk-forward. Passing this
            // only shows the general generator research stayed stable:
            // the frozen portfolio must ALSO pass the genuine 2023–24 OOS.
            r.WalkForward=new NQNativeWalkForwardV15(
                development.Bars,baseline,cfg.WalkForward).Run();
            if(!r.WalkForward.Valid ||
               !r.WalkForward.ProvisionalStabilityPass)
            {
                r.Reason="NESTED_DEVELOPMENT_WALK_FORWARD_REJECT";
                return r;
            }
            var frozen=new List<NQFrozenCandidateV16>();
            foreach(var selected in r.PortfolioRisk.Selection.Selected)
                frozen.Add(new NQFrozenCandidateV16(selected.Id,
                    genesById[selected.Id]));
            r.FrozenCampaign=new NQNativeFrozenCampaignV16(
                development.Manifest,r.PortfolioRisk,frozen,
                cfg.AccountRisk,cfg.MinimumFullDaysPerMonth,
                cfg.FinalCutoffExclusive);
            r.HasFrozenCandidates=true;
            r.Reason="FROZEN_DEVELOPMENT_ONLY_READY_FOR_EXTERNAL";
            return r;
        }
    }
}
