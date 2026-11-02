// S0.64 - G0 provisional economic gate for V5 research, pure C#.
// No NinjaTrader dependencies: the EXACT decision is executable in CI.
// Closed-trade equity drawdown only. MFFU trailing/intrabar DD needs later audit.
// Full 36-calendar-month sample 2020-01..2022-12; zero-trade months FAIL.
using System;
using System.Collections.Generic;

namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQG0TradeV6
    {
        public DateTime EntryTime { get; private set; }
        public DateTime ExitTime { get; private set; }
        public double NetProfitUSD { get; private set; }
        public NQG0TradeV6(DateTime entryTime, DateTime exitTime, double netProfitUSD)
        {
            EntryTime=entryTime; ExitTime=exitTime; NetProfitUSD=netProfitUSD;
        }
    }

    public sealed class NQG0ResultV6
    {
        public bool Pass { get; internal set; }
        public string Failure { get; internal set; }
        public int Trades { get; internal set; }
        public double NetProfitUSD { get; internal set; }
        public double ProfitFactor { get; internal set; }
        public double GrossProfitUSD { get; internal set; }
        public double GrossLossUSD { get; internal set; }
        public double ClosedMaxDrawdownUSD { get; internal set; }
        public double WorstTradeUSD { get; internal set; }
        public int MonthsBelowFive { get; internal set; }
        public int[] MonthlyCounts { get; internal set; }
    }

    public static class NQNativeG0RulesV6
    {
        public const int MinTrades=150;
        public const double MinProfitFactor=1.25;
        public const double MaxClosedDrawdownUSD=2000.0;
        public const int MinTradesPerCalendarMonth=5;
        public const double RejectScore=-1.0e12;
        public static readonly DateTime SampleBegin=new DateTime(2020,1,1);
        public static readonly DateTime SampleEndExclusive=new DateTime(2023,1,1);

        private static bool Finite(double x)
        {
            return !double.IsNaN(x) && !double.IsInfinity(x);
        }
        private static NQG0ResultV6 Fail(NQG0ResultV6 r,string cause)
        {
            r.Pass=false;r.Failure=cause;return r;
        }
        public static NQG0ResultV6 Evaluate(IList<NQG0TradeV6> trades,
                                              double nativeNetProfitUSD)
        {
            var r=new NQG0ResultV6{ MonthlyCounts=new int[36] };
            if(trades==null || !Finite(nativeNetProfitUSD))
                return Fail(r,"INVALID_INPUT");
            r.Trades=trades.Count;
            double equity=0.0,peak=0.0,maxDD=0.0,win=0.0,loss=0.0;
            double worst=0.0;
            DateTime priorExit=DateTime.MinValue;
            for(int i=0;i<trades.Count;i++)
            {
                var trade=trades[i];
                if(trade==null || !Finite(trade.NetProfitUSD) ||
                   trade.EntryTime<SampleBegin ||
                   trade.EntryTime>=SampleEndExclusive ||
                   trade.ExitTime<trade.EntryTime ||
                   trade.ExitTime>=SampleEndExclusive ||
                   trade.ExitTime<priorExit)
                    return Fail(r,"INVALID_TRADE_OR_UNSORTED_EXIT");
                priorExit=trade.ExitTime;
                // Entry month for the user's >=5 entries per month requirement.
                int month=(trade.EntryTime.Year-2020)*12+
                          trade.EntryTime.Month-1;
                if(month<0||month>=36)
                    return Fail(r,"OUTSIDE_IST_MONTH");
                r.MonthlyCounts[month]++;
                double p=trade.NetProfitUSD;
                if(p>0.0)win+=p;
                if(p<0.0)loss+=p;
                if(p<worst)worst=p;
                equity+=p;
                if(equity>peak)peak=equity;
                double dd=peak-equity;
                if(dd>maxDD)maxDD=dd;
            }
            r.NetProfitUSD=equity;
            r.GrossProfitUSD=win;
            r.GrossLossUSD=loss;
            r.ClosedMaxDrawdownUSD=maxDD;
            r.ProfitFactor=loss<0.0?win/-loss:0.0;
            r.WorstTradeUSD=worst;
            foreach(int n in r.MonthlyCounts)
                if(n<MinTradesPerCalendarMonth)r.MonthsBelowFive++;

            // Fail-closed: costs or PnL source must reconcile to NinjaTrader
            // NetProfit. Do not silently mix gross and net trade results.
            if(Math.Abs(nativeNetProfitUSD-equity)>0.03)
                return Fail(r,"PNL_MISMATCH_NATIVE_VS_TRADE_HISTORY");
            if(r.Trades<MinTrades)
                return Fail(r,"INSUFFICIENT_TRADES");
            if(r.MonthsBelowFive>0)
                return Fail(r,"MONTHLY_FREQUENCY");
            if(r.NetProfitUSD<=0.0)
                return Fail(r,"NEGATIVE_NET");
            if(!Finite(r.ProfitFactor) || r.ProfitFactor<MinProfitFactor)
                return Fail(r,"LOW_PROFIT_FACTOR");
            if(r.ClosedMaxDrawdownUSD>MaxClosedDrawdownUSD)
                return Fail(r,"EXCESS_CLOSED_DRAWDOWN");
            r.Pass=true;r.Failure="PASS_PROVISIONAL_CLOSED_EQUITY";
            return r;
        }
    }
}
