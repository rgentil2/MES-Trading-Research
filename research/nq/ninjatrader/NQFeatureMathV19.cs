// V19 common transparent M1 indicator mathematics.
// All observations <= completed signal bar "at". No future indexing.
// Degenerate inputs produce 0 instead of NaN/Infinity.
// Normalizations are research-specific, NOT NT8 vendor indicator parity.
using System;
using System.Collections.Generic;

namespace NinjaTrader.NinjaScript.Strategies
{
    internal static class NQFeatureMathV19
    {
        internal const double Eps=1e-12;
        internal static double Div(double a,double b)
        {return Math.Abs(b)<Eps?0:a/b;}
        internal static double Clip(double a,double lo,double hi)
        {return Math.Min(hi,Math.Max(lo,a));}
        internal static double Price(NQBarV11 b,int kind)
        {
            switch(kind)
            {
                case 0:return b.Close;
                case 1:return b.Open;
                case 2:return b.High;
                case 3:return b.Low;
                case 4:return b.Volume;
                case 5:return (b.High+b.Low+b.Close)/3;
                case 6:return (b.High+b.Low)/2;
                case 7:return (b.High+b.Low+2*b.Close)/4;
                case 8:return b.Close-b.Open;
                case 9:return b.High-b.Low;
                default:throw new ArgumentOutOfRangeException("kind");
            }
        }
        internal static double P(IList<NQBarV11> b,int at,int kind=0)
        {return Price(b[at],kind);}
        internal static double SMA(IList<NQBarV11> b,int at,int n,int kind=0)
        {
            double s=0;for(int k=at-n+1;k<=at;k++)s+=P(b,k,kind);
            return s/n;
        }
        internal static double WMA(IList<NQBarV11> b,int at,int n,int kind=0)
        {
            double s=0,den=n*(n+1)/2.0;
            for(int j=0;j<n;j++)s+=(n-j)*P(b,at-j,kind);
            return s/den;
        }
        internal static double EMA(IList<NQBarV11> b,int at,int n,int kind=0)
        {
            int from=Math.Max(0,at-3*n-5);
            double alpha=2.0/(n+1),x=P(b,from,kind);
            for(int k=from+1;k<=at;k++)
                x+=alpha*(P(b,k,kind)-x);
            return x;
        }
        internal static double SMMA(IList<NQBarV11> b,int at,int n,int kind=0)
        {
            int from=Math.Max(0,at-3*n-5);
            double x=P(b,from,kind);
            for(int k=from+1;k<=at;k++)
                x+=(P(b,k,kind)-x)/n;
            return x;
        }
        internal static double TR(IList<NQBarV11> b,int at)
        {
            var c=b[at];double p=b[Math.Max(0,at-1)].Close;
            return Math.Max(c.High-c.Low,Math.Max(
                Math.Abs(c.High-p),Math.Abs(c.Low-p)));
        }
        internal static double ATR(IList<NQBarV11> b,int at,int n)
        {
            double s=0;
            for(int k=at-n+1;k<=at;k++)s+=TR(b,k);
            return Math.Max(s/n,Eps);
        }
        internal static double Highest(IList<NQBarV11> b,int at,int n,
                                       int kind)
        {
            double x=Double.NegativeInfinity;
            for(int k=at-n+1;k<=at;k++)x=Math.Max(x,P(b,k,kind));
            return x;
        }
        internal static double Lowest(IList<NQBarV11> b,int at,int n,
                                      int kind)
        {
            double x=Double.PositiveInfinity;
            for(int k=at-n+1;k<=at;k++)x=Math.Min(x,P(b,k,kind));
            return x;
        }
        internal static double Std(IList<NQBarV11> b,int at,int n,
                                   int kind=0)
        {
            double mean=SMA(b,at,n,kind),s=0;
            for(int k=at-n+1;k<=at;k++)
            {
                double d=P(b,k,kind)-mean;
                s+=d*d;
            }
            return Math.Sqrt(s/n);
        }
        internal static double SumVolume(IList<NQBarV11> b,int at,int n)
        {
            double s=0;for(int k=at-n+1;k<=at;k++)s+=b[k].Volume;
            return s;
        }
        internal static double Direction(IList<NQBarV11> b,int at,int lag)
        {return Math.Sign(b[at].Close-b[at-lag].Close);}
        internal static double ROC(IList<NQBarV11> b,int at,int lag,
                                   int kind=0)
        {return Div(P(b,at,kind)-P(b,at-lag,kind),P(b,at-lag,kind));}
        internal static double Momentum(IList<NQBarV11> b,int at,int lag)
        {return b[at].Close-b[at-lag].Close;}
        internal static double RSI(IList<NQBarV11> b,int at,int n,
                                  int kind=0)
        {
            double gain=0,loss=0;
            for(int k=at-n+1;k<=at;k++)
            {
                double diff=P(b,k,kind)-P(b,k-1,kind);
                gain+=Math.Max(0,diff);loss+=Math.Max(0,-diff);
            }
            return Div(gain-loss,gain+loss);
        }
        internal static double Efficiency(IList<NQBarV11> b,int at,int n)
        {
            double sum=0;
            for(int k=at-n+1;k<=at;k++)
                sum+=Math.Abs(b[k].Close-b[k-1].Close);
            return Div(b[at].Close-b[at-n].Close,sum);
        }
        internal static double LinSlope(IList<NQBarV11> b,int at,int n,
                                        int kind=0)
        {
            double mean=(n-1)/2.0,mu=SMA(b,at,n,kind);
            double num=0,den=0;
            for(int j=0;j<n;j++)
            {
                double x=j-mean;
                num+=x*(P(b,at-n+1+j,kind)-mu);
                den+=x*x;
            }
            return Div(num,den);
        }
        internal static double Fit(IList<NQBarV11> b,int at,int n,
                                   int kind=0)
        {return SMA(b,at,n,kind)+LinSlope(b,at,n,kind)*(n-1)/2.0;}
        internal static double Clv(NQBarV11 b)
        {return Div(2*b.Close-b.High-b.Low,b.High-b.Low);}
        internal static double Typical(NQBarV11 b)
        {return (b.High+b.Low+b.Close)/3.0;}
        internal static double Vwap(IList<NQBarV11> b,int at,int n)
        {
            double a=0,v=0;
            for(int k=at-n+1;k<=at;k++)
            {
                v+=b[k].Volume;a+=Typical(b[k])*b[k].Volume;
            }
            return v>0?a/v:b[at].Close;
        }
        internal static double EmaSeries(int from,int to,int n,
                                          Func<int,double> value)
        {
            double a=2.0/(n+1),s=value(from);
            for(int k=from+1;k<=to;k++)
                s+=a*(value(k)-s);
            return s;
        }
    }
}
