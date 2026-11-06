// S0.73 — pure C# strategy robustness on CLOSED historical trade lists.
// Risk gates reuse V7/V6 exactly; new 1.5x all-in cost stress plus moving-
// block bootstrap (WITH replacement) of net trade outcomes. Does not claim
// intrabar chronological DD, walk-forward, funded-account approval or edge.
// Samples 2020-22 only, NEVER consumes held-out OOS 2023+ data.
using System;
using System.Collections.Generic;
using System.Linq;

namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQRobustnessConfigV13
    {
        public int BootstrapPaths=2000;
        public int BlockLengthTrades=8;
        public int Seed=20261105;
        public double BaseAllInCostPerTradeUSD=24.68;
        public double CostMultiplier=1.5;
        public double MaxBootstrapP95ClosedDDUSD=2000.0;

        public void Validate()
        {
            if(BootstrapPaths<100||BootstrapPaths>100000||
               BlockLengthTrades<1||BlockLengthTrades>1000||
               Seed<1||Double.IsNaN(BaseAllInCostPerTradeUSD)||
               Double.IsInfinity(BaseAllInCostPerTradeUSD)||
               BaseAllInCostPerTradeUSD<0||
               Double.IsNaN(CostMultiplier)||Double.IsInfinity(CostMultiplier)||
               CostMultiplier<1||CostMultiplier>5||
               MaxBootstrapP95ClosedDDUSD<=0||
               Double.IsNaN(MaxBootstrapP95ClosedDDUSD))
                throw new ArgumentException("Invalid V13 bootstrap/cost settings");
        }
    }

    public sealed class NQRobustnessResultV13
    {
        public bool Valid,ProvisionalG0Pass,CostStressPositive,MonteCarloRiskPass;
        public bool ProvisionalRobustPass;
        public string Reason;
        public int Trades,BootstrapPaths;
        public double HistoricalNetUSD,CostStressNetUSD;
        public double BootstrapP95ClosedDrawdownUSD;
        public double BootstrapP05NetUSD;
        public double ProbabilityBootstrapNetNegative;
        public NQG0DiagnosticsResultV7 G0Diagnostics;
    }

    public static class NQNativeRobustnessV13
    {
        private static bool Finite(double x)
        {return !Double.IsNaN(x)&&!Double.IsInfinity(x);}
        private static double Percentile(List<double> sorted,double q)
        {
            int last=sorted.Count-1;
            double ix=q*last;
            int lo=(int)Math.Floor(ix),hi=(int)Math.Ceiling(ix);
            return sorted[lo]+(ix-lo)*(sorted[hi]-sorted[lo]);
        }

        public static NQRobustnessResultV13 Evaluate(
            IList<NQG0RiskTradeV7> trades,NQRobustnessConfigV13 cfg)
        {
            var bad=new NQRobustnessResultV13 {
                Reason="INVALID_INPUT",Valid=false
            };
            if(trades==null||cfg==null||trades.Count==0)return bad;
            cfg.Validate();
            double net=0;
            foreach(var t in trades)
            {
                if(t==null||!Finite(t.NetProfitUSD))
                    return bad;
                net+=t.NetProfitUSD;
            }
            var g0=NQNativeG0DiagnosticsV7.Evaluate(trades,net);
            if(g0==null||!g0.Valid)
            {
                bad.Reason=g0==null?"NULL_G0":g0.FirstV6Failure;
                return bad;
            }

            double additionalCost=(cfg.CostMultiplier-1.0)*
                cfg.BaseAllInCostPerTradeUSD;
            var adjusted=trades.Select(x=>x.NetProfitUSD-additionalCost)
                .ToArray();
            double costNet=adjusted.Sum();
            int length=adjusted.Length;
            var rng=new Random(cfg.Seed);
            var ddSamples=new List<double>(cfg.BootstrapPaths);
            var netSamples=new List<double>(cfg.BootstrapPaths);
            int negative=0;
            for(int p=0;p<cfg.BootstrapPaths;p++)
            {
                double equity=0,peak=0,worstDD=0;
                int filled=0;
                // Circular moving-block bootstrap retains local order
                // within a contiguous sequence of BlockLengthTrades.
                while(filled<length)
                {
                    int start=rng.Next(length);
                    int block=Math.Min(cfg.BlockLengthTrades,length-filled);
                    for(int j=0;j<block;j++)
                    {
                        double step=adjusted[(start+j)%length];
                        equity+=step;
                        peak=Math.Max(peak,equity);
                        worstDD=Math.Max(worstDD,peak-equity);
                    }
                    filled+=block;
                }
                if(!Finite(equity)||!Finite(worstDD))
                    return bad;
                if(equity<0)negative++;
                ddSamples.Add(worstDD);
                netSamples.Add(equity);
            }
            ddSamples.Sort();netSamples.Sort();
            double p95=Percentile(ddSamples,0.95);
            double p05=Percentile(netSamples,0.05);
            bool costPositive=costNet>0;
            bool mcPass=p95<=cfg.MaxBootstrapP95ClosedDDUSD;
            return new NQRobustnessResultV13{
                Valid=true,Reason="HISTORICAL_TRADE_BOOTSTRAP_ONLY",
                Trades=trades.Count,BootstrapPaths=cfg.BootstrapPaths,
                G0Diagnostics=g0,ProvisionalG0Pass=g0.Pass,
                HistoricalNetUSD=net,CostStressNetUSD=costNet,
                CostStressPositive=costPositive,
                BootstrapP95ClosedDrawdownUSD=p95,
                BootstrapP05NetUSD=p05,
                ProbabilityBootstrapNetNegative=
                    (double)negative/cfg.BootstrapPaths,
                MonteCarloRiskPass=mcPass,
                ProvisionalRobustPass=g0.Pass&&costPositive&&mcPass
            };
        }
    }
}
