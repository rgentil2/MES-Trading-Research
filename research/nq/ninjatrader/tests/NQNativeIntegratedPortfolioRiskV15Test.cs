// S0.75 synthetic end-to-end V13 diversification -> V15 chronology.
// A portfolio that looks profitable on closed trades MUST still fail
// if its original M1 bars reveal simultaneous adverse floating exposure.
using System;
using System.Collections.Generic;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;
internal static class V15IntegratedPortfolioTest
{
    private static void A(bool yes,string why)
    {if(!yes)throw new Exception("NQ_V15_PORTFOLIO_FAIL "+why);}

    private static List<NQTimedBarV12> Bars(bool adverseShock=false)
    {
        var source=new List<NQTimedBarV12>();
        for(int year=2020;year<=2022;year++)
            for(int month=1;month<=12;month++)
                for(int day=1;day<=10;day++)
                {
                    DateTime date=new DateTime(year,month,day,9,30,0);
                    for(int minute=0;minute<11;minute++)
                    {
                        double high=1005,low=995;
                        if(adverseShock && year==2020 &&
                            month==1 && day==1 && minute==4)
                            low=30;
                        source.Add(new NQTimedBarV12(
                            date.AddMinutes(minute),
                            new NQBarV11(1000,high,low,1000,250)));
                    }
                }
        return source;
    }

    private static NQPortfolioExecutionCandidateV15 Candidate(
        string id,int family)
    {
        var trades=new List<NQG0RiskTradeV7>();
        var fills=new List<NQExecutionFillV12>();
        for(int year=2020;year<=2022;year++)
            for(int month=1;month<=12;month++)
            {
                int m=(year-2020)*12+month-1;
                double wave=family==0?Math.Sin(m*0.7):
                    family==1?Math.Cos(m*1.1):
                    Math.Sin(m*1.7+0.4);
                for(int day=1;day<=10;day++)
                {
                    var start=new DateTime(year,month,day,9,31,0);
                    var end=new DateTime(year,month,day,9,36,0);
                    double p=day<=8?65+8*wave:-100;
                    double exit=1000+(p+4.68)/20.0;
                    trades.Add(new NQG0RiskTradeV7(
                        start,end,p,Math.Max(0,-p),Math.Max(0,p)));
                    fills.Add(new NQExecutionFillV12(
                        start,end,1,1,1000,exit,4.68));
                }
            }
        return new NQPortfolioExecutionCandidateV15(
            id,trades,fills);
    }

    private static NQRobustnessConfigV13 Robust()
    {return new NQRobustnessConfigV13{
        BootstrapPaths=500,BlockLengthTrades=8,Seed=20261106,
        BaseAllInCostPerTradeUSD=24.68,CostMultiplier=1.5,
        MaxBootstrapP95ClosedDDUSD=2000
    };}
    private static NQPortfolioConfigV13 Portfolio()
    {return new NQPortfolioConfigV13{
        TargetStrategies=3,MaximumPositiveMonthlyCorrelation=0.45,
        MaximumClosedPortfolioDDUSD=2000,
        MaximumOverlappingMaeProxyUSD=1000,
        MaximumProfitConcentration=0.40
    };}

    public static int Main()
    {
        var a=Candidate("A",0);
        var b=Candidate("B",1);
        var c=Candidate("C",2);
        var inputs=new[]{a,b,c};
        var allBars=Bars();
        var result=NQNativeIntegratedPortfolioRiskV15.Evaluate(
            allBars,inputs,Robust(),Portfolio(),
            new NQChronologicalRiskConfigV15());
        A(result.Valid&&result.ProvisionalPass &&
            result.Reason=="V13_AND_V15_PROVISIONAL_PASS",
            "diverse synthetic closed + floating account pass: "+
            result.Reason+" risk="+
            (result.Chronology==null?"null":
                result.Chronology.MaxAdversarialM1StressDDUSD.ToString("F2")));
        A(result.Selection.Selected.Count==3 &&
          result.Chronology.FillCount==1080,
          "three components * 360 chronological closed fills each");
        A(Math.Abs(result.Selection.NetProfitUSD-
                result.Chronology.RealizedNetUSD)<0.03,
          "V13/V15 portfolio dollar economics reconciled");
        A(result.Chronology.MaxConcurrentContracts==3,
          "all three NQ positions open concurrently");

        // Same profitable closed trades, but an actual M1 price shock
        // while all three positions are open: V13 may still pass but
        // V15 MUST fail on float/trailing stress.
        var shock=NQNativeIntegratedPortfolioRiskV15.Evaluate(
            Bars(true),inputs,Robust(),Portfolio(),
            new NQChronologicalRiskConfigV15());
        A(shock.Valid&&shock.Selection.Valid &&
          !shock.ProvisionalPass &&
          shock.Reason=="V15_CHRONOLOGICAL_RISK_REJECT",
          "dangerous concurrent intrabar adverse risk rejected");
        A(shock.Chronology.MaxAdversarialM1StressDDUSD>2000,
          "$2k account stress breach detected despite good closed PnL");

        // Reject corrupt or inconsistent fill price ECONOMICS before
        // even attempting to select correlated portfolio strategies.
        var altered=new List<NQExecutionFillV12>(a.Executions);
        var first=altered[0];
        altered[0]=new NQExecutionFillV12(first.EntryTime,
            first.ExitTime,first.Side,1,first.EntryPrice,
            first.ExitPrice+2,first.RoundTripFeesUSD);
        var badInputs=new[]{
            new NQPortfolioExecutionCandidateV15("A",a.Trades,altered),b,c};
        var mismatch=NQNativeIntegratedPortfolioRiskV15.Evaluate(
            allBars,badInputs,Robust(),Portfolio(),
            new NQChronologicalRiskConfigV15());
        A(!mismatch.Valid &&
          mismatch.Reason=="EXECUTION_AND_TRADE_PNL_MISMATCH",
          "corrupted realized trade receipt fails closed");

        // Repeated same monthly strategy fails diversity gate.
        var clone=new NQPortfolioExecutionCandidateV15(
            "CLONE",a.Trades,a.Executions);
        var clones=NQNativeIntegratedPortfolioRiskV15.Evaluate(
            allBars,new[]{a,b,clone},Robust(),Portfolio(),
            new NQChronologicalRiskConfigV15());
        A(clones.Valid&&!clones.ProvisionalPass&&
          clones.Reason.StartsWith("V13_REJECT_"),
          "V13 rejection blocks V15 endorsement");

        Console.WriteLine("NQ_V15_INTEGRATED_PORTFOLIO_PASS "+
            "components="+result.Selection.Selected.Count+
            " fills="+result.Chronology.FillCount+
            " net="+result.Chronology.RealizedNetUSD.ToString("F2")+
            " maxConcurrent="+result.Chronology.MaxConcurrentContracts+
            " stressDD="+
            result.Chronology.MaxAdversarialM1StressDDUSD.ToString("F2")+
            " shockDD="+shock.Chronology.MaxAdversarialM1StressDDUSD.ToString("F2"));
        Console.WriteLine("SYNTHETIC_ONLY_V13_PLUS_V15_NOT_NT8_OR_MFFU_VALIDATED");
        return 0;
    }
}
