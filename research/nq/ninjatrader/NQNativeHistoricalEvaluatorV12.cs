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

    // One completed synthetic M1 fill round trip, with BOTH entry and exit
    // prices. These are filled by V12 conservative OFFLINE estimates only,
    // not proprietary NinjaTrader orders. No OOS or actual broker receipts.
    public sealed class NQExecutionFillV12
    {
        public readonly DateTime EntryTime,ExitTime;
        public readonly int Side,Quantity;
        public readonly double EntryPrice,ExitPrice,RoundTripFeesUSD;
        public NQExecutionFillV12(DateTime entryTime,DateTime exitTime,
            int side,int quantity,double entryPrice,double exitPrice,
            double feesUSD)
        {
            EntryTime=entryTime;ExitTime=exitTime;Side=side;
            Quantity=quantity;EntryPrice=entryPrice;ExitPrice=exitPrice;
            RoundTripFeesUSD=feesUSD;
        }
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
        public readonly List<NQExecutionFillV12> Executed=
            new List<NQExecutionFillV12>();
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
                                      int sourceIndex,
                                      Func<int,int,int,int> cachedSignal,
                                      out bool bull,out bool bear)
        {
            bull=false;bear=false;
            for(int s=0;s<g[0];s++)
            {
                bool b1,b2;
                if(cachedSignal==null)
                {
                    if(!NQNativeConditionsV11.TryEvaluate(rth,g[1+2*s],
                            g[2+2*s],out b1,out b2))
                    {
                        bull=false;bear=false;return;
                    }
                }
                else
                {
                    // -1=short; 0=neutral/unready; +1=long.
                    // Fail closed on an invalid cache value.
                    int signal=cachedSignal(sourceIndex,g[1+2*s],g[2+2*s]);
                    if(signal< -1 || signal>1)
                        throw new InvalidOperationException(
                            "Invalid cached directional signal");
                    b1=signal==1;
                    b2=signal==-1;
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
            return EvaluateWithSignals(source,genes,null,false);
        }

        // V16 FROZEN external validation: the *same* conservative
        // fills/entry/exit simulator can measure 2023–24 or 2025–26
        // with NO V9/V7 2020–22 training score. This method has no GA
        // callback and must not be used to select/tune candidates.
        public static NQHistoricalResultV12 EvaluateHeldout(
            IList<NQTimedBarV12> source,int[] genes,
            NQDataPartitionV16 partition)
        {
            int from=NQNativeDataLoaderV16.FirstYear(partition);
            int through=NQNativeDataLoaderV16.LastYear(partition);
            if(partition==NQDataPartitionV16.Development2020_2022)
                return Reject("DEVELOPMENT_NOT_A_HELDOUT");
            return EvaluateCore(source,genes,null,false,null,
                from,through,false);
        }

        // Internal research fast path. The V14 cache is responsible for
        // creating and validating an immutable source snapshot; ordinary
        // public calls still independently validate every input bar.
        internal static NQHistoricalResultV12 EvaluateWithSignals(
            IList<NQTimedBarV12> source,int[] genes,
            Func<int,int,int,int> cachedSignal,bool sourceValidated)
        {
            return EvaluateWithSignals(source,genes,cachedSignal,
                sourceValidated,null);
        }

        // Optional ATR lookup must reproduce the original SIMPLE TR mean
        // over the UNFILTERED M1 source, even when the research loop omits
        // overnight bars. Returning <=0 rejects an unavailable ATR.
        internal static NQHistoricalResultV12 EvaluateWithSignals(
            IList<NQTimedBarV12> source,int[] genes,
            Func<int,int,int,int> cachedSignal,bool sourceValidated,
            Func<int,int,double> cachedAtr)
        {
            return EvaluateCore(source,genes,cachedSignal,
                sourceValidated,cachedAtr,2020,2022,true);
        }

        private static NQHistoricalResultV12 EvaluateCore(
            IList<NQTimedBarV12> source,int[] genes,
            Func<int,int,int,int> cachedSignal,bool sourceValidated,
            Func<int,int,double> cachedAtr,int firstYear,int lastYear,
            bool discovery)
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
            if(!sourceValidated)
            for(int i=0;i<source.Count;i++)
            {
                if(source[i]==null||source[i].Time.Year<firstYear ||
                   source[i].Time.Year>lastYear ||
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
                    r.Executed.Add(new NQExecutionFillV12(entryAt,
                        item.Time,side,1,entry,exit,FeeRT));
                    r.TimeFills++;equity+=pnl;side=0;pendingFlat=false;
                }
                if(side!=0)
                {
                    double stopPx=entry-side*stopTicks*Tick;
                    double targetPx=entry+side*targetTicks*Tick;
                    bool stopHit=side==1?b.Low<=stopPx:b.High>=stopPx;
                    bool targetHit=targetTicks>0 &&
                        (side==1?b.High>=targetPx:b.Low<=targetPx);
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
                                Math.Min(stopPx,b.Open):Math.Max(stopPx,b.Open);
                            exit=price-side*SlipTicks*Tick;
                            r.StopFills++;
                        }
                        else{exit=targetPx;r.TargetFills++;}
                        double pnl=(exit-entry)*side*DollarPerPoint-FeeRT;
                        r.Trades.Add(new NQG0RiskTradeV7(entryAt,item.Time,
                            pnl,mae,mfe));
                        r.Executed.Add(new NQExecutionFillV12(entryAt,
                            item.Time,side,1,entry,exit,FeeRT));
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
                if(genes[16]!=0)
                {
                    if(cachedAtr==null)
                    {
                        if(!TryAtr(source,i,genes[17],out atr))
                        {r.AtrBlocked++;continue;}
                    }
                    else
                    {
                        atr=cachedAtr(i,genes[17]);
                        if(!Finite(atr)||atr<=0)
                        {r.AtrBlocked++;continue;}
                    }
                }
                int stop,target;
                if(!NQNativeATRExitMathV5.TryCompute(genes[16],atr,
                    Tick,genes[13],genes[14],genes[18],genes[19],
                    out stop,out target))
                {r.AtrBlocked++;continue;}
                if(stop*DollarPerTick+SlipTicks*DollarPerTick+FeeRT>300.0)
                {r.RiskBlocked++;continue;}
                bool bull,bear;
                Direction(rth,genes,i,cachedSignal,out bull,out bear);
                if(bull==bear)continue;
                r.SignalCount++;
                pendingEntry=true;
                nextSide=bull?1:-1;stopTicks=stop;targetTicks=target;
                submissions++;
            }
            if(side!=0||pendingEntry||pendingFlat)
                return Reject("MISSING_LAST_EXIT_OR_ENTRY_BAR");
            r.Net=equity;
            if(discovery)
            {
                r.Discovery=NQNativeDiscoveryScoreV9.Evaluate(r.Trades,equity);
                r.Score=r.Discovery==null||!r.Discovery.Valid?
                    NQNativeDiscoveryScoreV9.InvalidScore:r.Discovery.Score;
            }
            else
            {
                // Never evaluate V9 (whose economic gate expects 2020-22)
                // or leak an external segment's rank into the GA.
                r.Reason="FROZEN_EXTERNAL_ESTIMATE_ONLY";
                r.Score=NQNativeDiscoveryScoreV9.InvalidScore;
            }
            return r;
        }
    }
}
