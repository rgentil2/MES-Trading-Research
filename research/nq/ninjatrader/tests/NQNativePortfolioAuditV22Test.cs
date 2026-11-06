// S0.75 synthetic end-to-end V13 diversification -> V15 chronology.
// A portfolio that looks profitable on closed trades MUST still fail
// if its original M1 bars reveal simultaneous adverse floating exposure.
using System;
using System.Collections.Generic;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;
internal static class V22RiskPortfolioAuditTest
{
    private static void A(bool yes,string why)
    {if(!yes)throw new Exception("NQ_V22_AUDIT_FAIL "+why);}

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
                    family==2?Math.Sin(m*1.7+0.4):
                    family==3?Math.Cos(m*2.3+0.7):
                    Math.Sin(m*2.9+0.2);
                for(int day=1;day<=10;day++)
                {
                    // Families 3/4 trade AFTER original 0/1/2 have
                    // closed. This verifies 5 systems without making
                    // one guaranteed 5-way simultaneous exposure.
                    var start=new DateTime(year,month,day,
                        9,family>=3?37:31,0);
                    var end=new DateTime(year,month,day,
                        9,family>=3?39:36,0);
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


    private static int[] Genes(int family)
    {
        return new[]{
            1,(40+family)*11,12,789,12,999,12,1319,12,
            0,0,0,0,20,32,2,0,14,15,25
        };
    }
    private static Dictionary<string,int[]> Genomes(
        IList<NQPortfolioExecutionCandidateV15> candidates,
        bool duplicate=false)
    {
        var ids=new Dictionary<string,int[]>(StringComparer.Ordinal);
        for(int i=0;i<candidates.Count;i++)
            ids.Add(candidates[i].Id,Genes(duplicate?0:i));
        return ids;
    }
    private static NQWalkForwardResultV15 PassingWf()
    {
        // Isolated gate fixture: this is NOT a genuine winning
        // evolutionary or independently verified walk-forward result.
        var wf=new NQWalkForwardResultV15{
            Valid=true,Reason="SYNTHETIC_GATE_FIXTURE_ONLY",
            ProvisionalStabilityPass=true,
            PositiveValidationFolds=4,GatePassingValidationFolds=4,
            AggregatedValidationNetUSD=1400
        };
        for(int i=0;i<4;i++)
        {
            int[] genes=Genes(i);
            var train=new DateTime(2020,1,1).AddMonths(6*i);
            wf.Folds.Add(new NQWalkForwardFoldV15{
                TrainingBegin=train,TrainingEnd=train.AddMonths(12),
                ValidationBegin=train.AddMonths(12),
                ValidationEnd=train.AddMonths(18),
                ChosenCanonicalId=NQNativeExitCanonicalV19
                    .Analyze(genes).RuntimeKey,
                WinningGenes=genes,EvaluatedUnique=100,
                Training=new NQFoldMetricsV15{
                    Valid=true,PeriodGatePass=true,Trades=180,
                    Months=12,NetUSD=800,ProfitFactor=1.5},
                Validation=new NQFoldMetricsV15{
                    Valid=true,PeriodGatePass=true,Trades=90,
                    Months=6,NetUSD=350,ProfitFactor=1.4}
            });
        }
        return wf;
    }
    private static NQPortfolioAuditResultV22 Audit(
        IList<NQPortfolioExecutionCandidateV15> candidates,
        IDictionary<string,int[]> genes,
        NQWalkForwardResultV15 wf,
        NQPortfolioAuditConfigV22 settings=null,
        NQRobustnessConfigV13 robust=null,
        NQPortfolioConfigV13 portfolio=null,
        NQChronologicalRiskConfigV15 risk=null,
        IList<NQTimedBarV12> bars=null)
    {
        return NQNativePortfolioAuditV22.Evaluate(
            bars??Bars(),candidates,genes,robust??Robust(),
            portfolio??Portfolio(),
            risk??new NQChronologicalRiskConfigV15(),
            wf,settings??new NQPortfolioAuditConfigV22());
    }
    public static int Main()
    {
        var a=Candidate("A",0);
        var b=Candidate("B",1);
        var c=Candidate("C",2);
        var chosen=new[]{a,b,c};
        var genes=Genomes(chosen);
        var wf=PassingWf();

        var good=Audit(chosen,genes,wf);
        A(good.Valid&&good.ProvisionalPass&&
          good.Reason=="V22_DEV_RESEARCH_PROVISIONAL_READY_FOR_OOS",
          "3 complete independent DEV strategies should PASS");
        A(good.Strategies.Count==3&&
          good.Strategies.All(x=>x.Pass&&x.G0&&x.CostStress&&
            x.MonteCarlo&&x.AnnualStability&&x.PositiveYears==3&&
            x.Annual.Count==3&&x.TotalTrades==360),
          "each of 3 candidates has G0, 360 trades, all 36 months,"+
          " positive annual, 1.5x costs and 500 path MC");
        A(good.Strategies.All(x=>x.ProfitFactor>=1.25 &&
          x.CostStressNetUSD>0 &&
          x.BootstrapP95DDUSD<2000&&
          x.Annual.All(y=>y.AnnualPass&&
            y.MonthsBelowFive==0&&y.Trades==120)),
          "per-member economic and three-year metrics all verified");
        A(good.PortfolioRisk.ProvisionalPass &&
          good.PortfolioRisk.Selection.Selected.Count==3 &&
          good.Frozen.Count==3 &&
          good.Frozen.Select(x=>x.CanonicalId)
            .Distinct(StringComparer.Ordinal).Count()==3,
          "V13 diversified + V15 chronological pass, 3 distinct"+
          " EXCANv19 frozen candidates");
        A(good.MaximumMonthlyCorrelation<=0.45&&
          good.ProfitConcentration<=0.40 &&
          good.CombinedStressDDUSD<2000 &&
          good.CombinedSessionLossUSD<1000 &&
          good.CombinedConcurrentAdverseUSD<1000 &&
          good.WfValidatedFolds==4&&
          good.WfPassingFolds==4&&good.WfPositiveFolds==4,
          "all $2000/$1000, correlation/concentration and four WF gates");
        // Positive selection of FOUR and FIVE genuine independent
        // synthetic candidate streams, including chronology-aware
        // staggered execution rather than five concurrent contracts.
        var d=Candidate("D",3);
        var fifth=Candidate("E",4);
        var four=new[]{a,b,c,d};
        var fourPortfolio=Portfolio();fourPortfolio.TargetStrategies=4;
        var fourAccepted=Audit(four,Genomes(four),wf,
            null,null,fourPortfolio);
        A(fourAccepted.ProvisionalPass&&fourAccepted.Frozen.Count==4&&
          fourAccepted.ProfitConcentration<=0.40&&
          fourAccepted.MaximumMonthlyCorrelation<=0.45,
          "four diversified members must pass their combined real M1 stress");
        var five=new[]{a,b,c,d,fifth};
        var fivePortfolio=Portfolio();fivePortfolio.TargetStrategies=5;
        var fiveAccepted=Audit(five,Genomes(five),wf,
            null,null,fivePortfolio);
        A(fiveAccepted.ProvisionalPass&&fiveAccepted.Frozen.Count==5&&
          fiveAccepted.ProfitConcentration<=0.40&&
          fiveAccepted.MaximumMonthlyCorrelation<=0.45&&
          fiveAccepted.CombinedStressDDUSD<2000&&
          fiveAccepted.CombinedSessionLossUSD<1000&&
          fiveAccepted.CombinedConcurrentAdverseUSD<1000,
          "five staggered diversified strategy fills obey all default $ limits");

        var reproduced=Audit(chosen,genes,wf);
        A(reproduced.ProvisionalPass&&
          good.Frozen.Zip(reproduced.Frozen,(x,y)=>
            x.CanonicalId==y.CanonicalId&&x.Id==y.Id).All(x=>x),
          "replaying audited portfolio preserves selected V19 gene IDs");

        // 1. G0: one month with 4 operations, but still >=150 total.
        var sparseTrades=a.Trades.Where(x=>!
            (x.EntryTime.Year==2021&&x.EntryTime.Month==4&&
             x.EntryTime.Day>4)).ToList();
        var sparse=new NQPortfolioExecutionCandidateV15(
            "A",sparseTrades,a.Executions.Where(x=>!
                (x.EntryTime.Year==2021&&x.EntryTime.Month==4&&
                 x.EntryTime.Day>4)).ToList());
        var insufficientMonth=Audit(new[]{sparse,b,c},genes,wf);
        A(!insufficientMonth.ProvisionalPass &&
          insufficientMonth.Rejections.Any(x=>
            x.Contains("MONTHLY_FREQUENCY")),
          ">=5 entries EACH of 36 months, even if >=150 total");

        // 2. Explicit minimum of 150 total trades.
        var shortTrades=a.Trades.Take(149).ToList();
        var tooFew=new NQPortfolioExecutionCandidateV15(
            "A",shortTrades,a.Executions.Take(149).ToList());
        var insufficientCount=Audit(new[]{tooFew,b,c},genes,wf);
        A(!insufficientCount.ProvisionalPass &&
          insufficientCount.Rejections.Any(x=>
            x.Contains("INSUFFICIENT_TRADES")),
          "149 trades fail 150-operation minimum");

        // 3. Increasing additional costs must break otherwise
        // economically positive candidate selection.
        var costs=Robust();
        costs.CostMultiplier=5.0;
        var stressed=Audit(chosen,genes,wf,null,costs);
        A(!stressed.ProvisionalPass&&
          stressed.Rejections.Any(x=>
            x.Contains("COST_1_5X_NONPOSITIVE")),
          "cost stress blocks nominal profitable candidates");

        // 4. Small bootstrap P95 dollar budget must reject.
        var mc=Robust();
        mc.MaxBootstrapP95ClosedDDUSD=1;
        var monte=Audit(chosen,genes,wf,null,mc);
        A(!monte.ProvisionalPass&&
          monte.Rejections.Any(x=>
            x.Contains("BOOTSTRAP_P95_DD_EXCEEDED")),
          "moving-block Monte Carlo rejects excessive resampled DD");

        // 5. Independent annual gate, beyond aggregate 2020–22 G0.
        var yearly=new NQPortfolioAuditConfigV22{
            MinimumPositiveDevelopmentYears=3,
            MinimumAnnualProfitFactor=10
        };
        var years=Audit(chosen,genes,wf,yearly);
        A(!years.ProvisionalPass&&
          years.Rejections.Any(x=>
            x.Contains("INSUFFICIENT_2020_2022_YEAR_STABILITY")),
          "three separate 2020,2021,2022 PF windows audited");

        // 6. One duplicated genome gets rejected even with unique ID.
        var dup=Audit(chosen,Genomes(chosen,true),wf);
        A(!dup.Valid&&
          dup.Reason=="DUPLICATE_OR_REDUNDANT_STRATEGY",
          "distinct IDs cannot disguise identical EXCANv19 genes");

        // 7. Correlation of portfolio members must be <.45.
        var clone=new NQPortfolioExecutionCandidateV15(
            "C",a.Trades,a.Executions);
        var correlation=Audit(new[]{a,b,clone},genes,wf);
        A(!correlation.ProvisionalPass &&
          correlation.Reason==
            "V22_DIVERSIFICATION_OR_ACCOUNT_RISK_REJECT",
          "profitable duplicate monthly profiles fail selection");

        // 8. Simultaneous floating shock rejects even if closed
        // economics, net, 1.5x costs, MC and historical trades pass.
        var shock=Audit(chosen,genes,wf,null,null,null,null,Bars(true));
        A(!shock.ProvisionalPass&&
          shock.Reason=="V22_DIVERSIFICATION_OR_ACCOUNT_RISK_REJECT"&&
          shock.PortfolioRisk.Chronology!=null &&
          shock.PortfolioRisk.Chronology.MaxAdversarialM1StressDDUSD>2000,
          "adverse high/low synthetic M1 shock breaches account DD");

        // 9. Tight daily loss must be noticed with FLOATING equity.
        var riskConfig=new NQChronologicalRiskConfigV15{
            MaxAccountStressDDUSD=2000,
            MaxSessionPeakToTroughUSD=10,
            MaxConcurrentAdverseUSD=1000
        };
        var daily=Audit(chosen,genes,wf,null,null,null,riskConfig);
        A(!daily.ProvisionalPass &&
          daily.Reason=="V22_DIVERSIFICATION_OR_ACCOUNT_RISK_REJECT",
          "independently configured daily $10 pause stress");

        // 10. Corrupted WF genome/identity mapping rejected.
        var fake=PassingWf();
        fake.Folds[1].ChosenCanonicalId="EXCANv19:WRONG";
        var future=Audit(chosen,genes,fake);
        A(!future.ProvisionalPass &&
          future.Reason=="V22_TRAIN_ONLY_GENERATOR_WALKFORWARD_REJECT",
          "forged, changed or noncanonical WF winner never opens OOS");

        // 11. Positive economics but fewer than 3 strategies.
        var two=Audit(new[]{a,b},Genomes(new[]{a,b}),wf);
        A(!two.Valid&&two.Reason=="FEWER_THAN_REQUIRED_3_TO_5",
          "cannot freeze fewer than 3 strategies");

        // 12. Original chronological filled prices must reconcile.
        var changed=new List<NQExecutionFillV12>(a.Executions);
        var e=changed[0];
        changed[0]=new NQExecutionFillV12(
            e.EntryTime,e.ExitTime,e.Side,e.Quantity,
            e.EntryPrice,e.ExitPrice+1,e.RoundTripFeesUSD);
        var bad=new NQPortfolioExecutionCandidateV15(
            "A",a.Trades,changed);
        var mismatch=Audit(new[]{bad,b,c},genes,wf);
        A(!mismatch.ProvisionalPass &&
          mismatch.Reason=="V22_DIVERSIFICATION_OR_ACCOUNT_RISK_REJECT",
          "V15 rejects fake or altered economic fill prices");

        Console.WriteLine("NQ_V22_G0_PORTFOLIO_PASS "+
            "acceptedSyntheticStrategies="+good.Frozen.Count+
            " tradesPerStrategy="+good.Strategies[0].TotalTrades+
            " monthsVerified=36 yearsPositive=3 "+
            "costMultiplier=1.5 bootstrapPaths=500"+
            " maxMonthlyCorr="+
              good.MaximumMonthlyCorrelation.ToString("F3")+
            " maxProfitConcentration="+
              good.ProfitConcentration.ToString("F3")+
            " accountStressDD="+
              good.CombinedStressDDUSD.ToString("F2")+
            " dailyPeakLoss="+
              good.CombinedSessionLossUSD.ToString("F2")+
            " completedWfGates="+good.WfPassingFolds+
            " mandatoryRejections=12"+
            " frozenKeys=EXCANv19");
        Console.WriteLine("POSITIVE_WF_IS_TEST_FIXTURE_NOT_EMPIRICAL_WINNER;"+
            " ALL_BARS_AND_TRADES_SYNTHETIC_NO_NT8_MARKET_EDGE");
        return 0;
    }
}
