// Offline engineering test harness only: NOT a NinjaTrader backtest,
// NOT evidence of MFFU compliance, and NOT an OOS run.
using System;
using System.Globalization;
using NinjaTrader.NinjaScript.Strategies;

internal static class Program
{
    private static int _checks;

    private static void Check(bool condition, string label)
    {
        _checks++;
        if (!condition)
            throw new Exception("MNQ_R1_TEST_FAIL " + label);
    }

    private static void AssertSized(
        NQMnqInstrumentR1 instrument, int stopTicks,
        int expectedContracts, decimal expectedRiskUSD)
    {
        var x = NQMnqRiskSizingExperimentR1.Size(instrument, stopTicks);
        Check(x.Status == NQMnqSizingStatusR1.Sized,
            "status " + instrument + " " + stopTicks);
        Check(x.Contracts == expectedContracts,
            "quantity " + instrument + " " + stopTicks);
        Check(x.EstimatedRiskUSD == expectedRiskUSD,
            "risk " + instrument + " " + stopTicks);
        Check(x.EstimatedRiskUSD <= 200m, "hard risk budget");
    }

    private static void RunTests()
    {
        // NQ threshold: 35 ticks = $199.68; 36 = $204.68.
        AssertSized(NQMnqInstrumentR1.NQ, 35, 1, 199.68m);
        Check(NQMnqRiskSizingExperimentR1.Size(
            NQMnqInstrumentR1.NQ, 36).Status ==
            NQMnqSizingStatusR1.RiskTooLarge, "NQ 36 ticks rejected");

        // MNQ cost per contract 4 ticks slippage * $0.5 + $1.9.
        Check(NQMnqRiskSizingExperimentR1.PerContractCostUSD(
            NQMnqInstrumentR1.MNQ) == 3.90m, "MNQ cost");
        Check(NQMnqRiskSizingExperimentR1.PerContractCostUSD(
            NQMnqInstrumentR1.NQ) == 24.68m, "NQ cost");
        AssertSized(NQMnqInstrumentR1.MNQ, 60, 5, 169.50m);
        AssertSized(NQMnqInstrumentR1.MNQ, 80, 4, 175.60m);
        AssertSized(NQMnqInstrumentR1.MNQ, 120, 3, 191.70m);
        AssertSized(NQMnqInstrumentR1.MNQ, 160, 2, 167.80m);
        AssertSized(NQMnqInstrumentR1.MNQ, 240, 1, 123.90m);
        AssertSized(NQMnqInstrumentR1.MNQ, 392, 1, 199.90m);
        Check(NQMnqRiskSizingExperimentR1.Size(
            NQMnqInstrumentR1.MNQ, 393).Status ==
            NQMnqSizingStatusR1.RiskTooLarge, "MNQ 393 ticks rejected");
        Check(NQMnqRiskSizingExperimentR1.Size(
            NQMnqInstrumentR1.MNQ, 401).Status ==
            NQMnqSizingStatusR1.InvalidStop, "experimental cap");
        Check(NQMnqRiskSizingExperimentR1.Size(
            NQMnqInstrumentR1.MNQ, 0).Status ==
            NQMnqSizingStatusR1.InvalidStop, "zero stop");
        var r = NQMnqRiskSizingExperimentR1.Size(
            NQMnqInstrumentR1.MNQ, 80);
        Check(r.ExposureNqEquivalent == 0.4m, "exposure conversion");
        Check(r.StopTicks == 80, "stop unchanged");

        int ticks;
        Check(NQMnqRiskSizingExperimentR1.TryAtrStopTicks(
            12.0, 20, out ticks) && ticks == 96, "ATR 2x = 24 points");
        Check(NQMnqRiskSizingExperimentR1.TryAtrStopTicks(
            13.76, 10, out ticks) && ticks == 56, "ATR over V5 55 cap");
        Check(NQMnqRiskSizingExperimentR1.TryAtrStopTicks(
            98.0, 10, out ticks) && ticks == 392, "ATR 98 points");
        Check(!NQMnqRiskSizingExperimentR1.TryAtrStopTicks(
            101.0, 10, out ticks) && ticks == 0, "ATR cap fail closed");
        Check(!NQMnqRiskSizingExperimentR1.TryAtrStopTicks(
            double.NaN, 20, out ticks), "ATR NaN");
        Check(!NQMnqRiskSizingExperimentR1.TryAtrStopTicks(
            12.0, 31, out ticks), "invalid multiplier");
        Console.WriteLine("MNQ_R1_TEST_PASS checks=" + _checks +
            " mode=OFFLINE_SYNTHETIC_RISK_MATH_ONLY OOS=LOCKED");
    }

    private static void PrintExamples()
    {
        Console.WriteLine("stop_points\tnq_contracts\tnq_risk_usd\tmnq_contracts\tmnq_risk_usd\tmnq_nq_equivalent");
        foreach (int points in new[] { 10, 15, 20, 30, 40, 60, 98, 100 })
        {
            var nq = NQMnqRiskSizingExperimentR1.Size(
                NQMnqInstrumentR1.NQ, points * 4);
            var mnq = NQMnqRiskSizingExperimentR1.Size(
                NQMnqInstrumentR1.MNQ, points * 4);
            Console.WriteLine(string.Join("\t",
                points.ToString(CultureInfo.InvariantCulture),
                nq.Contracts.ToString(CultureInfo.InvariantCulture),
                nq.EstimatedRiskUSD.ToString(CultureInfo.InvariantCulture),
                mnq.Contracts.ToString(CultureInfo.InvariantCulture),
                mnq.EstimatedRiskUSD.ToString(CultureInfo.InvariantCulture),
                mnq.ExposureNqEquivalent.ToString(CultureInfo.InvariantCulture)));
        }
        Console.WriteLine("DIAGNOSTIC_ONLY: NO MARKET DATA, FILLS OR PORTFOLIO BACKTEST");
    }

    public static int Main(string[] args)
    {
        if (args.Length != 1 || (args[0] != "--self-test" &&
                                 args[0] != "--examples"))
        {
            Console.Error.WriteLine("Usage: --self-test OR --examples");
            return 2;
        }
        if (args[0] == "--self-test") RunTests();
        else PrintExamples();
        return 0;
    }
}
