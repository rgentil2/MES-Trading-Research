// S0.73 — conservative strategy diversification selection, research only.
// Inputs MUST be historical 2020-22 closed trades. Selects 3..5
// strategies that individually pass V13 provisional robustness and have
// limited monthly PnL correlation. Models 1 NQ contract per component,
// no fractional position weights. No tick-level simultaneous-stop/capital
// compliance claim. Evaluation years 2023+ remain held out.
using System;
using System.Collections.Generic;
using System.Linq;

namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQPortfolioCandidateV13
    {
        public readonly string Id;
        public readonly IList<NQG0RiskTradeV7> Trades;
        public NQPortfolioCandidateV13(string id,IList<NQG0RiskTradeV7> trades)
        {
            if(String.IsNullOrWhiteSpace(id)||trades==null)
                throw new ArgumentException("Candidate ID and trades required");
            Id=id;Trades=trades;
        }
    }

    public sealed class NQPortfolioConfigV13
    {
        public int TargetStrategies=3;
        public double MaximumPositiveMonthlyCorrelation=0.45;
        public double MaximumClosedPortfolioDDUSD=2000.0;
        public double MaximumOverlappingMaeProxyUSD=1000.0;
        public double MaximumProfitConcentration=0.40;
        public void Validate()
        {
            if(TargetStrategies<3||TargetStrategies>5||
               MaximumPositiveMonthlyCorrelation<0||
               MaximumPositiveMonthlyCorrelation>1||
               MaximumClosedPortfolioDDUSD<=0||
               MaximumOverlappingMaeProxyUSD<=0||
               MaximumProfitConcentration<1.0/TargetStrategies||
               MaximumProfitConcentration>1)
                throw new ArgumentException("Invalid V13 portfolio constraints");
        }
    }

    public sealed class NQPortfolioResultV13
    {
        public bool Valid;
        public string Reason;
        public readonly List<NQPortfolioCandidateV13> Selected=
            new List<NQPortfolioCandidateV13>();
        public readonly List<string> Rejected=new List<string>();
        public double NetProfitUSD,ClosedDrawdownUSD;
        public double WorstPairwiseMonthlyCorrelation;
        public double WorstConcurrentMaeProxyUSD;
        public double LargestProfitContribution;
    }

    public static class NQNativePortfolioV13
    {
        private static double[] Months(IList<NQG0RiskTradeV7> trades)
        {
            var m=new double[36];
            foreach(var t in trades)
            {
                int y=t.EntryTime.Year,mo=t.EntryTime.Month;
                if(y<2020||y>2022)
                    throw new ArgumentException("OOS trade in development portfolio");
                m[(y-2020)*12+mo-1]+=t.NetProfitUSD;
            }
            return m;
        }

        private static double Correlation(double[] a,double[] b)
        {
            double ma=a.Average(),mb=b.Average(),num=0,va=0,vb=0;
            for(int i=0;i<36;i++)
            {
                double x=a[i]-ma,y=b[i]-mb;
                num+=x*y;va+=x*x;vb+=y*y;
            }
            // Constant monthly returns are uninformative about regime
            // dependence; reject rather than pretending zero correlation.
            if(va<1e-9||vb<1e-9)return 1.0;
            return Math.Max(-1,Math.Min(1,num/Math.Sqrt(va*vb)));
        }

        private static void CombinedRisk(NQPortfolioResultV13 result)
        {
            var all=result.Selected.SelectMany(c=>c.Trades)
                .OrderBy(x=>x.ExitTime).ThenBy(x=>x.EntryTime).ToList();
            double equity=0,peak=0,dd=0;
            foreach(var t in all)
            {
                equity+=t.NetProfitUSD;
                peak=Math.Max(peak,equity);
                dd=Math.Max(dd,peak-equity);
            }
            result.NetProfitUSD=equity;
            result.ClosedDrawdownUSD=dd;

            // Not chronological intratrade MAE. Uses worst observed MAE
            // as a static per-position exposure proxy throughout its
            // lifespan, deliberately overconservative on overlapping bars.
            var events=new List<Tuple<DateTime,int,double>>();
            foreach(var t in all)
            {
                events.Add(Tuple.Create(t.EntryTime,1,t.MaeCurrency));
                events.Add(Tuple.Create(t.ExitTime,0,-t.MaeCurrency));
            }
            double openRisk=0,maxRisk=0;
            foreach(var item in events.OrderBy(x=>x.Item1)
                         .ThenBy(x=>x.Item2))
            {
                openRisk+=item.Item3;
                maxRisk=Math.Max(maxRisk,openRisk);
            }
            result.WorstConcurrentMaeProxyUSD=maxRisk;
            double totalPositive=result.Selected.Sum(x=>
                x.Trades.Sum(t=>t.NetProfitUSD));
            result.LargestProfitContribution=totalPositive<=0?1:
                result.Selected.Max(x=>
                    x.Trades.Sum(t=>t.NetProfitUSD)/totalPositive);
        }

        public static NQPortfolioResultV13 Select(
            IList<NQPortfolioCandidateV13> candidates,
            NQRobustnessConfigV13 robustness,NQPortfolioConfigV13 portfolio)
        {
            var result=new NQPortfolioResultV13{Valid=false,
                Reason="INSUFFICIENT_DIVERSIFIED_STRATEGIES"};
            if(candidates==null||robustness==null||portfolio==null)
                return result;
            portfolio.Validate();robustness.Validate();
            if(candidates.Any(x=>x==null)||
               candidates.Select(x=>x.Id).Distinct(StringComparer.Ordinal)
                   .Count()!=candidates.Count)
            {
                result.Reason="INVALID_OR_DUPLICATE_IDS";return result;
            }
            var ranked=new List<Tuple<NQPortfolioCandidateV13,
                                      NQRobustnessResultV13,double[]>>();
            foreach(var candidate in candidates)
            {
                var diag=NQNativeRobustnessV13.Evaluate(candidate.Trades,
                    robustness);
                if(!diag.Valid||!diag.ProvisionalRobustPass)
                {
                    result.Rejected.Add(candidate.Id+":RISK_OR_COST");
                    continue;
                }
                ranked.Add(Tuple.Create(candidate,diag,
                    Months(candidate.Trades)));
            }
            ranked=ranked.OrderByDescending(x=>
                    x.Item2.CostStressNetUSD/
                    (1+x.Item2.BootstrapP95ClosedDrawdownUSD))
                .ThenBy(x=>x.Item1.Id,StringComparer.Ordinal).ToList();

            var accepted=new List<Tuple<NQPortfolioCandidateV13,
                                        NQRobustnessResultV13,double[]>>();
            foreach(var candidate in ranked)
            {
                if(accepted.Count>=portfolio.TargetStrategies)break;
                double worst=-1;
                foreach(var selected in accepted)
                    worst=Math.Max(worst,
                        Correlation(candidate.Item3,selected.Item3));
                if(worst>portfolio.MaximumPositiveMonthlyCorrelation)
                {
                    result.Rejected.Add(candidate.Item1.Id+":CORRELATED");
                    continue;
                }
                accepted.Add(candidate);
            }
            result.Selected.AddRange(accepted.Select(x=>x.Item1));
            for(int i=0;i<accepted.Count;i++)
                for(int j=i+1;j<accepted.Count;j++)
                    result.WorstPairwiseMonthlyCorrelation=Math.Max(
                        result.WorstPairwiseMonthlyCorrelation,
                        Correlation(accepted[i].Item3,accepted[j].Item3));
            if(accepted.Count<portfolio.TargetStrategies)
                return result;
            CombinedRisk(result);
            if(result.ClosedDrawdownUSD>
               portfolio.MaximumClosedPortfolioDDUSD)
            {result.Reason="EXCESS_CLOSED_PORTFOLIO_DD";return result;}
            if(result.WorstConcurrentMaeProxyUSD>
               portfolio.MaximumOverlappingMaeProxyUSD)
            {result.Reason="EXCESS_OVERLAPPING_MAE_PROXY";return result;}
            if(result.LargestProfitContribution>
               portfolio.MaximumProfitConcentration)
            {result.Reason="EXCESS_SINGLE_STRATEGY_CONTRIBUTION";return result;}
            if(result.NetProfitUSD<=0)
            {result.Reason="PORTFOLIO_NEGATIVE_NET";return result;}
            result.Valid=true;
            result.Reason="PROVISIONAL_RESEARCH_PORTFOLIO_ONLY";
            return result;
        }
    }
}
