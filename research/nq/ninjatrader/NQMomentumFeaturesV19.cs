// V19 families 57..77: momentum, cycle and oscillator formulas.
// Fixed lookbacks and causal smoothing; return dimensionless signed
// values for existing 11 directional signal predicates.
using System;
using System.Collections.Generic;
using M = NinjaTrader.NinjaScript.Strategies.NQFeatureMathV19;

namespace NinjaTrader.NinjaScript.Strategies
{
    internal static class NQMomentumFeaturesV19
    {
        private static double Stoch(IList<NQBarV11> b,int at,int n)
        {
            double hi=M.Highest(b,at,n,2),
                   lo=M.Lowest(b,at,n,3);
            return M.Div(2*b[at].Close-hi-lo,hi-lo);
        }
        private static double MACD(IList<NQBarV11> b,int at,int n)
        {return M.EMA(b,at,Math.Max(2,n/2))-
                M.EMA(b,at,Math.Max(3,2*n));}
        private static double TRIX(IList<NQBarV11> b,int at,int n)
        {
            int from=Math.Max(0,at-3*n-4);
            double alpha=2.0/(n+1),e1=b[from].Close,e2=e1,e3=e2,
                   prior=e3;
            for(int k=from+1;k<=at;k++)
            {
                prior=e3;
                e1+=alpha*(b[k].Close-e1);
                e2+=alpha*(e1-e2);
                e3+=alpha*(e2-e3);
            }
            return M.Div(e3-prior,Math.Abs(e3));
        }
        private static double SMI(IList<NQBarV11> b,int at,int n)
        {
            int from=at-n+1;
            double alpha=2.0/(Math.Max(2,n/2)+1);
            double d=0,r=0,d2=0,r2=0;
            for(int k=from;k<=at;k++)
            {
                int look=Math.Min(n,k+1);
                double hi=M.Highest(b,k,look,2),
                       lo=M.Lowest(b,k,look,3);
                double x=b[k].Close-(hi+lo)/2;
                double half=(hi-lo)/2;
                if(k==from){d=x;r=half;d2=d;r2=r;}
                else
                {
                    d+=alpha*(x-d);r+=alpha*(half-r);
                    d2+=alpha*(d-d2);r2+=alpha*(r-r2);
                }
            }
            return M.Div(d2,r2);
        }
        public static double Compute(IList<NQBarV11> b,int at,int n,int f)
        {
            double p=b[at].Close,atr=M.ATR(b,at,n);
            int half=Math.Max(2,n/2),start=at-n+1;
            switch(f)
            {
                case 57: // Williams accumulation/distribution (WAD)
                {
                    double ad=0,scale=0;
                    for(int k=start;k<=at;k++)
                    {
                        double prev=b[k-1].Close;
                        double reference=b[k].Close>prev?
                            Math.Min(b[k].Low,prev):
                            b[k].Close<prev?Math.Max(b[k].High,prev):
                            b[k].Close;
                        ad+=b[k].Close-reference;
                        scale+=M.TR(b,k);
                    }
                    return M.Div(ad,scale);
                }
                case 58: // Ultimate oscillator with 7/14/28 scaled by n
                {
                    double value=0;
                    for(int group=0;group<3;group++)
                    {
                        int lag=group==0?half:group==1?n:2*n;
                        double bp=0,tr=0;
                        for(int k=at-lag+1;k<=at;k++)
                        {
                            double prev=b[k-1].Close;
                            bp+=b[k].Close-Math.Min(b[k].Low,prev);
                            tr+=Math.Max(b[k].High,prev)-
                                Math.Min(b[k].Low,prev);
                        }
                        value+=(group==0?4:group==1?2:1)*
                            M.Div(bp,tr);
                    }
                    return 2*value/7-1;
                }
                case 59: // stochastic RSI with rolling RSI extrema
                {
                    double lo=Double.PositiveInfinity,hi=Double.NegativeInfinity;
                    for(int k=start;k<=at;k++)
                    {
                        double x=M.RSI(b,k,n);
                        lo=Math.Min(lo,x);hi=Math.Max(hi,x);
                    }
                    return M.Div(2*M.RSI(b,at,n)-hi-lo,hi-lo);
                }
                case 60: // Connors RSI: RSI3 + streak RSI2 + percent rank ROC1
                {
                    double streak=0,prev=0,gain=0,loss=0;
                    for(int k=at-n+1;k<=at;k++)
                    {
                        double diff=b[k].Close-b[k-1].Close;
                        streak=diff>0?Math.Max(1,streak+1):
                            diff<0?Math.Min(-1,streak-1):0;
                        if(k>start)
                        {
                            double d=streak-prev;
                            gain+=Math.Max(0,d);loss+=Math.Max(0,-d);
                        }
                        prev=streak;
                    }
                    double percent=0,current=M.ROC(b,at,1);
                    for(int k=start;k<=at;k++)
                        if(M.ROC(b,k,1)<current)percent++;
                    return (M.RSI(b,at,3)+M.Div(gain-loss,gain+loss)+
                        2*percent/n-1)/3;
                }
                case 61: // RMI: RSI based on lagged momentum, not one-bar
                {
                    double up=0,down=0;
                    for(int k=start;k<=at;k++)
                    {
                        double d=b[k].Close-b[k-half].Close;
                        up+=Math.Max(d,0);down+=Math.Max(-d,0);
                    }
                    return M.Div(up-down,up+down);
                }
                case 62: // Difference between short and long RSI, signed
                    return M.RSI(b,at,half)-M.RSI(b,at,n);
                case 63: // Percentage price oscillator
                    return M.Div(MACD(b,at,n),
                        M.EMA(b,at,2*n));
                case 64: // Percentage volume oscillator
                    return M.Div(M.EMA(b,at,half,4)-
                        M.EMA(b,at,n,4),M.EMA(b,at,n,4));
                case 65: // KST: 4 ROC averages at lag 1..4 × half
                {
                    double kst=0;
                    for(int level=1;level<=4;level++)
                    {
                        int lag=level*half;
                        double avg=0;
                        for(int j=0;j<half;j++)
                            avg+=M.ROC(b,at-j,lag);
                        kst+=level*avg/half;
                    }
                    return kst/10;
                }
                case 66: // KST first derivative (signal-line spread)
                {
                    double current=0,previous=0;
                    for(int level=1;level<=4;level++)
                    {
                        int lag=level*half;
                        double a=0,z=0;
                        for(int j=0;j<half;j++)
                        {
                            a+=M.ROC(b,at-j,lag);
                            z+=M.ROC(b,at-j-1,lag);
                        }
                        current+=level*a/half;
                        previous+=level*z/half;
                    }
                    return (current-previous)/10;
                }
                case 67: // TRIX momentum acceleration
                    return (TRIX(b,at,n)-TRIX(b,at-1,n))*100;
                case 68: // Inverse Fisher transform of RSI
                    return Math.Tanh(2.5*M.RSI(b,at,n));
                case 69: // STC-like double stochastic normalization MACD
                {
                    double lo=Double.PositiveInfinity,hi=Double.NegativeInfinity;
                    for(int k=start;k<=at;k++)
                    {
                        double m=MACD(b,k,n);
                        lo=Math.Min(lo,m);hi=Math.Max(hi,m);
                    }
                    double stoch=M.Div(MACD(b,at,n)-lo,hi-lo);
                    double mean=0;
                    for(int k=start;k<=at;k++)
                    {
                        double min=Double.PositiveInfinity,
                               max=Double.NegativeInfinity;
                        for(int j=Math.Max(start,k-half+1);j<=k;j++)
                        {
                            double v=MACD(b,j,n);
                            min=Math.Min(min,v);max=Math.Max(max,v);
                        }
                        mean+=M.Div(MACD(b,k,n)-min,max-min);
                    }
                    return 2*(0.5*stoch+0.5*mean/n)-1;
                }
                case 70: // Double-smoothed stochastic momentum index
                    return SMI(b,at,n);
                case 71: // Choppiness index with directional trend sign
                {
                    double sum=0;
                    for(int k=start;k<=at;k++)sum+=M.TR(b,k);
                    double range=M.Highest(b,at,n,2)-
                        M.Lowest(b,at,n,3);
                    double chop=range<=M.Eps?1:
                        M.Clip(Math.Log10(Math.Max(1,sum/range))/
                          Math.Log10(n),0,1);
                    return M.Direction(b,at,n)*(1-chop);
                }
                case 72: // CCI of typical price, EMA center versus SMA
                {
                    double t=M.P(b,at,5),mean=M.EMA(b,at,n,5),dev=0;
                    for(int k=start;k<=at;k++)
                        dev+=Math.Abs(M.P(b,k,5)-mean);
                    return M.Div(t-mean,0.015*dev/n*150);
                }
                case 73: // Ehlers center of gravity weighted-price oscillator
                {
                    double weighted=0,total=0;
                    for(int j=0;j<n;j++)
                    {
                        double x=b[at-j].Close;
                        weighted+=(n-j)*x;total+=x;
                    }
                    return 2*M.Div(weighted,total)/(n+1)-1;
                }
                case 74: // Laguerre RSI 4-filter, gamma 0.5
                {
                    double l0=b[at-n].Close,l1=l0,l2=l0,l3=l0;
                    for(int k=at-n+1;k<=at;k++)
                    {
                        double x=b[k].Close;
                        double a=l0,bb=l1,c=l2,d=l3;
                        l0=0.5*a+0.5*x;
                        l1=-0.5*l0+a+0.5*bb;
                        l2=-0.5*l1+bb+0.5*c;
                        l3=-0.5*l2+c+0.5*d;
                    }
                    double cu=Math.Max(0,l0-l1)+Math.Max(0,l1-l2)+
                        Math.Max(0,l2-l3);
                    double cd=Math.Max(0,l1-l0)+Math.Max(0,l2-l1)+
                        Math.Max(0,l3-l2);
                    return M.Div(cu-cd,cu+cd);
                }
                case 75: // Coppock: WMA of dual ROC
                {
                    double sum=0,weight=0;
                    for(int j=0;j<n;j++)
                    {
                        int k=at-j;double w=n-j;
                        sum+=w*(M.ROC(b,k,half)+M.ROC(b,k,n));
                        weight+=w;
                    }
                    return M.Div(sum,weight);
                }
                case 76: // Balance of Power, SMA normalized candle body/range
                {
                    double sum=0;
                    for(int k=start;k<=at;k++)
                        sum+=M.Div(b[k].Close-b[k].Open,
                                   b[k].High-b[k].Low);
                    return sum/n;
                }
                case 77: // Elder bull/bear power, full range above/below EMA
                {
                    double ema=M.EMA(b,at,n);
                    return (b[at].High+b[at].Low-2*ema)/(2*atr);
                }
            }
            throw new ArgumentOutOfRangeException("family");
        }
    }
}
