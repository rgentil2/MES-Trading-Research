// V13 portfolio selection on synthetic 2020–22 36-month trade streams.
// Never uses 2023+ market data. Correlation is monthly realized PnL,
// not claims of causality or true intrabar simultaneous account risk.
using System;
using System.Collections.Generic;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;
internal static class V13PortfolioQA
{
    private static void Check(bool ok,string reason)
    {if(!ok)throw new Exception("V13_PORTFOLIO_FAIL "+reason);}

    private static List<NQG0RiskTradeV7> Strategy(int family,
                                                  double scale=1)
    {
        var r=new List<NQG0RiskTradeV7>();
        for(int yr=2020;yr<=2022;yr++)
            for(int mo=1;mo<=12;mo++)
            {
                int index=(yr-2020)*12+mo-1;
                double wave=family==0?Math.Sin(index*0.7):
                    family==1?Math.Cos(index*1.1):
                    Math.Sin(index*1.7+0.4);
                for(int i=0;i<10;i++)
                {
                    DateTime t=new DateTime(yr,mo,1,10,0,0).AddDays(i);
                    double pnl=i<8?(65+8*wave)*scale:-100*scale;
                    r.Add(new NQG0RiskTradeV7(t,t.AddMinutes(35),
                        pnl,Math.Max(0,-pnl),Math.Max(0,pnl)));
                }
            }
        return r;
    }

    private static NQRobustnessConfigV13 Robust()
    {return new NQRobustnessConfigV13{
        BootstrapPaths=500,BlockLengthTrades=8,Seed=20261105,
        BaseAllInCostPerTradeUSD=24.68,CostMultiplier=1.5,
        MaxBootstrapP95ClosedDDUSD=2000
    };}

    public static int Main()
    {
        var a=new NQPortfolioCandidateV13("A",Strategy(0));
        var b=new NQPortfolioCandidateV13("B",Strategy(1));
        var c=new NQPortfolioCandidateV13("C",Strategy(2));
        var d=new NQPortfolioCandidateV13("D_DUP_A",Strategy(0));
        var p=new NQPortfolioConfigV13{
            TargetStrategies=3,
            MaximumPositiveMonthlyCorrelation=0.45,
            MaximumClosedPortfolioDDUSD=2000,
            MaximumOverlappingMaeProxyUSD=1000,
            MaximumProfitConcentration=0.40
        };
        var result=NQNativePortfolioV13.Select(
            new[]{a,b,c,d},Robust(),p);
        Check(result.Valid,"three diverse 2020-22 candidates accepted: "+
            result.Reason+" selected="+String.Join(",",
                result.Selected.Select(x=>x.Id)));
        Check(result.Selected.Count==3,"target 3 candidates");
        Check(result.Selected.All(x=>x.Id=="A"||x.Id=="B"||
            x.Id=="C"||x.Id=="D_DUP_A"),"only supplied IDs");
        Check(!(result.Selected.Any(x=>x.Id=="A")&&
                result.Selected.Any(x=>x.Id=="D_DUP_A")),
            "identical monthly PnL may not coexist");
        Check(result.WorstPairwiseMonthlyCorrelation<=0.45,
            "max pairwise monthly positive correlation");
        Check(result.ClosedDrawdownUSD<=2000,
            "closed equity combined drawdown");
        Check(result.WorstConcurrentMaeProxyUSD<=1000,
            "overlapping observed MAE exposure proxy");
        Check(result.LargestProfitContribution<=0.40,
            "no single strategy dominates realized PnL");
        Check(result.NetProfitUSD>0,"positive combined PnL");

        var two=NQNativePortfolioV13.Select(
            new[]{a,b},Robust(),p);
        Check(!two.Valid&&two.Selected.Count<3,
            "requires minimum three suitable strategies");

        var correlated=NQNativePortfolioV13.Select(
            new[]{a,d,new NQPortfolioCandidateV13("OTHER_DUP_A",
                Strategy(0))},Robust(),p);
        Check(!correlated.Valid&&correlated.Reason==
            "INSUFFICIENT_DIVERSIFIED_STRATEGIES",
            "three perfectly correlated systems cannot qualify");

        var concentrated=NQNativePortfolioV13.Select(new[]{
            new NQPortfolioCandidateV13("BIG",Strategy(0,4)),
            b,c},Robust(),p);
        Check(!concentrated.Valid &&
             (concentrated.Reason=="EXCESS_SINGLE_STRATEGY_CONTRIBUTION" ||
              concentrated.Reason=="INSUFFICIENT_DIVERSIFIED_STRATEGIES"),
            "one dominant profit source must not pass");

        var dup=NQNativePortfolioV13.Select(new[]{a,a,b,c},Robust(),p);
        Check(!dup.Valid&&dup.Reason=="INVALID_OR_DUPLICATE_IDS",
            "duplicate candidate IDs blocked");

        Console.WriteLine("NQ_V13_PORTFOLIO_PASS count="+
            result.Selected.Count+" net="+result.NetProfitUSD.ToString("F2")+
            " closedDD="+result.ClosedDrawdownUSD.ToString("F2")+
            " maxCorr="+
            result.WorstPairwiseMonthlyCorrelation.ToString("F3")+
            " maxContribution="+
            result.LargestProfitContribution.ToString("F3"));
        Console.WriteLine("PROVISIONAL_SYNTHETIC_MONTHLY_CORRELATION_ONLY");
        return 0;
    }
}
