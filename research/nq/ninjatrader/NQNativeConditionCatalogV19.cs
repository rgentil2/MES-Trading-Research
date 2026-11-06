// S0.80 V19: 120 implemented OHLCV formula definitions × 11
// completed-M1 directional predicate variants = 1,320 conditions.
// IDs 0..131 EXACT V11; 132..395 EXACT V18; 396..1319 NEW V19.
// IMPORTANT: 120 programmed named formulas does NOT imply 120
// statistically independent indicators nor NinjaTrader built-in parity.
// No future bars or unavailable bid/ask/volume-at-price data.
using System;
using System.Collections.Generic;

namespace NinjaTrader.NinjaScript.Strategies
{
    public static class NQNativeConditionCatalogV19
    {
        public const int V11Families=12;
        public const int V18Families=36;
        public const int NewFamilies=84;
        public const int Families=120;
        public const int Rules=NQNativeConditionsV11.Rules;
        public const int Count=Families*Rules; // 1,320
        public const int MinPeriod=NQNativeConditionsV11.MinPeriod;
        public const int MaxPeriod=NQNativeConditionsV11.MaxPeriod;

        public static readonly string[] AddedNames=new[]{
            // TREND / ADAPTIVE MA: families 36..56 (21)
            "Fast SMA versus slow SMA / ATR",
            "Fast EMA versus slow EMA / ATR",
            "Fast WMA versus slow WMA / ATR",
            "Wilder SMMA displacement / ATR",
            "Wilder SMMA slope / ATR",
            "Linear regression fitting residual / ATR",
            "Signed linear-regression R squared",
            "Linear-regression slope change / ATR",
            "Kaufman adaptive moving average displacement",
            "Fractal adaptive moving average displacement",
            "McGinley Dynamic displacement",
            "Tillson T3 displacement",
            "Triangular moving average displacement",
            "Median price exponential moving average",
            "Typical price exponential moving average",
            "Weighted-close exponential moving average",
            "Typical-price SMA divergence",
            "Sine-weighted moving average divergence",
            "VIDYA Chande adaptive moving average",
            "Zero-lag least squares regression average",
            "EMA-smoothed n-lag momentum",
            // MOMENTUM / OSCILLATORS: families 57..77 (21)
            "Williams accumulation/distribution momentum",
            "Ultimate oscillator centered",
            "Stochastic RSI centered",
            "Connors RSI composite",
            "Relative momentum index (RMI)",
            "Short minus long RSI oscillator",
            "Percentage price oscillator (PPO)",
            "Percentage volume oscillator (PVO)",
            "Know Sure Thing weighted ROC",
            "Know Sure Thing first derivative",
            "TRIX acceleration",
            "Inverse Fisher transform RSI",
            "Schaff Trend Cycle stochastic MACD proxy",
            "Double-smoothed stochastic momentum index",
            "Choppiness index directional efficiency",
            "CCI of typical price relative EMA",
            "Center of gravity oscillator",
            "Laguerre RSI",
            "Coppock dual ROC weighted average",
            "Balance of Power moving average",
            "Elder bull versus bear power",
            // VOLATILITY / CHANNELS: families 78..98 (21)
            "Keltner ATR channel breakout",
            "Donchian channel midpoint slope",
            "Prior Donchian channel breakout distance",
            "Donchian midpoint displacement / ATR",
            "ATR channel weighted EMA slope",
            "Bollinger bandwidth trend regime",
            "Historical standard deviation change",
            "Log-return volatility expansion",
            "Normalized ATR expansion",
            "Parkinson OHLC volatility signed trend",
            "Garman Klass range volatility signed trend",
            "Rogers Satchell OHLC volatility signed trend",
            "Yang Zhang open-close volatility signed trend",
            "Chaikin range volatility expansion",
            "Ulcer drawdown risk adjusted momentum",
            "Chande Kroll ATR stop-channel divergence",
            "Supertrend dynamic channel stop distance",
            "Ichimoku Tenkan versus Kijun spread",
            "Ichimoku current cloud span A/B spread",
            "DeMark rolling pivot deviation",
            "Bollinger Keltner squeeze momentum",
            // VOLUME / PRICE ACTION: families 99..119 (21)
            "Signed volume moving average oscillator",
            "Relative volume surprise weighted ROC",
            "Negative Volume Index momentum",
            "Positive Volume Index momentum",
            "Volume Flow Indicator (VFI proxy)",
            "Accumulated relative-price volume flow",
            "PVT exponential smoothing divergence",
            "Klinger volume-force oscillator proxy",
            "Twiggs money-flow smoothed proxy",
            "Volume-weighted price RSI",
            "Volume-adjusted EMA MACD",
            "Up-volume minus down-volume ratio",
            "Volume surprise weighted price momentum",
            "Candle-body proportional volume delta proxy",
            "Causal Heikin Ashi candle strength",
            "Candle body versus wick pressure",
            "Two-candle body engulfing signal",
            "Inside-outside bar directional range",
            "NR7 narrow-range breakout",
            "Polarized fractal efficiency",
            "Hurst rescaled-range trend persistence"
        };
        public static int RequiredBars(int period)
        {return NQNativeConditionsV11.RequiredBars(period);}

