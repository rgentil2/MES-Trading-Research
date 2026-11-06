// S0.83 V22 final 150/5/PF/cost/DD/MC/annual/portfolio/WF audit before frozen OOS.
// S0.82 — V21 durable full-economics research runner over all 1320 conditions.
// Inputs: 2020–22 development ONLY, V19 GA/V12 M1 economics -> V13
// robustness -> V15 combined 3–5 account risk -> V20 train-only WF ->
// V16 versioned frozen OOS evaluator 2023–24 then 2025–26.
// Source-bound COMPLETE economic ledger, ranked finalists, fill receipts. NO NT8 native order calls.
// Fail closed when there are no G0 survivors; never manufacture edge.
using System;
using System.Collections.Generic;
using System.Linq;
namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQResearchRunV22
    {
        public string Reason,DevelopmentChecksum;
        public bool Completed,HasFrozenCandidates;
        public int GeneticEvaluated,RobustnessChecked,RobustnessPassed;
        public NQEvolutionSummaryV12 Genetic;
        public NQBulkEconomicResultV21 Bulk;
        public NQPortfolioAuditResultV22 Audit;
        public NQWalkForwardResultV15 WalkForward;
        public NQIntegratedPortfolioRiskResultV15 PortfolioRisk;
        public NQNativeFrozenCampaignV16 FrozenCampaign;
        public readonly List<string> RobustCandidateKeys=
            new List<string>();
    }

    public static class NQNativeResearchRunnerV22
    {
        public static NQResearchRunV22 Run(NQDataLoadV16 development,
            int[] baseline,NQResearchConfigV16 cfg,
            string ledgerPath,string rankingPath,string fillsPath,
            int shortlist,int featureCacheBytes,
            NQPortfolioAuditConfigV22 auditConfig=null)
        {
            var r=new NQResearchRunV22{
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
            // V19 source-genome identity + all 1,320 signal types.
            // Coverage is checked above using operator config, not the
            // hardcoded 15-session legacy V14 requireFull36 flag.
            r.Bulk=NQNativeBulkEconomicV21.Run(
                development.Bars,baseline,cfg.Genetic,
                development.Manifest.Sha256,ledgerPath,rankingPath,
                fillsPath,shortlist,cfg.SignalCacheBytes,
                featureCacheBytes,true);
            r.Genetic=r.Bulk.Evolution;
            // The top candidates are rechecked with the identical V12
            // M1 estimator before entering the V13 portfolio risk gate.
            var cache=new NQNativeSignalCacheV14(
                development.Bars,cfg.SignalCacheBytes,67108864,
                NQNativeConditionCatalogV19.Count,
                NQNativeExpandedResearchV19.Direction);
            var memo=new NQNativeFeatureMemoV21(cache,featureCacheBytes);
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
                var run=memo.Evaluate(genes);
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
            r.WalkForward=new NQNativeWalkForwardV20(
                development.Bars,baseline,cfg.WalkForward).Run();
            if(!r.WalkForward.Valid ||
               !r.WalkForward.ProvisionalStabilityPass)
            {
                r.Reason="NESTED_DEVELOPMENT_WALK_FORWARD_REJECT";
                return r;
            }
            // Audit ONLY the same 3–5 V13-selected strategies. Do not
            // accidentally allow a profitable unselected candidate or a
            // failing annual/cost/Monte Carlo result into the frozen book.
            var selectedIds=new HashSet<string>(
                r.PortfolioRisk.Selection.Selected.Select(x=>x.Id),
                StringComparer.Ordinal);
            var selectedInputs=qualified.Where(x=>
                selectedIds.Contains(x.Id)).ToList();
            var selectedGenes=new Dictionary<string,int[]>(
                StringComparer.Ordinal);
            foreach(var selected in r.PortfolioRisk.Selection.Selected)
                selectedGenes.Add(selected.Id,genesById[selected.Id]);
            r.Audit=NQNativePortfolioAuditV22.Evaluate(
                development.Bars,selectedInputs,selectedGenes,
                cfg.Robustness,cfg.Portfolio,cfg.AccountRisk,
                r.WalkForward,auditConfig??
                    new NQPortfolioAuditConfigV22());
            if(!r.Audit.Valid||!r.Audit.ProvisionalPass)
            {
                r.Reason="V22_FINAL_PORTFOLIO_AUDIT_REJECT_"+
                    r.Audit.Reason;
                return r;
            }
            var frozen=r.Audit.Frozen;
            var frozenEvaluator=new NQNativeV20OosEvaluator(
                cfg.SignalCacheBytes);
            r.FrozenCampaign=new NQNativeFrozenCampaignV16(
                development.Manifest,r.PortfolioRisk,frozen,
                cfg.AccountRisk,cfg.MinimumFullDaysPerMonth,
                cfg.FinalCutoffExclusive,frozenEvaluator.Evaluate,
                "EXCANv19_1320_CONDITIONS_V20_OOS_SAME_V12_FILLS");
            r.HasFrozenCandidates=true;
            r.Reason="FROZEN_DEVELOPMENT_ONLY_READY_FOR_EXTERNAL";
            return r;
        }
    }
}
