// S0.75: real chronological calculations on SYNTHETIC M1 bars / fill
// ledgers. Does NOT assert proprietary NT8 fill or MFFU rule parity.
using System;
using System.Collections.Generic;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;
internal static class V15ChronoTest
{
    static void A(bool yes,string msg)
    {if(!yes)throw new Exception("NQ_V15_CHRONO_FAIL "+msg);}
    static DateTime Start=new DateTime(2021,6,1,9,30,0);
    static List<NQTimedBarV12> Bars(bool shock=false)
    {
        var result=new List<NQTimedBarV12>();
        for(int i=0;i<120;i++)
        {
            double px=100+0.20*i;
            double hi=px+1,lo=px-1;
            if(shock&&i==7)
            {hi=px+2;lo=30;}
            result.Add(new NQTimedBarV12(Start.AddMinutes(i),
                new NQBarV11(px,hi,lo,px,100)));
        }
        return result;
    }
    static NQExecutionFillV12 F(int enter,int exit,int side,
                               double entry,double leave,double fee=4.68)
    {return new NQExecutionFillV12(Start.AddMinutes(enter),
        Start.AddMinutes(exit),side,1,entry,leave,fee);}
    public static int Main()
    {
        var config=new NQChronologicalRiskConfigV15();
        var a=F(5,11,1,100,105);
        var b=F(6,12,-1,102,101);
        var r=NQNativeChronologicalRiskV15.Evaluate(Bars(),
            new[]{a,b},config);
        A(r.Valid&&r.FillCount==2,"two fill ledger rows validated");
        A(Math.Abs(r.RealizedNetUSD-110.64)<1e-5,
          "realized account net includes 2 roundtrip fees");
        A(r.MaxConcurrentContracts==2,
          "overlapping simultaneous positions counted");
        A(r.Marks==120,"minute-close time series computed");
        A(r.MaxAdversarialM1StressDDUSD>=r.MaxM1CloseMarkedDDUSD,
          "adversarial minute stress not less than close mark drawdown");

        var overlapping=new[]{F(5,11,1,100,100),
                              F(6,12,1,100,100)};
        var shock=NQNativeChronologicalRiskV15.Evaluate(
            Bars(true),overlapping,config);
        A(shock.Valid&&!shock.ProvisionalPass,
            "big adverse minute rejects funded proxy");
        A(shock.AccountDDBreaches>=1&&shock.SessionPauseBreaches>=1,
            "both account stress $2k and daily $1k breached");
        A(shock.MaxConcurrentAdverseUSD>=2000,
            "two simultaneous positions add adverse NQ dollar exposure");

        var same=NQNativeChronologicalRiskV15.Evaluate(Bars(),
            new[]{F(7,7,1,100,101)},config);
        A(same.Valid&&same.MaxConcurrentContracts==0,
            "same minute entry+exit counts realized, never open at close");

        var missing=Bars();
        missing.RemoveAt(9);
        var bad=NQNativeChronologicalRiskV15.Evaluate(
            missing,new[]{a},config);
        A(!bad.Valid&&bad.Reason=="MISSING_INTRATRADE_MINUTE",
            "missing open-position minute fails closed");

        var broken=NQNativeChronologicalRiskV15.Evaluate(
            Bars(),new[]{F(5,11,2,100,105)},config);
        A(!broken.Valid&&broken.Reason=="INVALID_EXECUTION_LEDGER",
            "unknown direction fails closed");

        var oos=Bars();
        oos.Add(new NQTimedBarV12(new DateTime(2023,1,2,9,30,0),
            new NQBarV11(100,102,99,100,100)));
        A(!NQNativeChronologicalRiskV15.Evaluate(
            oos,new[]{a},config).Valid,
            "2023+ cannot contaminate development risk research");

        // Full research pipeline V12 -> detailed immutable fill ledger ->
        // V15 chronological risk. Verify the portfolio ledger sums match
        // the original V12 M1 economic result exactly (same fee model).
        var trending=new List<NQTimedBarV12>();
        double px=15000;
        for(int i=0;i<120;i++)
        {
            double open=px;px+=0.75;
            trending.Add(new NQTimedBarV12(Start.AddMinutes(i),
                new NQBarV11(open,Math.Max(open,px)+0.25,
                    Math.Min(open,px)-0.25,px,500)));
        }
        int[] genes={1,0,6,44,12,77,12,121,12,
            0,0,0,0,20,32,2,0,14,15,25};
        var original=NQNativeHistoricalEvaluatorV12.Evaluate(
            trending,genes);
        A(original.Valid&&original.Executed.Count==original.Trades.Count &&
          original.Executed.Count>0,
          "V12 produced one exact detailed row per closed trade");
        var fromStrategy=NQNativeChronologicalRiskV15.Evaluate(
            trending,original.Executed,config);
        A(fromStrategy.Valid&&
          Math.Abs(original.Net-fromStrategy.RealizedNetUSD)<1e-7,
          "V12 and V15 identical trade ledger realized economics");
        A(original.Executed.All(x=>x.Side==1 && x.Quantity==1),
          "V12 synthetic rising trend buys one contract");

        Console.WriteLine("NQ_V15_CHRONO_PASS marks="+r.Marks+
            " concurrent="+r.MaxConcurrentContracts+
            " ledgerNet="+r.RealizedNetUSD.ToString("F2")+
            " shockDD="+shock.MaxAdversarialM1StressDDUSD.ToString("F2")+
            " shockDaily="+shock.MaxSessionPeakToTroughUSD.ToString("F2")+
            " V12V15FillCount="+original.Executed.Count);
        Console.WriteLine("BAR_CLOSE_AND_ADVERSE_EXTREMA_PROXY_NOT_NT8_OR_MFFU");
        return 0;
    }
}