        public static string Name(int type)
        {
            if(type<0||type>=Count)
                throw new ArgumentOutOfRangeException("type");
            if(type<NQNativeConditionCatalogV18.Count)
                return NQNativeConditionCatalogV18.Name(type);
            return AddedNames[type/Rules-V18Families]+
                " / "+NQNativeConditionsV11.RuleNames[type%Rules];
        }

        internal static double Feature(IList<NQBarV11> b,int at,
                                       int family,int period)
        {
            if(family<36||family>=120)
                throw new ArgumentOutOfRangeException("family");
            if(family<57)
                return NQTrendFeaturesV19.Compute(b,at,period,family);
            if(family<78)
                return NQMomentumFeaturesV19.Compute(b,at,period,family);
            if(family<99)
                return NQVolatilityFeaturesV19.Compute(b,at,period,family);
            return NQVolumeActionFeaturesV19.Compute(b,at,period,family);
        }

        private static bool Finite(double x)
        {return !Double.IsNaN(x)&&!Double.IsInfinity(x);}
        public static bool TryEvaluate(IList<NQBarV11> bars,int type,
            int period,out bool bull,out bool bear)
        {
            bull=false;bear=false;
            if(bars==null||type<0||type>=Count||
               period<MinPeriod||period>MaxPeriod||
               bars.Count<RequiredBars(period))
                return false;
            if(type<NQNativeConditionCatalogV18.Count)
                return NQNativeConditionCatalogV18.TryEvaluate(bars,
                    type,period,out bull,out bear);
            int family=type/Rules,rule=type%Rules,at=bars.Count-1;
            double x=Feature(bars,at,family,period);
            double y=Feature(bars,at-1,family,period);
            double z=Feature(bars,at-2,family,period);
            if(!Finite(x)||!Finite(y)||!Finite(z))
                return false;
            switch(rule)
            {
                case 0: bull=x>0;bear=x<0;break;
                case 1: bull=x>y;bear=x<y;break;
                case 2:
                    bull=y<=0&&x>0;bear=y>=0&&x<0;break;
                case 3: bull=x>0.15;bear=x< -0.15;break;
                case 4: bull=x>0.35;bear=x< -0.35;break;
                case 5: bull=x>0.60;bear=x< -0.60;break;
                case 6:
                    bull=y<=0.15&&x>0.15;
                    bear=y>=-0.15&&x< -0.15;break;
                case 7:
                    bull=y<=0.35&&x>0.35;
                    bear=y>=-0.35&&x< -0.35;break;
                case 8:
                    bull=y< -0.60&&x>=-0.60;
                    bear=y>0.60&&x<=0.60;break;
                case 9:
                    bull=x-2*y+z>1e-9;
                    bear=x-2*y+z< -1e-9;break;
                case 10:
                    bull=x>0&&y>0;bear=x<0&&y<0;break;
            }
            return true;
        }
    }
}
