// S0.86 V25 — FROZEN candidate validation on NinjaTrader 8.
// One fixed purpose: final native bar/signal/fill parity, NO new GA.
// This read-only signal core can be compiled both in .NET8 QA and NT8.
// It reads completed one-minute bars stamped at their START in New
// York wall-clock time (the adapter subtracts 1m from NT8 end stamp).
// No look-ahead, no bid/ask/tick assumption, no orders here.
using System;
using System.Collections.Generic;
using System.Linq;
namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQNativeV25SignalDecision
    {
        public readonly DateTime CompletedMinuteStartET;
        public readonly int Side,StopTicks,TargetTicks;
        public readonly string CanonicalKey;
        public NQNativeV25SignalDecision(DateTime at,int side,
            int stop,int target,string canonical)
        {CompletedMinuteStartET=at;Side=side;StopTicks=stop;
         TargetTicks=target;CanonicalKey=canonical;}
    }
    public sealed class NQNativeV25FrozenSignalCore
    {
        public const string Version="S0.86_V25_FROZEN_ONE_SHOT_NATIVE_1";
        public const double NQTick=0.25;
        public const double NQUSDPerTick=5.0;
        public const double ResearchFeeRoundTripUSD=4.68;
        public const int ResearchSlippageTicks=2;
        public const int FirstRth=93000,LastSignal=112700;
        public const int FirstSignal=93500,FlattenSubmit=112800;
        private readonly int[] genes;
        private readonly List<NQBarV11> rth=new List<NQBarV11>(150);
        private readonly List<NQBarV11> atrBars=new List<NQBarV11>(32);
        private DateTime prior=DateTime.MinValue,session=DateTime.MinValue;
        private readonly string key;
        private int observed,rawSignals;
        public int BarsObserved{get{return observed;}}
        public int RawSignals{get{return rawSignals;}}
        public string CanonicalId{get{return key;}}
        public int[] FrozenGenes{get{return (int[])genes.Clone();}}

        public NQNativeV25FrozenSignalCore(int[] frozenGenes)
        {
            var canonical=NQNativeExitCanonicalV19.Analyze(frozenGenes);
            if(canonical.IsRedundant)
                throw new ArgumentException("V25_REDUNDANT_FROZEN_GENOME");
            genes=(int[])frozenGenes.Clone();key=canonical.RuntimeKey;
        }
        public static DateTime NinjaTraderMinuteStart(DateTime endStampET)
        {
            if(endStampET.Kind==DateTimeKind.Utc)
                throw new ArgumentException("V25_NT8_EXPECTS_ET_WALL_CLOCK");
            if(endStampET.Second!=0||endStampET.Millisecond!=0)
                throw new ArgumentException("V25_REQUIRES_END_STAMPED_M1");
            return DateTime.SpecifyKind(endStampET.AddMinutes(-1),
                DateTimeKind.Unspecified);
        }
        private static int Clock(DateTime time)
        {return 10000*time.Hour+100*time.Minute+time.Second;}
        private double SimpleAtr(int period)
        {
            if(atrBars.Count<period+1)return 0;
            double sum=0;
            for(int i=atrBars.Count-period;i<atrBars.Count;i++)
            {
                var now=atrBars[i];
                var prev=atrBars[i-1];
                double tr=Math.Max(now.High-now.Low,
                    Math.Max(Math.Abs(now.High-prev.Close),
                        Math.Abs(now.Low-prev.Close)));
                sum+=tr;
            }
            return sum/period;
        }
        // The reference research generator counts the last completed
        // bar as the candidate signal observation and submits an entry
        // for NEXT minute's open. The bridge returns only an intention,
        // leaving execution timing to NT8 Strategy Analyzer.
        public NQNativeV25SignalDecision PushCompletedBar(
            DateTime minuteStartET,NQBarV11 completed)
        {
            if(minuteStartET.Kind==DateTimeKind.Utc||
               minuteStartET.Second!=0||minuteStartET.Millisecond!=0||
               minuteStartET.Year<2020||minuteStartET.Year>2026||
               (prior!=DateTime.MinValue&&
                 (minuteStartET<=prior||
                  minuteStartET-prior>TimeSpan.FromDays(5))))
                throw new ArgumentException("V25_INVALID_M1_TIME_ORDER_OR_PERIOD");
            if(prior==DateTime.MinValue||
               session!=minuteStartET.Date)
            {
                rth.Clear();session=minuteStartET.Date;
            }
            prior=minuteStartET;observed++;
            atrBars.Add(completed);
            if(atrBars.Count>32)atrBars.RemoveAt(0);
            int clock=Clock(minuteStartET);
            if(clock>=FirstRth&&clock<=LastSignal)
                rth.Add(completed);
            if(clock<FirstSignal||clock>LastSignal)return null;
            int needed=0;
            for(int i=0;i<genes[0];i++)
                needed=Math.Max(needed,
                    NQNativeConditionCatalogV19.RequiredBars(
                        genes[2+2*i]));
            if(rth.Count<needed)return null;
            double atr=genes[16]==0?0:SimpleAtr(genes[17]);
            if(genes[16]!=0&&atr<=0)return null;
            int stop,target;
            if(!NQNativeATRExitMathV5.TryCompute(
                genes[16],atr,NQTick,genes[13],genes[14],
                genes[18],genes[19],out stop,out target))
                return null;
            if(stop*NQUSDPerTick+
                ResearchSlippageTicks*NQUSDPerTick+
                ResearchFeeRoundTripUSD>300.0)return null;
            bool bull=false,bear=false;
            for(int s=0;s<genes[0];s++)
            {
                bool b1,b2;
                if(!NQNativeConditionCatalogV19.TryEvaluate(rth,
                    genes[1+2*s],genes[2+2*s],out b1,out b2))
                    return null;
                if(s==0){bull=b1;bear=b2;}
                else
                {
                    bool or=genes[8+s]==1;
                    bull=or?bull||b1:bull&&b1;
                    bear=or?bear||b2:bear&&b2;
                }
            }
            if(genes[12]==1){bool tmp=bull;bull=bear;bear=tmp;}
            if(bull==bear)return null;
            rawSignals++;
            return new NQNativeV25SignalDecision(minuteStartET,
                bull?1:-1,stop,target,key);
        }
    }
}
