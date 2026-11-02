// S0.64 - V5 research G0 economic optimization fitness. Separate from V5
// StructureFitness, so previous V5/optimizer install and saved template remain.
// This ranks performance AFTER the native backtest. It cannot prevent the
// historical RunIteration and cannot validate intrabar floating trailing DD.
using System;
using System.Collections.Generic;
using System.Globalization;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.Strategies;
using NinjaTrader.Cbi;

namespace NinjaTrader.NinjaScript.OptimizationFitnesses
{
    public class NQNativeG0FitnessV6 : OptimizationFitness
    {
        private static void Log(string msg)
        {
            NinjaTrader.Code.Output.Process("NQ_G0 " + msg,PrintTo.OutputTab1);
        }

        protected override void OnCalculatePerformanceValue(StrategyBase strategy)
        {
            Value=NQNativeG0RulesV6.RejectScore;
            var v5=strategy as NQNativeGeneticLabV5;
            if(v5==null || !v5.CanonicalReady || v5.IsStructurallyRedundant ||
               v5.EffectiveConditionCount<1)
            {
                Log("REJECT INVALID_OR_REDUNDANT");
                return;
            }
            try
            {
                var history=strategy.SystemPerformance.AllTrades;
                var performance=history.TradesPerformance;
                double nativeNet=performance.NetProfit;
                var closed=new List<NQG0TradeV6>(history.Count);
                for(int i=0;i<history.Count;i++)
                {
                    Trade t=history[i];
                    if(t==null || t.Entry==null || t.Exit==null)
                    {
                        Log("REJECT MISSING_TRADE_EXECUTION");
                        return;
                    }
                    closed.Add(new NQG0TradeV6(
                        t.Entry.Time,t.Exit.Time,t.ProfitCurrency));
                }
                var result=NQNativeG0RulesV6.Evaluate(closed,nativeNet);
                Log((result.Pass?"PASS":"REJECT")+
                    " reason="+result.Failure+
                    " id="+(v5.CanonicalRuntimeFingerprint??"(none)")+
                    " trades="+result.Trades+
                    " net="+result.NetProfitUSD.ToString("F2",CultureInfo.InvariantCulture)+
                    " pf="+result.ProfitFactor.ToString("F4",CultureInfo.InvariantCulture)+
                    " closedDD="+result.ClosedMaxDrawdownUSD.ToString("F2",CultureInfo.InvariantCulture)+
                    " monthsBelow5="+result.MonthsBelowFive);
                if(!result.Pass)
                    return;
                // Positive, finite score only for provisionally eligible G0
                // candidates. The last step (floating DD) is separate.
                Value=result.NetProfitUSD;
            }
            catch(Exception ex)
            {
                Value=NQNativeG0RulesV6.RejectScore;
                Log("REJECT EXCEPTION "+ex.GetType().Name+" "+ex.Message);
            }
        }
    }
}
