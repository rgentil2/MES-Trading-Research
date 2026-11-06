// NQ S0.69 — Continuous discovery score for native NT8 Strategy Analyzer.
// Research-only. NOT an acceptance gate and NOT a recommendation to trade.
// G0 hard gates (V7) remain unchanged and must be applied after discovery.
// 2020-2022 in-sample; held-out years are never consumed here.
using System;
using System.Collections.Generic;

namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQDiscoveryResultV9
    {
        public bool Valid { get; internal set; }
        public string Reason { get; internal set; }
        public double Score { get; internal set; }
        public int Trades { get; internal set; }
        public double NetUSD { get; internal set; }
        public double ProfitFactor { get; internal set; }
        public double StressDDUSD { get; internal set; }
        public int MonthsBelowFive { get; internal set; }
        public int PositiveYears { get; internal set; }
        public bool HardG0Pass { get; internal set; }
    }

    public static class NQNativeDiscoveryScoreV9
    {
        // Distinct from V7's -1e12 reject: all valid but economically weak
        // systems receive a FINITE, COMPARABLE score for broad exploration.
        public const double InvalidScore = -1000000000000.0;
        private static bool Finite(double x)
        { return !Double.IsNaN(x) && !Double.IsInfinity(x); }

        public static NQDiscoveryResultV9 Evaluate(
            IList<NQG0RiskTradeV7> trades, double nativeNetUSD)
        {
            var bad = new NQDiscoveryResultV9 {
                Valid = false, Reason = "INVALID", Score = InvalidScore
            };
            if (trades == null || trades.Count == 0 || !Finite(nativeNetUSD))
                return bad;

            NQG0DiagnosticsResultV7 diagnostic =
                NQNativeG0DiagnosticsV7.Evaluate(trades, nativeNetUSD);
            if (diagnostic == null || !diagnostic.Valid ||
                diagnostic.Economic == null)
            {
                bad.Reason = diagnostic == null ? "NO_DIAGNOSTIC" :
                    diagnostic.FirstV6Failure;
                return bad;
            }
            NQG0ResultV6 e = diagnostic.Economic;
            double stress = diagnostic.MaeMfeStressDrawdownUSD;
            if (!Finite(e.NetProfitUSD) || !Finite(e.ProfitFactor) ||
                !Finite(stress) || stress < 0.0)
            {
                bad.Reason = "NONFINITE_ECONOMICS";
                return bad;
            }

            // Annual net returns are from entry year for the full,
            // already-closed native trade history in the frozen IST.
            // This is a research consistency feature, not a walk-forward.
            double[] annual = new double[3];
            foreach (NQG0RiskTradeV7 t in trades)
            {
                if (t == null || t.EntryTime.Year < 2020 ||
                    t.EntryTime.Year > 2022)
                {
                    bad.Reason = "YEAR_OUTSIDE_IST";
                    return bad;
                }
                annual[t.EntryTime.Year - 2020] += t.NetProfitUSD;
            }
            int positiveYears = 0;
            for (int i = 0; i < annual.Length; i++)
                if (annual[i] > 0.0) positiveYears++;

            // Continuous fitness, NOT a permissive pass:
            // - profitability as risk-aware profit factor and net PnL
            // - penalty for stress drawdown even BEFORE $2k hard threshold
            // - frequency gaps and low sample size reduce discovery rank
            // - annual stability reward is limited (no holdout used)
            // Bounded log prevents zero-PF from producing -Infinity.
            double pf = Math.Max(0.01, Math.Min(100.0, e.ProfitFactor));
            double score =
                  5000.0 * Math.Log(pf)
                + 0.10 * e.NetProfitUSD
                - 0.50 * stress
                - 800.0 * e.MonthsBelowFive
                - 30.0 * Math.Max(0, 150 - e.Trades)
                + 500.0 * positiveYears
                - 500.0 * (3 - positiveYears);

            if (!Finite(score))
            {
                bad.Reason = "NONFINITE_SCORE";
                return bad;
            }
            return new NQDiscoveryResultV9 {
                Valid = true,
                Reason = "RANK_ONLY",
                Score = score,
                Trades = e.Trades,
                NetUSD = e.NetProfitUSD,
                ProfitFactor = e.ProfitFactor,
                StressDDUSD = stress,
                MonthsBelowFive = e.MonthsBelowFive,
                PositiveYears = positiveYears,
                HardG0Pass = diagnostic.Pass
            };
        }
    }
}
