// S0.66 tests exercising EXACT production G0 V6 + V7 C# decisions.
using System;
using System.Collections.Generic;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;

internal static class Program
{
    static int check;
    static void T(bool x,string w)
    {check++;if(!x)throw new Exception("S0.66 G0 V7 QA FAIL "+w);}
    static List<NQG0RiskTradeV7> Good()
    {
        var t=new List<NQG0RiskTradeV7>();
        for(int y=2020;y<=2022;y++)
            for(int m=1;m<=12;m++)
                for(int k=0;k<5;k++)
                {
                    var dt=new DateTime(y,m,1,9,50,0).AddMinutes(k*3);
                    t.Add(new NQG0RiskTradeV7(
                        dt,dt.AddMinutes(1), k==4?-25:25,20,5));
                }
        return t;
    }
    static double Net(IEnumerable<NQG0RiskTradeV7> t)
    {return t.Sum(x=>x.NetProfitUSD);}
    static List<NQG0RiskTradeV7> Swap(
      List<NQG0RiskTradeV7> t,int i,
      double? net=null,double? mae=null,double? mfe=null)
    {
        var a=new List<NQG0RiskTradeV7>(t);
        var q=a[i];
        a[i]=new NQG0RiskTradeV7(q.EntryTime,q.ExitTime,
            net??q.NetProfitUSD,mae??q.MaeCurrency,mfe??q.MfeCurrency);
        return a;
    }
    static void Flag(NQG0DiagnosticsResultV7 r,string flag)
    {T(r.AllFailures.Contains(flag),"requires "+flag);}
    static void NoFlag(NQG0DiagnosticsResultV7 r,string flag)
    {T(!r.AllFailures.Contains(flag),"excludes "+flag);}
    public static int Main()
    {
        var good=Good();T(good.Count==180,"180 IST entries");
        var ok=NQNativeG0DiagnosticsV7.Evaluate(good,Net(good));
        T(ok.Valid&&ok.Pass,"test baseline passes");
        T(ok.FirstV6Failure=="PASS_PROVISIONAL_CLOSED_EQUITY",
          "V6 baseline retained");
        T(ok.AllFailures.Length==0,"no false rejects");
        T(ok.Economic.Trades==180&&ok.Economic.MonthsBelowFive==0,"36 months");
        T(ok.Economic.ProfitFactor>=1.25 && 
          ok.Economic.ClosedMaxDrawdownUSD<=2000,"base G0 conditions");
        T(ok.MaeMfeStressDrawdownUSD>=ok.Economic.ClosedMaxDrawdownUSD,
          "stress includes closed DD");

        var risk=Swap(good,0,null,2200,100);
        var a=NQNativeG0DiagnosticsV7.Evaluate(risk,Net(risk));
        T(a.Valid&&!a.Pass,"risk stress rejects eligible base");
        Flag(a,"EXCESS_M1_MAE_MFE_STRESS_DD");
        NoFlag(a,"EXCESS_CLOSED_DRAWDOWN");
        T(a.Economic.Pass,"V6 would pass and V7 rejects");
        T(a.MaeMfeStressDrawdownUSD>2000,"stress metric over limit");

        var noFeeMatch=NQNativeG0DiagnosticsV7.Evaluate(good,Net(good)+0.50);
        T(!noFeeMatch.Valid,"native mismatch fail closed");
        Flag(noFeeMatch,"PNL_MISMATCH_NATIVE_VS_TRADE_HISTORY");

        var multi=Swap(good,0,-100,5500,1500);
        multi.RemoveAt(1);
        var m=NQNativeG0DiagnosticsV7.Evaluate(multi,Net(multi));
        T(m.Valid&&!m.Pass,"multiple signals");
        Flag(m,"MONTHLY_FREQUENCY");
        Flag(m,"LOW_PROFIT_FACTOR");
        Flag(m,"EXCESS_M1_MAE_MFE_STRESS_DD");
        NoFlag(m,"NEGATIVE_NET");
        T(m.AllFailures.Length>=3,"all reasons retained");

        var allLose=new List<NQG0RiskTradeV7>();
        foreach(var t in good)
            allLose.Add(new NQG0RiskTradeV7(t.EntryTime,t.ExitTime,
                                  -5,5,0));
        var lose=NQNativeG0DiagnosticsV7.Evaluate(allLose,Net(allLose));
        Flag(lose,"NEGATIVE_NET");Flag(lose,"LOW_PROFIT_FACTOR");
        T(!lose.Pass,"negative net and PF not pass");

        var tooFew=good.GetRange(0,100);
        var few=NQNativeG0DiagnosticsV7.Evaluate(tooFew,Net(tooFew));
        Flag(few,"INSUFFICIENT_TRADES");
        Flag(few,"MONTHLY_FREQUENCY");
        T(few.Economic.MonthsBelowFive==16,"missing calendar months count");

        var highClosed=new List<NQG0RiskTradeV7>();
        foreach(var t in good)
            highClosed.Add(new NQG0RiskTradeV7(t.EntryTime,t.ExitTime,
                              t.NetProfitUSD,20,5));
        highClosed=Swap(highClosed,50,-2100,2100,5);
        var dd=NQNativeG0DiagnosticsV7.Evaluate(highClosed,Net(highClosed));
        Flag(dd,"EXCESS_CLOSED_DRAWDOWN");
        Flag(dd,"EXCESS_M1_MAE_MFE_STRESS_DD");

        var badMae=Swap(good,0,null,-1,null);
        Flag(NQNativeG0DiagnosticsV7.Evaluate(badMae,Net(badMae)),
             "INVALID_MAE_MFE");
        var nanMfe=Swap(good,0,null,null,double.NaN);
        Flag(NQNativeG0DiagnosticsV7.Evaluate(nanMfe,Net(nanMfe)),
             "INVALID_MAE_MFE");
        var infMae=Swap(good,0,null,double.PositiveInfinity,null);
        Flag(NQNativeG0DiagnosticsV7.Evaluate(infMae,Net(infMae)),
             "INVALID_MAE_MFE");

        T(NQNativeG0DiagnosticsV7.Evaluate(null,0).AllFailures[0] ==
             "INVALID_INPUT","null rejected");
        T(NQNativeG0DiagnosticsV7.Evaluate(good,double.NaN).AllFailures[0] ==
             "INVALID_INPUT","NaN native net rejected");

        // MAE/MFE proxy is NOT a true chronological tick reconstruction.
        // Check a case where a single trade's MFE then MAE stress dominates
        // although neither realized PnL nor closed-equity drawdown is large.
        var peakFirst=Swap(good,0,null,1200,1200);
        var path=NQNativeG0DiagnosticsV7.Evaluate(peakFirst,Net(peakFirst));
        Flag(path,"EXCESS_M1_MAE_MFE_STRESS_DD");
        T(path.MaeMfeStressDrawdownUSD>=2400,"MFE-before-MAE stress assumption");

        // Determinism and no hidden state across repeated candidates.
        for(int k=0;k<100;k++)
        {
            var z=NQNativeG0DiagnosticsV7.Evaluate(good,Net(good));
            T(z.Pass&&Math.Abs(z.MaeMfeStressDrawdownUSD-
                    ok.MaeMfeStressDrawdownUSD)<1e-8,"repeat deterministic");
        }
        Console.WriteLine("NQ_S066_G0_V7_CPPURE_QA_PASS="+check);
        Console.WriteLine("M1_MAE_MFE_STRESS_PROXY_NOT_TICK_LEVEL_OR_FUNDED_DD");
        return 0;
    }
}
