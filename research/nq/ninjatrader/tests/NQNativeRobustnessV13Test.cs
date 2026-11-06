// V13 robustness deterministic unit tests use SYNTHETIC CLOSED TRADES.
using System;
using System.Collections.Generic;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;
internal static class V13RobustnessQA
{
    private static void Check(bool x,string reason)
    {if(!x)throw new Exception("V13_ROBUST_FAIL "+reason);}
    private static List<NQG0RiskTradeV7> Trades(double win,double loss,
                                                 int winsPerMonth=8)
    {
        var trades=new List<NQG0RiskTradeV7>();
        for(int yr=2020;yr<=2022;yr++)
            for(int mo=1;mo<=12;mo++)
                for(int i=0;i<10;i++)
                {
                    var entry=new DateTime(yr,mo,1,10,0,0).AddDays(i);
                    double p=i<winsPerMonth?win:loss;
                    trades.Add(new NQG0RiskTradeV7(entry,
                        entry.AddMinutes(30),p,Math.Abs(Math.Min(0,p)),
                        Math.Max(0,p)));
                }
        return trades;
    }
    public static int Main()
    {
        var all=Trades(60,-100);
        var cfg=new NQRobustnessConfigV13{
            BootstrapPaths=2000,BlockLengthTrades=8,Seed=20261105,
            BaseAllInCostPerTradeUSD=24.68,CostMultiplier=1.5,
            MaxBootstrapP95ClosedDDUSD=2000
        };
        var a=NQNativeRobustnessV13.Evaluate(all,cfg);
        var b=NQNativeRobustnessV13.Evaluate(all,cfg);
        Check(a.Valid&&a.ProvisionalG0Pass,"V7 financial gates pass fixture");
        Check(a.Trades==360&&a.BootstrapPaths==2000,"sample size");
        Check(a.HistoricalNetUSD>0&&a.CostStressNetUSD>0,
            "positive historical and 1.5x stressed costs");
        Check(Math.Abs(a.CostStressNetUSD-
            (a.HistoricalNetUSD-360*12.34))<0.05,
            "1.5x all-in cost formula");
        Check(a.BootstrapP95ClosedDrawdownUSD>=0,
            "bootstrap percentile drawdown nonnegative");
        Check(a.BootstrapP95ClosedDrawdownUSD==
            b.BootstrapP95ClosedDrawdownUSD &&
            a.BootstrapP05NetUSD==b.BootstrapP05NetUSD,
            "seed gives deterministic percentiles");
        Check(a.ProbabilityBootstrapNetNegative>=0&&
            a.ProbabilityBootstrapNetNegative<=1,
            "probability normalized");
        var weak=NQNativeRobustnessV13.Evaluate(
            Trades(15,-70,3),cfg);
        Check(weak.Valid&&!weak.ProvisionalG0Pass&&
            !weak.ProvisionalRobustPass,
            "failed V7 cannot pass robustness even if resampled");
        var sparse=NQNativeRobustnessV13.Evaluate(
            all.Take(120).ToList(),cfg);
        Check(sparse.Valid&&!sparse.ProvisionalG0Pass,
            "incomplete 2020-22 months fail V7 G0");
        var oos=Trades(60,-100);
        oos.Add(new NQG0RiskTradeV7(new DateTime(2023,1,4,10,0,0),
            new DateTime(2023,1,4,10,15,0),50,10,55));
        Check(!NQNativeRobustnessV13.Evaluate(oos,cfg).Valid,
            "held-out year cannot be used for risk tuning");
        var highCost=new NQRobustnessConfigV13{
            BootstrapPaths=2000,BlockLengthTrades=8,Seed=20261105,
            BaseAllInCostPerTradeUSD=200,CostMultiplier=1.5
        };
        var stress=NQNativeRobustnessV13.Evaluate(all,highCost);
        Check(stress.Valid&&!stress.CostStressPositive&&
            !stress.ProvisionalRobustPass,
            "negative stressed costs fail closed");
        Console.WriteLine("NQ_V13_BOOTSTRAP_PASS count="+a.Trades+
            " histNet="+a.HistoricalNetUSD.ToString("F2")+
            " cost15Net="+a.CostStressNetUSD.ToString("F2")+
            " p95DD="+a.BootstrapP95ClosedDrawdownUSD.ToString("F2")+
            " lossProbability="+a.ProbabilityBootstrapNetNegative.ToString("F3"));
        Console.WriteLine("SYNTHETIC_TRADES_ONLY_NOT_ACCOUNT_TRAILING_DD_OR_OOS");
        return 0;
    }
}
