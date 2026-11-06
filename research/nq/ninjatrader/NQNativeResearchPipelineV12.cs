// S0.72 — single-call research pipeline: 132-condition V11 genomes ->
// pure C# genetic search V12 -> conservative historical M1 fills ->
// original V9 discovery score and original V7 risk diagnostics.
// Does not require NinjaTrader to execute, but REQUIRES real sorted NQ M1
// bars for meaningful results. Data is NOT present in this GitHub repo.
// Optional fixture mode only for tests. Never uses OOS 2023+ data.
using System;
using System.Collections.Generic;
namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQNativeResearchPipelineV12
    {
        public readonly IList<NQTimedBarV12> Bars;
        public readonly int[] Baseline;
        public readonly bool ExploreExits;
        public readonly bool RequireFullDevelopmentWindow;
        public readonly NQEvolutionConfigV12 Config;

        public NQNativeResearchPipelineV12(IList<NQTimedBarV12> bars,
            int[] baseline,NQEvolutionConfigV12 cfg,bool exploreExits,
            bool requireFullDevelopmentWindow)
        {
            if(bars==null||baseline==null||baseline.Length!=20||cfg==null)
                throw new ArgumentException("M1 bars, 20 genes and V12 config required");
            Bars=bars;
            Baseline=(int[])baseline.Clone();
            Config=cfg;
            ExploreExits=exploreExits;
            RequireFullDevelopmentWindow=requireFullDevelopmentWindow;
        }

        private void ValidateDataset()
        {
            if(Bars.Count==0)throw new InvalidOperationException("No NQ M1 data");
            var monthSeen=new bool[36];
            DateTime prior=DateTime.MinValue;
            foreach(var b in Bars)
            {
                if(b==null||b.Time.Year<2020||b.Time.Year>2022||
                   b.Time<=prior)
                    throw new InvalidOperationException(
                        "Unsorted, null or held-out 2023+ M1 data");
                prior=b.Time;
                monthSeen[(b.Time.Year-2020)*12+b.Time.Month-1]=true;
            }
            if(RequireFullDevelopmentWindow)
            {
                foreach(bool present in monthSeen)
                    if(!present)
                        throw new InvalidOperationException(
                            "Incomplete 36-month 2020-22 in-sample window");
            }
        }

        public NQEvolutionSummaryV12 Run()
        {
            ValidateDataset();
            var ranges=NQEvolutionEngineV12.DefaultDomains(Baseline,
                ExploreExits);
            var engine=new NQEvolutionEngineV12(ranges,Config);
            // This callback is the real V9 economic SCORE on a simulated
            // M1 trade list, NOT a synthetic oracle. It is NOT native
            // NT8 fill parity and not an MFFU acceptance test.
            return engine.Run(genome=>
                NQNativeHistoricalEvaluatorV12.Evaluate(
                    Bars,genome.Genes).Score);
        }
    }
}
