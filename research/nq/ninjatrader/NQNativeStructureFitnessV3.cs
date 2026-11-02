// S0.49 - Mandatory V3 structural search fitness for NinjaTrader Strategy Analyzer.
// Use "Optimize on: NQNativeStructureFitnessV3" (NOT Max. net profit).
// Penalizes redundant boolean rules and no-trade genotypes with a strongly
// negative number so no-trade/no-signal candidates do not beat losing ones.
// On usable candidates the objective is the exact native NET profit in USD.
// NOT a formal G0 filter, not 132 indicators, not a unique-10K optimizer.
// Does not skip historical backtest of duplicate genomes: only down-ranks them.
//
// All computations operate in NinjaTrader 8 C#; no Python integration.
using System;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.Strategies;

namespace NinjaTrader.NinjaScript.OptimizationFitnesses
{
    public class NQNativeStructureFitnessV3 : OptimizationFitness
    {
        protected override void OnCalculatePerformanceValue(StrategyBase strategy)
        {
            // Fail closed for unrelated strategies. Ensure the selected
            // "Optimize on" cannot silently score non-V3 results.
            var v3 = strategy as NQNativeGeneticLabV3;
            if (v3 == null || !v3.CanonicalReady ||
                v3.IsStructurallyRedundant || v3.EffectiveConditionCount < 1)
            {
                Value = -1.0e12;
                return;
            }

            var results = strategy.SystemPerformance.AllTrades.TradesPerformance;
            double net = results.NetProfit;
            int count = results.TradesCount;
            if (count < 1 || double.IsNaN(net) || double.IsInfinity(net))
            {
                Value = -1.0e12;
                return;
            }

            // Diagnostic smoke objective only, same economic objective as V2.
            // Later G0 must enforce PF>=1.25, DD<=2000 and sample/holdouts.
            Value = net;
        }
    }
}
