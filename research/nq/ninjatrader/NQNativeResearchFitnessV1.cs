// S0.40/S0.41 optional native Strategy Analyzer Optimization Fitness.
// Install alongside NQNativeGeneticLabV1.cs in NinjaTrader's NinjaScript Editor.
// Correct NT8 TradesPerformanceValues.Drawdown casing per official API.
// Not compiled/tested in NinjaTrader yet; no forward/holdout authorization.
//
// Fitness = G0-like coarse gating for research ON IST 2020-22 ONLY.
// IMPORTANT: maximum drawdown here is Strategy Analyzer's CLOSED-TRADE
// performance metric; it is NOT an MFFU intraday/equity/trailing account audit.
// This does not check monthly cadence, annual stability or portfolio overlaps.
using System;
using NinjaTrader.NinjaScript;

namespace NinjaTrader.NinjaScript.OptimizationFitnesses
{
    public class NQNativeResearchFitnessV1 : OptimizationFitness
    {
        protected override void OnCalculatePerformanceValue(StrategyBase strategy)
        {
            var performance = strategy.SystemPerformance.AllTrades.TradesPerformance;
            int trades = performance.TradesCount;
            double pf = performance.ProfitFactor;
            double net = performance.NetProfit;
            double closedDrawdown = Math.Abs(performance.Currency.Drawdown);

            // Fail closed, no optimization reward for tiny-sample/no-loss
            // systems, or for unacceptable closed-trade drawdown.
            if (trades < 150 ||
                double.IsNaN(pf) || double.IsInfinity(pf) ||
                double.IsNaN(net) || double.IsInfinity(net) ||
                double.IsNaN(closedDrawdown) || double.IsInfinity(closedDrawdown) ||
                pf < 1.25 || net <= 0 || closedDrawdown > 2000.0)
            {
                Value = -1.0e12;
                return;
            }

            // A preliminary ranking only. Native execution and costs must be
            // configured in NT8, and formal later-stage tests remain required.
            Value = (net / (1.0 + closedDrawdown)) * Math.Min(5.0, pf)
                    * Math.Sqrt(trades);
        }
    }
}
