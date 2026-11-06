// S0.75 — last-mile provisional portfolio risk gate.
// First uses V13's 3–5 diversification/cost/closed-DD selection, then
// REQUIRES minute-by-minute V15 account risk on the combined executed
// entry/exit ledger. Fails closed on inconsistent per-trade economics.
// ALL inputs are 2020–22 development-only; NO live/prop approval.
using System;
using System.Collections.Generic;
using System.Linq;

namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQPortfolioExecutionCandidateV15
    {
        public readonly string Id;
        public readonly IList<NQG0RiskTradeV7> Trades;
        public readonly IList<NQExecutionFillV12> Executions;
        public NQPortfolioExecutionCandidateV15(string id,
            IList<NQG0RiskTradeV7> trades,
            IList<NQExecutionFillV12> executions)
        {
            Id=id;Trades=trades;Executions=executions;
        }
    }

    public sealed class NQIntegratedPortfolioRiskResultV15
    {
        public bool Valid,ProvisionalPass;
        public string Reason;
        public NQPortfolioResultV13 Selection;
        public NQChronologicalRiskResultV15 Chronology;
    }

    public static class NQNativeIntegratedPortfolioRiskV15
    {
        private static NQIntegratedPortfolioRiskResultV15 Fail(string why)
        {return new NQIntegratedPortfolioRiskResultV15{
            Valid=false,ProvisionalPass=false,Reason=why
        };}
        public static NQIntegratedPortfolioRiskResultV15 Evaluate(
            IList<NQTimedBarV12> source,
            IList<NQPortfolioExecutionCandidateV15> candidates,
            NQRobustnessConfigV13 robustness,NQPortfolioConfigV13 portfolio,
            NQChronologicalRiskConfigV15 chronology)
        {
            if(source==null||candidates==null||robustness==null||
               portfolio==null||chronology==null)
                return Fail("NULL_INPUT");
            if(candidates.Count<portfolio.TargetStrategies)
                return Fail("INSUFFICIENT_CANDIDATES");
            var ids=new HashSet<string>(StringComparer.Ordinal);
            foreach(var c in candidates)
            {
                if(c==null||String.IsNullOrWhiteSpace(c.Id)||
                   !ids.Add(c.Id)||c.Trades==null||c.Executions==null||
                   c.Trades.Count!=c.Executions.Count)
                    return Fail("INVALID_OR_DUPLICATE_CANDIDATE");
                for(int i=0;i<c.Trades.Count;i++)
                {
                    var t=c.Trades[i];
                    var f=c.Executions[i];
                    if(t==null||f==null||t.EntryTime!=f.EntryTime||
                       t.ExitTime!=f.ExitTime||f.Quantity!=1||
                       f.Side!=1&&f.Side!=-1 ||
                       Math.Abs((f.ExitPrice-f.EntryPrice)*
                           20.0*f.Side*f.Quantity-
                           f.RoundTripFeesUSD-t.NetProfitUSD)>0.03)
                        return Fail("EXECUTION_AND_TRADE_PNL_MISMATCH");
                }
            }
            var v13=new List<NQPortfolioCandidateV13>();
            foreach(var c in candidates)
                v13.Add(new NQPortfolioCandidateV13(c.Id,c.Trades));
            NQPortfolioResultV13 selection;
            try
            {selection=NQNativePortfolioV13.Select(
                v13,robustness,portfolio);}
            catch(ArgumentException ex)
            {return Fail("INVALID_V13_CONFIG_"+ex.GetType().Name);}

            var result=new NQIntegratedPortfolioRiskResultV15{
                Valid=true,Selection=selection,
                Reason="PORTFOLIO_PROVISIONAL_ONLY"
            };
            if(!selection.Valid)
            {
                result.Reason="V13_REJECT_"+selection.Reason;
                return result;
            }
            var chosen=new HashSet<string>(
                selection.Selected.Select(x=>x.Id),StringComparer.Ordinal);
            var combined=new List<NQExecutionFillV12>();
            foreach(var c in candidates)
                if(chosen.Contains(c.Id))
                    combined.AddRange(c.Executions);
            result.Chronology=NQNativeChronologicalRiskV15.Evaluate(
                source,combined,chronology);
            if(!result.Chronology.Valid)
            {
                result.Valid=false;
                result.Reason="V15_INVALID_"+result.Chronology.Reason;
                return result;
            }
            // Explicit reconciliation prevents optimistic selection if
            // expected combined pnl and actual recorded fill pnl differ.
            if(Math.Abs(result.Chronology.RealizedNetUSD-
                        selection.NetProfitUSD)>0.03)
            {
                result.Valid=false;
                result.Reason="COMBINED_LEDGER_NET_MISMATCH";
                return result;
            }
            result.ProvisionalPass=result.Chronology.ProvisionalPass;
            if(!result.ProvisionalPass)
                result.Reason="V15_CHRONOLOGICAL_RISK_REJECT";
            else result.Reason="V13_AND_V15_PROVISIONAL_PASS";
            return result;
        }
    }
}
