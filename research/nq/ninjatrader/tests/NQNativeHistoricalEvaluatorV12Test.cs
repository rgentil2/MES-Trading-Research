// Conservative M1 historical evaluator contract tests — synthetic bars ONLY.
// Validates trade timing, costs, dual-hit adverse exits, research years, no
// future-bar use and V9/V7 score aggregation. No claim of native NT8 parity.
using System;
using System.Collections.Generic;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;
internal static class V12OfflineM1Test
{
    private static void Check(bool x,string msg)
    {if(!x)throw new Exception("V12_M1_FAIL "+msg);}
    private static int[] Genes(int direction=1)
    {
        return new[]{
            1,0,6,44,12,77,12,121,12,
            0,0,0,direction<0?1:0,
            20,32,2,0,14,15,25
        };
    }
    private static List<NQTimedBarV12> Day(int year=2021,
        double trend=0.75,bool ambiguous=false,int n=130)
    {
        var bars=new List<NQTimedBarV12>();
        var begin=new DateTime(year,6,1,9,30,0);
        double p=15000;
        for(int i=0;i<n;i++)
        {
            double o=p;
            p+=trend;
            double hi=Math.Max(o,p)+0.25;
            double lo=Math.Min(o,p)-0.25;
            if(ambiguous&&i==40)
            {hi=o+20;lo=o-20;}
            bars.Add(new NQTimedBarV12(begin.AddMinutes(i),
                new NQBarV11(o,hi,lo,p,500)));
        }
        return bars;
    }

    private static bool SameTrades(NQHistoricalResultV12 a,
                                   NQHistoricalResultV12 b)
    {
        return a.Trades.Count==b.Trades.Count &&
            a.Trades.Zip(b.Trades,(x,y)=>
                x.EntryTime==y.EntryTime&&x.ExitTime==y.ExitTime&&
                Math.Abs(x.NetProfitUSD-y.NetProfitUSD)<1e-8).All(x=>x);
    }

    public static int Main()
    {
        int[] g=Genes();
        var data=Day();
        var win=NQNativeHistoricalEvaluatorV12.Evaluate(data,g);
        Check(win.Valid&&win.Reason=="ESTIMATE_ONLY","valid synthetic in-sample data");
        Check(win.Trades.Count==2,"two profitable trades, daily capped");
        Check(win.TargetFills==2 && win.StopFills==0,
            "both exits must be limit targets");
        Check(win.Trades.All(x=>x.EntryTime>=new DateTime(2021,6,1,10,10,0)),
            "no entry before 40 completed RTH warmup bars");
        Check(win.Trades.All(x=>Math.Abs(x.NetProfitUSD-155.32)<0.01),
            "target price, market entry slip and $4.68 roundtrip fee");
        Check(win.Discovery!=null && win.Discovery.Valid,
            "use existing V9 discovery economics on 2021 trades");
        Check(win.Score==win.Discovery.Score,
            "actual V9 score returned, not synthetic optimization proxy");
        Check(win.SignalCount==2,"signal submissions counted");
        Check(win.DailyBlocked>0,"per-day gate blocks further signals");
        var shorter=NQNativeHistoricalEvaluatorV12.Evaluate(
            data.Take(125).ToList(),g);
        Check(shorter.Valid && SameTrades(win,shorter),
            "later bars cannot change already closed trades");

        var both=NQNativeHistoricalEvaluatorV12.Evaluate(
            Day(2021,0.75,true),g);
        Check(both.Valid&&both.AmbiguousStops>=1&&both.StopFills>=1,
            "when both touched in a minute, stop wins");
        Check(both.Trades[0].NetProfitUSD<0,
            "ambiguous high/low bar cannot claim optimistic target");

        var flat=Genes();flat[14]=0;flat[15]=1;
        var time=NQNativeHistoricalEvaluatorV12.Evaluate(Day(),flat);
        Check(time.Valid&&time.TimeFills==1&&time.Trades.Count==1,
            "no-target position flattened 11:29 following 11:28 submit");
        Check(time.Trades[0].ExitTime.Hour==11&&
              time.Trades[0].ExitTime.Minute==29,
            "flat execution timestamp at next bar open");

        var bear=NQNativeHistoricalEvaluatorV12.Evaluate(
            Day(2021,-0.75),Genes());
        Check(bear.Valid&&bear.Trades.Count==2&&
            bear.Trades.All(t=>t.NetProfitUSD>0),
            "symmetrical bearish signal and short fills");

        var leak=Day();
        leak.AddRange(Day(2023).Take(1));
        var future=NQNativeHistoricalEvaluatorV12.Evaluate(leak,g);
        Check(!future.Valid&&future.Score==-1e12,
            "reject any held-out 2023+ data");
        var incomplete=Genes();incomplete[14]=0;incomplete[15]=1;
        var stopped=NQNativeHistoricalEvaluatorV12.Evaluate(
            Day(2021,0.75,false,65),incomplete);
        Check(!stopped.Valid&&stopped.Reason=="MISSING_LAST_EXIT_OR_ENTRY_BAR",
            "never silently carry an unclosed position overnight");
        Check(!NQNativeHistoricalEvaluatorV12.Evaluate(null,g).Valid,
            "null source rejected");
        var wrong=(int[])g.Clone();wrong[1]=132;
        Check(!NQNativeHistoricalEvaluatorV12.Evaluate(data,wrong).Valid,
            "unknown condition rejected");
        var wrongOrder=Day();
        var swap=wrongOrder[4];wrongOrder[4]=wrongOrder[5];
        wrongOrder[5]=swap;
        Check(!NQNativeHistoricalEvaluatorV12.Evaluate(wrongOrder,g).Valid,
            "unordered bar timestamps rejected");

        Console.WriteLine("NQ_V12_OFFLINE_M1_PASS trades="+win.Trades.Count+
            " net="+win.Net.ToString("F2")+
            " target="+win.TargetFills+
            " stopAmbiguity="+both.AmbiguousStops+
            " timedExit="+time.TimeFills+
            " V9_SYNTHETIC_TRADE_SCORE="+win.Score.ToString("F2"));
        Console.WriteLine("M1_FILL_ESTIMATE_ONLY_NOT_NINJATRADER_PARITY_NO_REAL_NQ_DATA");
        return 0;
    }
}
