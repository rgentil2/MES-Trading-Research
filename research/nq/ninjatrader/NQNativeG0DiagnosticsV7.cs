// S0.66 — G0 V7 diagnostic and M1 MAE/MFE stress proxy. Pure C#.
// Independent of the NinjaTrader API; uses V6 G0 exact economics unchanged.
// MAE/MFE are historical bar-based excursions, not true tick-level chronology.
// Stress DD assumes favorable excursion may precede adverse excursion, and
// takes unrealized peaks into account ACROSS trades. It is NOT certified
// intrabar/trailing account DD or compliance with funded-account rules.
using System;
using System.Collections.Generic;
using System.Linq;

namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQG0RiskTradeV7
    {
        public DateTime EntryTime { get; private set; }
        public DateTime ExitTime { get; private set; }
        public double NetProfitUSD { get; private set; }
        public double MaeCurrency { get; private set; }
        public double MfeCurrency { get; private set; }

        public NQG0RiskTradeV7(DateTime entry, DateTime exit,
                                double netUSD, double maeUSD, double mfeUSD)
        {
            EntryTime=entry; ExitTime=exit;
            NetProfitUSD=netUSD; MaeCurrency=maeUSD; MfeCurrency=mfeUSD;
        }
    }

    public sealed class NQG0DiagnosticsResultV7
    {
        public bool Pass { get; internal set; }
        public bool Valid { get; internal set; }
        public string FirstV6Failure { get; internal set; }
        public string[] AllFailures { get; internal set; }
        public NQG0ResultV6 Economic { get; internal set; }
        public double MaeMfeStressDrawdownUSD { get; internal set; }
        public double WorstTradeMaeUSD { get; internal set; }
        public double MaxObservedMfeUSD { get; internal set; }
        public int MonthsBelowFive { get { return Economic==null ? 36 : Economic.MonthsBelowFive; } }
    }

    public static class NQNativeG0DiagnosticsV7
    {
        public const double MaxStressProxyDDUSD=2000.0;
        private static bool Finite(double x)
        { return !double.IsNaN(x) && !double.IsInfinity(x); }

        private static NQG0DiagnosticsResultV7 Bad(string reason)
        {
            return new NQG0DiagnosticsResultV7{
                Pass=false,Valid=false,FirstV6Failure=reason,
                AllFailures=new []{reason},
                MaeMfeStressDrawdownUSD=double.NaN
            };
        }

        public static NQG0DiagnosticsResultV7 Evaluate(
            IList<NQG0RiskTradeV7> trades,double nativeNetUSD)
        {
            if(trades==null || !Finite(nativeNetUSD))
                return Bad("INVALID_INPUT");
            var basic=new List<NQG0TradeV6>(trades.Count);
            foreach(var t in trades)
            {
                // MAE/MFE are expected nonnegative currency excursions from
                // the NinjaTrader Trade object. Do NOT silently treat
                // invalid/missing extrema as zero, which could pass risk.
                if(t==null || !Finite(t.MaeCurrency) || !Finite(t.MfeCurrency) ||
                   !Finite(t.NetProfitUSD) ||
                   t.MaeCurrency<0.0 || t.MfeCurrency<0.0)
                    return Bad("INVALID_MAE_MFE");
                basic.Add(new NQG0TradeV6(
                    t.EntryTime,t.ExitTime,t.NetProfitUSD));
            }
            var v6=NQNativeG0RulesV6.Evaluate(basic,nativeNetUSD);
            if(v6.Failure=="INVALID_TRADE_OR_UNSORTED_EXIT" ||
               v6.Failure=="INVALID_INPUT" ||
               v6.Failure=="OUTSIDE_IST_MONTH" ||
               v6.Failure=="PNL_MISMATCH_NATIVE_VS_TRADE_HISTORY")
            {
                var bad=Bad(v6.Failure);
                bad.Economic=v6;
                return bad;
            }

            // Currency marked-to-market *stress proxy*:
            // peak potential equity includes best bar-extrema MFE of every
            // prior open trade; trough includes worst MAE for current trade.
            // MFE may occur AFTER MAE in same minute; assuming reverse order
            // deliberately stress-tests but is NOT a chronological fill path.
            // V6 closed PnL is net of commissions, whereas MFE/MAE may not
            // include fees. Neither actual funded trailing DD nor exact
            // intrabar high/low sequencing can be inferred from minute bars.
            double equity=0.0,possiblePeak=0.0,stressDD=0.0;
            double worstMae=0.0,maxMfe=0.0;
            foreach(var t in trades)
            {
                possiblePeak=Math.Max(possiblePeak,equity+t.MfeCurrency);
                double potentialTrough=Math.Min(
                    equity-t.MaeCurrency, equity+t.NetProfitUSD);
                stressDD=Math.Max(stressDD,
                    Math.Max(0.0,possiblePeak-potentialTrough));
                worstMae=Math.Max(worstMae,t.MaeCurrency);
                maxMfe=Math.Max(maxMfe,t.MfeCurrency);
                equity+=t.NetProfitUSD;
                possiblePeak=Math.Max(possiblePeak,equity);
            }
            stressDD=Math.Max(stressDD,v6.ClosedMaxDrawdownUSD);
            if(!Finite(stressDD))
                return Bad("INVALID_STRESS_DRAW");
            var failures=new List<string>(6);
            if(v6.Trades<NQNativeG0RulesV6.MinTrades)
                failures.Add("INSUFFICIENT_TRADES");
            if(v6.MonthsBelowFive>0)
                failures.Add("MONTHLY_FREQUENCY");
            if(v6.NetProfitUSD<=0.0)
                failures.Add("NEGATIVE_NET");
            if(!Finite(v6.ProfitFactor) ||
               v6.ProfitFactor<NQNativeG0RulesV6.MinProfitFactor)
                failures.Add("LOW_PROFIT_FACTOR");
            if(v6.ClosedMaxDrawdownUSD>
                NQNativeG0RulesV6.MaxClosedDrawdownUSD)
                failures.Add("EXCESS_CLOSED_DRAWDOWN");
            if(stressDD>MaxStressProxyDDUSD)
                failures.Add("EXCESS_M1_MAE_MFE_STRESS_DD");

            // The V6 economics are authoritative for old gates; V7 adds
            // independent multiple-reason visibility and a conservative
            // additional M1 stress proxy. Reject on any gate failure.
            return new NQG0DiagnosticsResultV7 {
                Pass=failures.Count==0,
                Valid=true,
                FirstV6Failure=v6.Failure,
                Economic=v6,
                AllFailures=failures.ToArray(),
                MaeMfeStressDrawdownUSD=stressDD,
                WorstTradeMaeUSD=worstMae,
                MaxObservedMfeUSD=maxMfe
            };
        }
    }
}
