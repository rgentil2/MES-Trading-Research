// S0.71 V11 — 132 executable signal CONDITIONS = 12 distinct OHLCV feature
// families x 11 explicit directional predicates. NOT 132 unrelated indicators.
// Pure C#, no NinjaTrader dependency; sampled at completed M1 bars only.
// Historical RESEARCH ONLY. Signals are NOT optimized or validated for profit.
using System;
using System.Collections.Generic;
namespace NinjaTrader.NinjaScript.Strategies
{
    public struct NQBarV11
    {
        public readonly double Open, High, Low, Close, Volume;
        public NQBarV11(double open,double high,double low,double close,double volume)
        {
            if(!Finite(open)||!Finite(high)||!Finite(low)||!Finite(close)||
               !Finite(volume)||volume<0 || high<low || open>high ||
               open<low || close>high || close<low)
                throw new ArgumentException("Invalid completed OHLCV bar");
            Open=open;High=high;Low=low;Close=close;Volume=volume;
        }
        private static bool Finite(double v)
        { return !Double.IsNaN(v) && !Double.IsInfinity(v); }
    }

    public static class NQNativeConditionsV11
    {
        public const int Families=12;
        public const int Rules=11;
        public const int Count=Families*Rules; // 132
        public const int MinPeriod=4;
        public const int MaxPeriod=30;
        public static readonly string[] FamilyNames={
            "Close minus SMA / ATR", "Close minus EMA / ATR",
            "SMA fast minus EMA slow / ATR", "Close minus WMA / ATR",
            "Wilder RSI centered", "CCI scaled", "ATR-normalized ROC",
            "Close stochastic position", "EMA MACD / ATR",
            "Bollinger position z", "Money flow index centered",
            "Volume-weighted close location"
        };
        public static readonly string[] RuleNames={
            "Positive/negative", "Rising/falling", "Zero cross",
            "Threshold 0.15", "Threshold 0.35", "Threshold 0.60",
            "Threshold 0.15 cross", "Threshold 0.35 cross",
            "Reversion from +/-0.60", "Positive/negative acceleration",
            "Two-bar directional persistence"
        };
        public static int RequiredBars(int period)
        {
            if(period<MinPeriod||period>MaxPeriod)
                throw new ArgumentOutOfRangeException("period");
            return 3*period+22;
        }
        public static string Name(int type)
        {
            if(type<0||type>=Count)
                throw new ArgumentOutOfRangeException("type");
            return FamilyNames[type/Rules]+" / "+RuleNames[type%Rules];
        }
        private static bool Finite(double v)
        { return !Double.IsNaN(v)&&!Double.IsInfinity(v); }
        private static double AverageClose(IList<NQBarV11> b,int at,int n)
        {
            double x=0;for(int i=at-n+1;i<=at;i++)x+=b[i].Close;
            return x/n;
        }
        private static double EmaClose(IList<NQBarV11> b,int at,int n,int period)
        {
            // Fixed-length warm-up relative to each completed sample; not
            // a NinjaTrader EMA parity claim.
            int start=at-(3*period+5);
            if(start<0)start=0;
            double x=b[start].Close,k=2.0/(n+1);
            for(int i=start+1;i<=at;i++)x+=k*(b[i].Close-x);
            return x;
        }
        private static double Atr(IList<NQBarV11> b,int at,int n)
        {
            double x=0;
            for(int i=at-n+1;i<=at;i++)
            {
                double prev=i==0?b[i].Close:b[i-1].Close;
                x+=Math.Max(b[i].High-b[i].Low,
                    Math.Max(Math.Abs(b[i].High-prev),Math.Abs(b[i].Low-prev)));
            }
            return x/n;
        }
        private static double Typical(NQBarV11 b)
        { return (b.High+b.Low+b.Close)/3.0; }
        private static double Feature(IList<NQBarV11> b,int at,int f,int n)
        {
            double close=b[at].Close;
            double atr=Math.Max(Atr(b,at,n),1e-12);
            if(f==0)return (close-AverageClose(b,at,n))/atr;
            if(f==1)return (close-EmaClose(b,at,n,n))/atr;
            if(f==2)return (AverageClose(b,at,n)-EmaClose(b,at,2*n,n))/atr;
            if(f==3)
            {
                double num=0,den=n*(n+1)*0.5;
                for(int j=0;j<n;j++)num+=(n-j)*b[at-j].Close;
                return (close-num/den)/atr;
            }
            if(f==4)
            {
                // Wilder RSI with 3*n rolling differences, centered [-1,+1].
                int start=at-3*n;
                double gain=0,loss=0;
                for(int i=start+1;i<=start+n;i++)
                {
                    double diff=b[i].Close-b[i-1].Close;
                    gain+=Math.Max(diff,0);loss+=Math.Max(-diff,0);
                }
                gain/=n;loss/=n;
                for(int i=start+n+1;i<=at;i++)
                {
                    double diff=b[i].Close-b[i-1].Close;
                    gain=(gain*(n-1)+Math.Max(diff,0))/n;
                    loss=(loss*(n-1)+Math.Max(-diff,0))/n;
                }
                if(gain+loss<1e-12)return 0;
                return (gain-loss)/(gain+loss);
            }
            if(f==5)
            {
                double mean=0;
                for(int i=at-n+1;i<=at;i++)mean+=Typical(b[i]);
                mean/=n;
                double dev=0;
                for(int i=at-n+1;i<=at;i++)
                    dev+=Math.Abs(Typical(b[i])-mean);
                dev/=n;
                return dev<1e-12?0:(Typical(b[at])-mean)/(0.015*dev*150);
            }
            if(f==6)
                return (close-b[at-n].Close)/(atr*Math.Sqrt(n));
            if(f==7)
            {
                double hi=Double.NegativeInfinity,lo=Double.PositiveInfinity;
                for(int i=at-n+1;i<=at;i++)
                {hi=Math.Max(hi,b[i].High);lo=Math.Min(lo,b[i].Low);}
                return hi-lo<1e-12?0:2*(close-lo)/(hi-lo)-1;
            }
            if(f==8)
                return (EmaClose(b,at,n,n)-EmaClose(b,at,2*n,n))/atr;
            if(f==9)
            {
                double avg=AverageClose(b,at,n),v=0;
                for(int i=at-n+1;i<=at;i++)
                    v+=Math.Pow(b[i].Close-avg,2);
                double sd=Math.Sqrt(v/n);
                return sd<1e-12?0:(close-avg)/(2*sd);
            }
            if(f==10)
            {
                double plus=0,minus=0;
                for(int i=at-n+1;i<=at;i++)
                {
                    double prev=Typical(b[i-1]),cur=Typical(b[i]);
                    double flow=cur*b[i].Volume;
                    if(cur>prev)plus+=flow;
                    if(cur<prev)minus+=flow;
                }
                return plus+minus<1e-12?0:(plus-minus)/(plus+minus);
            }
            if(f==11)
            {
                double num=0,den=0;
                for(int i=at-n+1;i<=at;i++)
                {
                    double range=b[i].High-b[i].Low;
                    double clv=range<1e-12?0:
                        (2*b[i].Close-b[i].High-b[i].Low)/range;
                    num+=clv*b[i].Volume;den+=b[i].Volume;
                }
                return den<1e-12?0:num/den;
            }
            throw new ArgumentOutOfRangeException("family");
        }

        public static bool TryEvaluate(IList<NQBarV11> bars,int type,int period,
                                       out bool bull,out bool bear)
        {
            bull=false;bear=false;
            if(bars==null||type<0||type>=Count||
               period<MinPeriod||period>MaxPeriod||
               bars.Count<RequiredBars(period))
                return false;
            int f=type/Rules,rule=type%Rules,at=bars.Count-1;
            double x=Feature(bars,at,f,period);
            double y=Feature(bars,at-1,f,period);
            double z=Feature(bars,at-2,f,period);
            if(!Finite(x)||!Finite(y)||!Finite(z))return false;
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
                    bull=y<=0.15&&x>0.15;bear=y>=-0.15&&x< -0.15;break;
                case 7:
                    bull=y<=0.35&&x>0.35;bear=y>=-0.35&&x< -0.35;break;
                case 8:
                    bull=y< -0.60&&x>=-0.60;bear=y>0.60&&x<=0.60;break;
                case 9:
                    bull=x-2*y+z>1e-9;bear=x-2*y+z< -1e-9;break;
                case 10:
                    bull=x>0&&y>0;bear=x<0&&y<0;break;
            }
            return true;
        }
    }
}
