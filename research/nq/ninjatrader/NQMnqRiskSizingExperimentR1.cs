// EXPERIMENT R1 -- isolated NQ vs MNQ position sizing research.
// No NinjaTrader orders, no OOS access, no modifications to PF1 v1.0.0.
// This C# math is dependency-free so it can be tested on GitHub Actions
// and later reused inside an explicitly separate NinjaScript experiment.
using System;

namespace NinjaTrader.NinjaScript.Strategies
{
    public enum NQMnqInstrumentR1 { NQ, MNQ }

    public enum NQMnqSizingStatusR1
    {
        Sized,
        InvalidStop,
        RiskTooLarge
    }

    public sealed class NQMnqSizingResultR1
    {
        public NQMnqInstrumentR1 Instrument { get; internal set; }
        public NQMnqSizingStatusR1 Status { get; internal set; }
        public int StopTicks { get; internal set; }
        public int Contracts { get; internal set; }
        public decimal EstimatedRiskUSD { get; internal set; }
        public decimal ExposureNqEquivalent { get; internal set; }
        public decimal RoundTripCostPerContractUSD { get; internal set; }
    }

    public static class NQMnqRiskSizingExperimentR1
    {
        public const int MaxMnqContracts = 5;
        public const int MaxResearchStopTicks = 400; // 100 NQ points; R1 experimental only.
        public const int SlippageTicksPerSide = 2;
        public const decimal MaximumPlannedRiskUSD = 200m;
        public const decimal NqTickValueUSD = 5m;
        public const decimal MnqTickValueUSD = 0.5m;
        public const decimal NqCommissionRoundTripUSD = 4.68m;
        public const decimal MnqCommissionRoundTripUSD = 1.90m;

        // A cost assumption, NOT a guarantee of broker fills or commissions.
        // Every contract pays entry + exit slippage and an RT commission once.
        public static decimal PerContractCostUSD(NQMnqInstrumentR1 instrument)
        {
            decimal tickValue = instrument == NQMnqInstrumentR1.NQ
                ? NqTickValueUSD : MnqTickValueUSD;
            decimal fee = instrument == NQMnqInstrumentR1.NQ
                ? NqCommissionRoundTripUSD : MnqCommissionRoundTripUSD;
            return 2m * SlippageTicksPerSide * tickValue + fee;
        }

        public static NQMnqSizingResultR1 Size(
            NQMnqInstrumentR1 instrument, int originalStopTicks)
        {
            if (instrument != NQMnqInstrumentR1.NQ &&
                instrument != NQMnqInstrumentR1.MNQ)
                throw new ArgumentOutOfRangeException("instrument");

            var result = new NQMnqSizingResultR1
            {
                Instrument = instrument,
                StopTicks = originalStopTicks,
                RoundTripCostPerContractUSD = PerContractCostUSD(instrument),
                Status = NQMnqSizingStatusR1.InvalidStop
            };
            // Preserve the original stop. Never reduce it to force a trade.
            if (originalStopTicks < 1 ||
                originalStopTicks > MaxResearchStopTicks)
                return result;

            decimal tickValue = instrument == NQMnqInstrumentR1.NQ
                ? NqTickValueUSD : MnqTickValueUSD;
            decimal perContractRisk = originalStopTicks * tickValue +
                result.RoundTripCostPerContractUSD;
            int maxContracts = instrument == NQMnqInstrumentR1.NQ
                ? 1 : MaxMnqContracts;
            int quantity = 0;
            for (int q = maxContracts; q >= 1; q--)
            {
                if (q * perContractRisk <= MaximumPlannedRiskUSD)
                {
                    quantity = q;
                    break;
                }
            }
            if (quantity == 0)
            {
                result.Status = NQMnqSizingStatusR1.RiskTooLarge;
                return result;
            }

            result.Status = NQMnqSizingStatusR1.Sized;
            result.Contracts = quantity;
            result.EstimatedRiskUSD = quantity * perContractRisk;
            result.ExposureNqEquivalent = instrument ==
                NQMnqInstrumentR1.NQ ? quantity : quantity / 10m;
            return result;
        }

        // ATR is computed on a COMPLETED bar, outside this function.
        // In contrast to the historic V5's 55-tick cap, this R1 experiment
        // admits 1..400 ticks, without changing V5 or the PF1 contract.
        public static bool TryAtrStopTicks(
            double atrPoints, int stopMultiplierX10, out int stopTicks)
        {
            stopTicks = 0;
            if (double.IsNaN(atrPoints) ||
                double.IsInfinity(atrPoints) || atrPoints <= 0 ||
                stopMultiplierX10 < 10 || stopMultiplierX10 > 30)
                return false;
            double rawTicks = atrPoints * 4.0 *
                (stopMultiplierX10 / 10.0);
            if (double.IsNaN(rawTicks) ||
                double.IsInfinity(rawTicks) || rawTicks <= 0 ||
                rawTicks > MaxResearchStopTicks)
                return false;
            int rounded = (int)Math.Ceiling(rawTicks);
            if (rounded < 1 || rounded > MaxResearchStopTicks)
                return false;
            stopTicks = rounded;
            return true;
        }
    }
}
