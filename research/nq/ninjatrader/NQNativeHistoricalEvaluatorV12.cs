// S0.72: research-only, deterministic, conservative M1 close-bar
// approximation. This is NOT NinjaTrader's historical fill engine.
// No actual NQ 2020-22 dataset is bundled with this repository.
// All trade timestamps in EASTERN / configured bar timezone; caller
// must provide contiguous sorted M1 data and an exact roll series.
// M1 both-stop-and-target ambiguity resolves STOP FIRST (adverse).
// Costs: provisional $4.68 round-trip, adverse 2-tick slippage on
// market/stop legs; target limit fills exactly at target.
// 1 NQ contract = $20 per point, min tick 0.25 = $5.
using System;
using System.Collections.Generic;
using System.Linq;

namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQTimedBarV12
    {
        public readonly DateTime Time;
        public readonly NQBarV11 Bar;
        public NQTimedBarV12(DateTime time,NQBarV11 bar)
        {Time=time;Bar=bar;}
    }

    public sealed class NQHistoricalResultV12
    {
        public bool Valid;
        public string Reason;
        public double Score;
        public double Net;
        public int SignalCount, RiskBlocked, AtrBlocked, DailyBlocked;
        public int AmbiguousStops, StopFills, TargetFills, TimeFills;
        public readonly List<NQG0RiskTradeV7> Trades=
            new List<NQG0RiskTradeV7>();
        public NQDiscoveryResultV9 Discovery;
    }

    public static class NQNativeHistoricalEvaluatorV12
    {
        private const double Tick=0.25;
        private const double DollarPerPoint=20.0;
        private const double DollarPerTick=5.0;
        private const double FeeRT=4.68;
        private const double SlipTicks=2.0;
        private const int BeginSignal=93500;
        private const int EndSignal=112700;
        private const int FlatSubmit=112800;
        private const int FirstRth=93000;
        private const int LastRth=112700;

        private static int HHmmss(DateTime t)
        {return 10000*t.Hour+100*t.Minute+t.Second;}
        private static bool Finite(double x)
        {return !Double.IsInfinity(x)&&!Double.IsNaN(x);}

        private static int Required(int[] g)
        {
            int max=0;
            for(int j=0;j<g[0];j++)
            {
                int idx=1+2*j;
                max=Math.Max(max,NQNativeConditionsV11.RequiredBars(g[idx+1]));
            }
            return max;
        }

        private static bool TryAtr(IList<NQTimedBarV12> bars,int i,int n,
                                   out double atr)
        {
            atr=0;
            if(i<n||n<1)return false;
            // This is a SIMPLE true-range ATR and intentionally not claimed
            // identical to NinjaTrader's native Wilder ATR.
            for(int k=i-n+1;k<=i;k++)
            {
                var b=bars[k].Bar;
                double prev=bars[k-1].Bar.Close;
                atr+=Math.Max(b.High-b.Low,
                    Math.Max(Math.Abs(b.High-prev),Math.Abs(b.Low-prev)));
            }
            atr/=n;
            return Finite(atr)&&atr>0;
        }

        private static void Direction(IList<NQBarV11> rth,int[] g,
                                      out bool bull,out bool bear)
        {
            bull=false;bear=false;
            for(int s=0;s<g[0];s++)
            {
                bool b1,b2;
                if(!NQNativeConditionsV11.TryEvaluate(rth,g[1+2*s],
                        g[2+2*s],out b1,out b2))
                {
                    bull=false;bear=false;return;
                }
                if(s==0){bull=b1;bear=b2;}
                else
                {
                    bool or=g[8+s]==1;
                    bull=or ? bull||b1 : bull&&b1;
                    bear=or ? bear||b2 : bear&&b2;
                }
            }
            if(g[12]==1){bool swap=bull;bull=bear;bear=swap;}
        }

        private static NQHistoricalResultV12 Reject(string reason)
        {return new NQHistoricalResultV12{
            Valid=false,Reason=reason,Score=NQNativeDiscoveryScoreV9.InvalidScore
        };}

        public static NQHistoricalResultV12 Evaluate(
            IList<NQTimedBarV12> source,int[] genes)
        {
            if(source==null||genes==null||source.Count==0)
                return Reject("NULL_OR_EMPTY");
            NQExitIdentityV11 canonical;
            try{canonical=NQNativeExitCanonicalV11.Analyze(genes);}
            catch(ArgumentException){return Reject("INVALID_GENES");}
            if(canonical.IsRedundant)
                return Reject("REDUNDANT_BOOLEAN");
            // Full dataset must be validated even if a trade is rare. A mixed
            // 2023/26 sample MUST NOT leak into 2020-22 optimization.
            for(int i=0;i<source.Count;i++)
            {
                if(source[i]==null||source[i].Time.Year<2020 ||
                   source[i].Time.Year>2022 ||
                   i>0 && (source[i].Time<=source[i-1].Time ||
                     source[i].Time-source[i-1].Time>TimeSpan.FromDays(5)))
                    return Reject("UNSORTED_OUTSIDE_IST_OR_LARGE_GAP");
            }
            var r=new NQHistoricalResultV12{Valid=true,Reason="ESTIMATE_ONLY",
                Score=NQNativeDiscoveryScoreV9.InvalidScore};
            var rth=new List<NQBarV11>(150);
            DateTime day=DateTime.MinValue;
            int submissions=0,side=0;
            bool pendingEntry=false,pendingFlat=false;
            int nextSide=0,stopTicks=0,targetTicks=0;
            double equity=0,sessionBase=0,entry=0,mae=0,mfe=0;
            DateTime entryAt=DateTime.MinValue;

            for(int i=0;i<source.Count;i++)
            {
                var item=source[i];
                var b=item.Bar;
                DateTime date=item.Time.Date;
                int clock=HHmmss(item.Time);
                if(date!=day)
                {
                    if(side!=0||pendingEntry||pendingFlat)
                        return Reject("UNTERMINATED_OVERNIGHT_POSITION");
                    day=date;rth.Clear();submissions=0;sessionBase=equity;
                }

                // OnBarClose signal -> next M1 OPEN entry. Market fills
                // conservatively incur two adverse ticks on that OPEN.
                if(pendingEntry)
                {
                    pendingEntry=false;
                    side=nextSide;
                    entry=b.Open+side*SlipTicks*Tick;
                    entryAt=item.Time;
                    mae=0;mfe=0;
                }

                // Previously submitted 11:28 flatten -> next bar OPEN.
                if(pendingFlat && side!=0)
                {
                    double exit=b.Open-side*SlipTicks*Tick;
                    double pnl=(exit-entry)*side*DollarPerPoint-FeeRT;
                    r.Trades.Add(new NQG0RiskTradeV7(entryAt,item.Time,
                        pnl,mae,mfe));
                    r.TimeFills++;equity+=pnl;side=0;pendingFlat=false;
                }
                if(side!=0)
                {
                    double stop=entry-side*stopTicks*Tick;
                    double target=entry+side*targetTicks*Tick;
                    bool stopHit=side==1?b.Low<=stop:b.High>=stop;
                    bool targetHit=targetTicks>0 &&
                        (side==1?b.High>=target:b.Low<=target);
                    double worst=side==1?entry-b.Low:b.High-entry;
                    double best=side==1?b.High-entry:entry-b.Low;
                    mae=Math.Max(mae,Math.Max(0,worst*DollarPerPoint));
                    mfe=Math.Max(mfe,Math.Max(0,best*DollarPerPoint));
                    if(stopHit||targetHit)
                    {
                        if(stopHit && targetHit)r.AmbiguousStops++;
                        double exit;
                        if(stopHit)
                        {
                            // If the next bar opens beyond the stop, execute
                            // at the worse of stop/open plus two ticks.
                            double price=side==1?
                                Math.Min(stop,b.Open):Math.Max(stop,b.Open);
                            exit=price-side*SlipTicks*Tick;
                            r.StopFills++;
                        }
                        else{exit=target;r.TargetFills++;}
                        double pnl=(exit-entry)*side*DollarPerPoint-FeeRT;
                        r.Trades.Add(new NQG0RiskTradeV7(entryAt,item.Time,
                            pnl,mae,mfe));
                        equity+=pnl;side=0;pendingFlat=false;
                    }
                }
                if(clock>=FirstRth&&clock<=LastRth)
                    rth.Add(b);
                if(clock>=FlatSubmit)
                {
                    if(side!=0)pendingFlat=true;
                    continue;
                }
                if(clock<BeginSignal||clock>EndSignal||side!=0||
                   pendingEntry||submissions>=genes[15])
                {
                    if(submissions>=genes[15])r.DailyBlocked++;
                    continue;
                }
                if(rth.Count<Required(genes))continue;
                if(equity-sessionBase<=-600)continue;
                double atr=0;
                if(genes[16]!=0&&!TryAtr(source,i,genes[17],out atr))
                {r.AtrBlocked++;continue;}
                int stop,target;
                if(!NQNativeATRExitMathV5.TryCompute(genes[16],atr,
                    Tick,genes[13],genes[14],genes[18],genes[19],
                    out stop,out target))
                {r.AtrBlocked++;continue;}
                if(stop*DollarPerTick+SlipTicks*DollarPerTick+FeeRT>300.0)
                {r.RiskBlocked++;continue;}
                bool bull,bear;
                Direction(rth,genes,out bull,out bear);
                if(bull==bear)continue;
                r.SignalCount++;
                pendingEntry=true;
                nextSide=bull?1:-1;stopTicks=stop;targetTicks=target;
                submissions++;
            }
            if(side!=0||pendingEntry||pendingFlat)
                return Reject("MISSING_LAST_EXIT_OR_ENTRY_BAR");
            r.Net=equity;
            r.Discovery=NQNativeDiscoveryScoreV9.Evaluate(r.Trades,equity);
            r.Score=r.Discovery==null||!r.Discovery.Valid?
                NQNativeDiscoveryScoreV9.InvalidScore:r.Discovery.Score;
            return r;
        }
    }
}
