using System;
using System.Collections.Generic;
using NinjaTrader.NinjaScript.Strategies;

internal static class Program
{
    private static void Check(bool condition, string message)
    {
        if (!condition) throw new Exception("ASSERT: " + message);
    }

    private static List<NQG0RiskTradeV7> Sample(double win, double loss,
        double mae, double mfe, bool sparse = false)
    {
        var trades = new List<NQG0RiskTradeV7>();
        for (int year = 2020; year <= 2022; year++)
        for (int month = 1; month <= 12; month++)
        for (int day = 1; day <= (sparse ? 1 : 5); day++)
        {
            DateTime entry = new DateTime(year, month, day, 10, 0, 0);
            double net = day == 5 ? loss : win;
            trades.Add(new NQG0RiskTradeV7(entry, entry.AddMinutes(3),
                net, mae, mfe));
        }
        return trades;
    }

    private static double Net(IList<NQG0RiskTradeV7> trades)
    {
        double total = 0;
        foreach (var t in trades) total += t.NetProfitUSD;
        return total;
    }

    public static void Main()
    {
        var good = Sample(100, -50, 10, 40);
        var losing = Sample(-20, -40, 20, 5);
        var risky = Sample(100, -50, 3500, 4000);
        var sparse = Sample(100, -50, 10, 40, true);
        NQDiscoveryResultV9 g = NQNativeDiscoveryScoreV9.Evaluate(good, Net(good));
        NQDiscoveryResultV9 l = NQNativeDiscoveryScoreV9.Evaluate(losing, Net(losing));
        NQDiscoveryResultV9 r = NQNativeDiscoveryScoreV9.Evaluate(risky, Net(risky));
        NQDiscoveryResultV9 s = NQNativeDiscoveryScoreV9.Evaluate(sparse, Net(sparse));
        Check(g.Valid && l.Valid && r.Valid && s.Valid, "valid candidate");
        Check(g.Trades == 180 && g.MonthsBelowFive == 0 && g.PositiveYears == 3,
            "full 36-month sample and annual sign");
        Check(g.Score > l.Score, "profitable ranks over losing");
        Check(g.Score > r.Score, "risk stress penalized");
        Check(!r.HardG0Pass, "extreme MAE is not approved");
        Check(!s.HardG0Pass && s.MonthsBelowFive == 36, "sparse candidate rejected by hard gate");
        Check(s.Score > NQNativeDiscoveryScoreV9.InvalidScore, "valid sparse receives soft finite rank");
        Check(!NQNativeDiscoveryScoreV9.Evaluate(null, 0).Valid, "null invalid");
        Check(!NQNativeDiscoveryScoreV9.Evaluate(new List<NQG0RiskTradeV7>(), 0).Valid,
            "zero-trade invalid");
        Check(!NQNativeDiscoveryScoreV9.Evaluate(good, Net(good) + 5).Valid,
            "PnL mismatch fails closed");
        Console.WriteLine("NQ_S069_DISCOVERY_V9_TESTS_PASS=10");
    }
}
