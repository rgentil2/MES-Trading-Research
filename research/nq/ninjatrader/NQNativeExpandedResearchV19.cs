// S0.80 V19 — 120 implemented technical formulas, 1320 directional predicates.
// The research GA, M1 simulated economics, bounded cache and resumable journal run against the NEW versioned catalog.
// S0.79 V19 — 36 distinct OHLCV feature families x 11 predicates.
// Uses SAME economic V12 filled-trade model/V9 ranking and SAME
// genetic evolution V12, but versioned V19 canonical keys/domains.
// V11's original 132 ids and V12 default engine remain unchanged.
// Inputs: 2020–22 completed NQ M1 only, read-only research.
// No 2023+ tuning, no native NT8 orders, no real-market profit claim.
using System;
using System.Collections.Generic;
using System.Linq;

namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQNativeExpandedResearchV19
    {
        private readonly NQNativeSignalCacheV14 cache;
        private readonly NQGeneRangeV11[] domains;
        private readonly NQEvolutionConfigV12 cfg;
        private readonly string catalogTag=
            "V19_120_FEATURES_1320_PREDICATES_V12_FILLS_V9_FITNESS_V1";
        public NQNativeSignalCacheV14 Cache{get{return cache;}}

        private static int Direction(
            IList<NQBarV11> bars,int type,int period)
        {
            bool bull,bear;
            if(!NQNativeConditionCatalogV19.TryEvaluate(bars,type,
                period,out bull,out bear)||bull&&bear)
                return -2;
            return bull?1:bear?-1:0;
        }
        public NQNativeExpandedResearchV19(
            IList<NQTimedBarV12> source,int[] baseline,
            NQEvolutionConfigV12 settings,bool exploreExits,
            bool requireAll36Months,long maxSignalCacheBytes,
            long maxAtrCacheBytes=67108864)
        {
            if(baseline==null||baseline.Length!=20||settings==null)
                throw new ArgumentException(
                    "20-gene baseline and V12 genetic configuration required");
            var identity=NQNativeExitCanonicalV19.Analyze(baseline);
            if(identity.IsRedundant)
                throw new ArgumentException("Redundant initial baseline");
            settings.Validate();
            cfg=settings;
            domains=NQNativeExitCanonicalV19.DefaultDomains(
                baseline,exploreExits);
            cache=new NQNativeSignalCacheV14(source,maxSignalCacheBytes,
                maxAtrCacheBytes,NQNativeConditionCatalogV19.Count,
                Direction);
            if(requireAll36Months &&
               !cache.HasSufficientMonthCoverage)
                throw new InvalidOperationException(
                    "All 36 months 2020–22 require >=15 full sessions");
        }

        public NQHistoricalResultV12 Evaluate(int[] genes)
        {
            return cache.EvaluateExpanded(genes,
                NQNativeExitCanonicalV19.Analyze);
        }

        public NQEvolutionSummaryV12 Run()
        {
            return new NQEvolutionEngineV12(domains,cfg,
                NQNativeExitCanonicalV19.Analyze).Run(
                genome=>Evaluate(genome.Genes).Score);
        }

        public NQEvolutionSummaryV12 RunWithJournal(
            string journalPath,string developmentSourceSha256)
        {
            string signature=NQNativeScoreJournalV17.Fingerprint(
                cfg,domains,catalogTag);
            using(var journal=new NQNativeScoreJournalV17(
                journalPath,developmentSourceSha256,signature,64,
                NQNativeExitCanonicalV19.Analyze))
            {
                var evolution=new NQEvolutionEngineV12(domains,cfg,
                    NQNativeExitCanonicalV19.Analyze);
                return evolution.Run(g=>journal.Score(g,x=>
                    Evaluate(x.Genes).Score));
            }
        }
    }
}
