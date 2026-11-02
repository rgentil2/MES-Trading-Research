// S0.64 standalone tests for PRODUCTION G0 code; run by .NET8 GitHub Actions.
using System;
using System.Collections.Generic;
using NinjaTrader.NinjaScript.Strategies;
internal static class Program
{
    static int assertions;
    static void T(bool b,string s)
    { assertions++;if(!b) throw new Exception("G0 FAILED: "+s); }
    static List<NQG0TradeV6> Synthetic(double winner,double loser)
    {
        var t=new List<NQG0TradeV6>();
        for(int y=2020;y<=2022;y++)
          for(int m=1;m<=12;m++)
            for(int j=0;j<5;j++)
            {
                DateTime when=new DateTime(y,m,1,9,50,0).AddMinutes(j*2);
                double pnl=j==4?loser:winner;
                t.Add(new NQG0TradeV6(when,when.AddMinutes(1),pnl));
            }
        return t;
    }
    static double Sum(List<NQG0TradeV6> t)
    {
        double z=0;foreach(var q in t)z+=q.NetProfitUSD;return z;
    }
    public static int Main()
    {
        var good=Synthetic(25,-25);
        var r=NQNativeG0RulesV6.Evaluate(good,Sum(good));
        T(r.Pass,"180-entry sample must pass");
        T(r.Trades==180,"must have 180 trades");
        T(r.MonthsBelowFive==0,"monthly all pass");
        T(Math.Abs(r.NetProfitUSD-2700)<0.01,"net calculation");
        T(Math.Abs(r.ProfitFactor-4.0)<0.00001,"PF calculation");
        T(Math.Abs(r.ClosedMaxDrawdownUSD-25)<0.00001,"closed peak-trough");
        T(r.Failure=="PASS_PROVISIONAL_CLOSED_EQUITY","pass annotation");

        var neg=Synthetic(5,-25);
        T(NQNativeG0RulesV6.Evaluate(neg,Sum(neg)).Failure=="NEGATIVE_NET","net fail");

        var lowPf=Synthetic(27,-100);
        var low=NQNativeG0RulesV6.Evaluate(lowPf,Sum(lowPf));
        T(low.Failure=="LOW_PROFIT_FACTOR","PF 1.08 fail");
        T(low.ProfitFactor>1&&low.ProfitFactor<1.25,"PF boundary");

        var dd=Synthetic(800,-2400);
        var d=NQNativeG0RulesV6.Evaluate(dd,Sum(dd));
        T(d.Failure=="EXCESS_CLOSED_DRAWDOWN","DD 2400 fail");
        T(d.ClosedMaxDrawdownUSD>2000 && d.ProfitFactor>1.25,
          "isolate DD gate");

        var month=good.GetRange(0,good.Count);
        month.RemoveAt(0);
        var m=NQNativeG0RulesV6.Evaluate(month,Sum(month));
        T(m.Failure=="MONTHLY_FREQUENCY","missing 1 trade monthly gate");
        T(m.MonthsBelowFive==1,"exactly one weak month");
        T(m.Trades==179,"still more than 150 trades");

        var tiny=good.GetRange(0,100);
        T(NQNativeG0RulesV6.Evaluate(tiny,Sum(tiny)).Failure=="INSUFFICIENT_TRADES",
          "under 150 trades");

        T(NQNativeG0RulesV6.Evaluate(good,Sum(good)+1).Failure==
          "PNL_MISMATCH_NATIVE_VS_TRADE_HISTORY","gross/net mismatch fail");

        var outside=good.GetRange(0,good.Count);
        outside[0]=new NQG0TradeV6(new DateTime(2023,1,1,9,50,0),
                                    new DateTime(2023,1,1,9,51,0),25);
        T(NQNativeG0RulesV6.Evaluate(outside,Sum(outside)).Failure==
          "INVALID_TRADE_OR_UNSORTED_EXIT","holdout blocked");

        var unsorted=good.GetRange(0,good.Count);
        unsorted[2]=new NQG0TradeV6(
          new DateTime(2020,1,1,9,50,0),new DateTime(2020,1,1,9,51,0),25);
        T(NQNativeG0RulesV6.Evaluate(unsorted,Sum(unsorted)).Failure==
          "INVALID_TRADE_OR_UNSORTED_EXIT","nonchronological blocked");

        T(NQNativeG0RulesV6.Evaluate(null,0).Failure=="INVALID_INPUT",
          "null fail");
        T(NQNativeG0RulesV6.Evaluate(good,double.NaN).Failure=="INVALID_INPUT",
          "NaN fail");

        // Four supplied real candidate outcomes: can never pass G0.
        // S0.63 best candidates all PF <1.25, except even that isn't enough.
        foreach(var pf in new[]{1.06,1.04,1.01,1.11})
            T(pf<NQNativeG0RulesV6.MinProfitFactor,"4 real PF fail");

        Console.WriteLine("NQ_S064_G0_CPPURE_RULES_QA_PASS="+assertions);
        return 0;
    }
}
