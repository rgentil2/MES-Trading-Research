// S0.66 — separate NT8 Research Fitness V7; V5/V6 untouched.
// Uses native Trade.MaeCurrency and Trade.MfeCurrency (historical M1 bar
// extrema). The risk field is a STRESS PROXY, not account intrabar DD.
// Called AFTER backtest; no live orders, no 2023+ data, no trading logic.
using System;
using System.Collections.Generic;
using System.Globalization;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.Strategies;
using NinjaTrader.Cbi;

namespace NinjaTrader.NinjaScript.OptimizationFitnesses
{
    public class NQNativeG0RiskFitnessV7 : OptimizationFitness
    {
        private static string N(double x)
        { return x.ToString("F2",CultureInfo.InvariantCulture); }
        private static void Log(string s)
        { NinjaTrader.Code.Output.Process("NQ_G0_V7 "+s,PrintTo.OutputTab1); }

        protected override void OnCalculatePerformanceValue(StrategyBase strategy)
        {
            Value=NQNativeG0RulesV6.RejectScore;
            var v5=strategy as NQNativeGeneticLabV5;
            if(v5==null || !v5.CanonicalReady || v5.IsStructurallyRedundant ||
               v5.EffectiveConditionCount<1)
            {
                Log("REJECT reasons=INVALID_OR_REDUNDANT");
                return;
            }
            try
            {
                var history=strategy.SystemPerformance.AllTrades;
                var closed=new List<NQG0RiskTradeV7>(history.Count);
                for(int i=0;i<history.Count;i++)
                {
                    Trade t=history[i];
                    if(t==null || t.Entry==null || t.Exit==null)
                    {
                        Log("REJECT reasons=MISSING_TRADE_EXECUTION");
                        return;
                    }
                    closed.Add(new NQG0RiskTradeV7(
                        t.Entry.Time,t.Exit.Time,t.ProfitCurrency,
                        t.MaeCurrency,t.MfeCurrency));
                }
                double nativeNet=history.TradesPerformance.NetProfit;
                var result=NQNativeG0DiagnosticsV7.Evaluate(closed,nativeNet);
                string reasons=result.Pass?"PASS_PROVISIONAL_M1_STRESS":
                    string.Join(",",result.AllFailures);
                var r=result.Economic;
                Log((result.Pass?"PASS":"REJECT")+
                    " reasons="+reasons+
                    " id="+(v5.CanonicalRuntimeFingerprint??"(none)")+
                    " trades="+(r==null ? closed.Count : r.Trades)+
                    " net="+(r==null ? "NA" : N(r.NetProfitUSD))+
                    " pf="+(r==null ? "NA" : r.ProfitFactor.ToString("F4",CultureInfo.InvariantCulture))+
                    " closedDD="+(r==null ? "NA" : N(r.ClosedMaxDrawdownUSD))+
                    " stressDD="+(result.Valid ? N(result.MaeMfeStressDrawdownUSD) : "NA")+
                    " monthsBelow5="+result.MonthsBelowFive+
                    " worstMAE="+(result.Valid ? N(result.WorstTradeMaeUSD) : "NA"));
                if(result.Pass)
                    Value=result.Economic.NetProfitUSD;
            }
            catch(Exception ex)
            {
                Value=NQNativeG0RulesV6.RejectScore;
                Log("REJECT reasons=EXCEPTION:"+ex.GetType().Name+
                    " "+ex.Message);
            }
        }
    }
}
