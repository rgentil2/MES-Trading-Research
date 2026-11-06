// S0.69 — native NinjaTrader 8 discovery fitness.
// This ranks candidate backtests. It deliberately DOES NOT accept them for
// prop-account use. Use strict NQNativeG0RiskFitnessV7 for final G0.
// Accepts V5 and derived V8 audit strategies; no trades or orders here.
using System;
using System.Collections.Generic;
using System.Globalization;
using NinjaTrader.Cbi;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.Strategies;

namespace NinjaTrader.NinjaScript.OptimizationFitnesses
{
    public class NQNativeDiscoveryFitnessV9 : OptimizationFitness
    {
        private static string F(double value)
        { return value.ToString("F2", CultureInfo.InvariantCulture); }

        protected override void OnCalculatePerformanceValue(StrategyBase strategy)
        {
            Value = NQNativeDiscoveryScoreV9.InvalidScore;
            var candidate = strategy as NQNativeGeneticLabV5;
            if (candidate == null || !candidate.CanonicalReady ||
                candidate.IsStructurallyRedundant ||
                candidate.EffectiveConditionCount < 1)
                return;
            try
            {
                var history = strategy.SystemPerformance.AllTrades;
                var closed = new List<NQG0RiskTradeV7>(history.Count);
                for (int i = 0; i < history.Count; i++)
                {
                    Trade trade = history[i];
                    if (trade == null || trade.Entry == null || trade.Exit == null)
                        return;
                    closed.Add(new NQG0RiskTradeV7(
                        trade.Entry.Time, trade.Exit.Time,
                        trade.ProfitCurrency, trade.MaeCurrency, trade.MfeCurrency));
                }
                NQDiscoveryResultV9 result =
                    NQNativeDiscoveryScoreV9.Evaluate(
                        closed, history.TradesPerformance.NetProfit);
                if (result == null || !result.Valid)
                {
                    NinjaTrader.Code.Output.Process(
                        "NQ_DISCOVERY_V9 INVALID id=" +
                        (candidate.CanonicalRuntimeFingerprint ?? "NONE") +
                        " reason=" + (result == null ? "NULL" : result.Reason),
                        PrintTo.OutputTab1);
                    return;
                }
                Value = result.Score;
                NinjaTrader.Code.Output.Process(
                    "NQ_DISCOVERY_V9 SCORE id=" +
                    candidate.CanonicalRuntimeFingerprint +
                    " rank=" + F(result.Score) +
                    " net=" + F(result.NetUSD) +
                    " pf=" + result.ProfitFactor.ToString("F4", CultureInfo.InvariantCulture) +
                    " stressDD=" + F(result.StressDDUSD) +
                    " trades=" + result.Trades +
                    " monthsBelow5=" + result.MonthsBelowFive +
                    " positiveYears=" + result.PositiveYears +
                    " strictG0=" + result.HardG0Pass +
                    " NOTE=DISCOVERY_ONLY_NOT_DEPLOYABLE",
                    PrintTo.OutputTab1);
            }
            catch (Exception ex)
            {
                Value = NQNativeDiscoveryScoreV9.InvalidScore;
                NinjaTrader.Code.Output.Process(
                    "NQ_DISCOVERY_V9 ERROR " +
                    ex.GetType().Name + " " + ex.Message,
                    PrintTo.OutputTab1);
            }
        }
    }
}
