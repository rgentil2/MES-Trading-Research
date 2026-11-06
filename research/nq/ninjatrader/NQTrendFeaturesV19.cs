// V19 families 36..56: distinct trend, smoothers, regression, adaptive MA.
// These are research implementations using only past completed OHLCV.
// They are NOT claimed to match NT8 vendor warmups/parameters bit-for-bit.
using System;
using System.Collections.Generic;
using M = NinjaTrader.NinjaScript.Strategies.NQFeatureMathV19;

namespace NinjaTrader.NinjaScript.Strategies
{
    internal static class NQTrendFeaturesV19
    {
        public static double Compute(IList<NQBarV11> b,int at,int n,int f)
        {
            double p=b[at].Close,atr=M.ATR(b,at,n);
            int half=Math.Max(2,n/2),slow=Math.Max(3,2*n);
            switch(f)
            {
                case 36: // fast / slow simple-average spread
                    return (M.SMA(b,at,half)-M.SMA(b,at,n))/atr;
                case 37: // dual EMA spread
                    return (M.EMA(b,at,half)-M.EMA(b,at,n))/atr;
                case 38: // dual WMA spread
                    return (M.WMA(b,at,half)-M.WMA(b,at,n))/atr;
                case 39: // Wilder smoothed close displacement
                    return (p-M.SMMA(b,at,n))/atr;
                case 40: // Wilder smoother slope
                    return (M.SMMA(b,at,n)-M.SMMA(b,at-1,n))/atr;
                case 41: // residual relative to least-squares fit at t
                    return (p-M.Fit(b,at,n))/atr;
                case 42: // signed regression fit quality, R-squared
                {
                    double mu=M.SMA(b,at,n),ssT=0,ssE=0;
                    double slope=M.LinSlope(b,at,n);
                    for(int j=0;j<n;j++)
                    {
                        double obs=b[at-n+1+j].Close;
                        double pred=mu+slope*(j-(n-1)/2.0);
                        ssT+=(obs-mu)*(obs-mu);
                        ssE+=(obs-pred)*(obs-pred);
                    }
                    return Math.Sign(slope)*M.Clip(1-M.Div(ssE,ssT),0,1);
                }
                case 43: // change in linear-regression slope
                    return (M.LinSlope(b,at,n)-
                            M.LinSlope(b,at-n/2,n))/atr;
                case 44: // KAMA recursive smoothed trend displacement
                {
                    int from=at-2*n;
                    double kama=b[from].Close;
                    for(int k=from+1;k<=at;k++)
                    {
                        int t=Math.Max(from,k-n),diffs=0;
                        double travel=0;
                        for(int j=t+1;j<=k;j++)
                        {
                            travel+=Math.Abs(b[j].Close-b[j-1].Close);
                            diffs++;
                        }
                        double er=diffs==0?0:
                            Math.Abs(M.Div(b[k].Close-b[t].Close,travel));
                        double a=Math.Pow(er*(2.0/3-2.0/31)+2.0/31,2);
                        kama+=a*(b[k].Close-kama);
                    }
                    return (p-kama)/atr;
                }
                case 45: // FRAMA fractal adaptive EMA
                {
                    double frama=b[at-2*n].Close;
                    int h=Math.Max(2,n/2);
                    for(int k=at-2*n+1;k<=at;k++)
                    {
                        if(k<n)continue;
                        double hi1=M.Highest(b,k,h,2),
                               lo1=M.Lowest(b,k,h,3),
                               hi2=M.Highest(b,k-h,h,2),
                               lo2=M.Lowest(b,k-h,h,3),
                               hi=M.Highest(b,k,2*h,2),
                               lo=M.Lowest(b,k,2*h,3);
                        double d1=(hi1-lo1)/h,d2=(hi2-lo2)/h,
                               d3=(hi-lo)/(2.0*h);
                        double dimension=d1+d2<=M.Eps||d3<=M.Eps?
                            1:Math.Log((d1+d2)/d3)/Math.Log(2);
                        double alpha=M.Clip(Math.Exp(-4.6*
                            (dimension-1)),0.01,1);
                        frama+=alpha*(b[k].Close-frama);
                    }
                    return (p-frama)/atr;
                }
                case 46: // McGinley Dynamic adaptivity using price ratio
                {
                    double dynamic=b[at-2*n].Close;
                    for(int k=at-2*n+1;k<=at;k++)
                    {
                        double ratio=M.Div(b[k].Close,dynamic);
                        double denom=n*Math.Pow(M.Clip(ratio,0.5,2),4);
                        dynamic+=M.Div(b[k].Close-dynamic,
                            Math.Max(1,denom));
                    }
                    return (p-dynamic)/atr;
                }
                case 47: // Tillson T3, six EMA cascades, fixed vfactor=.7
                {
                    double alpha=2.0/(n+1),v=0.7;
                    double e1=b[at-3*n].Close,e2=e1,e3=e1,
                        e4=e1,e5=e1,e6=e1;
                    for(int k=at-3*n+1;k<=at;k++)
                    {
                        e1+=alpha*(b[k].Close-e1);
                        e2+=alpha*(e1-e2);e3+=alpha*(e2-e3);
                        e4+=alpha*(e3-e4);e5+=alpha*(e4-e5);
                        e6+=alpha*(e5-e6);
                    }
                    double c1=-v*v*v,c2=3*v*v+3*v*v*v;
                    double c3=-6*v*v-3*v-3*v*v*v;
                    double c4=1+3*v+3*v*v+v*v*v;
                    return (p-(c1*e6+c2*e5+c3*e4+c4*e3))/atr;
                }
                case 48: // double smoothed SMA, triangular moving average
                {
                    int a=(n+1)/2,c=n-a+1;
                    double sum=0;
                    for(int i=0;i<c;i++)
                        sum+=M.SMA(b,at-i,a);
                    return (p-sum/c)/atr;
                }
                case 49: // median (high+low)/2 EMA displacement
                    return (p-M.EMA(b,at,n,6))/atr;
                case 50: // typical (high+low+close)/3 EMA displacement
                    return (p-M.EMA(b,at,n,5))/atr;
                case 51: // weighted-close (H+L+2C)/4 EMA displacement
                    return (p-M.EMA(b,at,n,7))/atr;
                case 52: // typical price versus SMA of typical prices
                    return (M.P(b,at,5)-M.SMA(b,at,n,5))/atr;
                case 53: // sine weighted moving-average displacement
                {
                    double sum=0,den=0;
                    for(int j=0;j<n;j++)
                    {
                        double w=Math.Sin(Math.PI*(n-j)/(n+1));
                        sum+=w*b[at-j].Close;den+=w;
                    }
                    return (p-M.Div(sum,den))/atr;
                }
                case 54: // VIDYA via magnitude of Chande momentum
                {
                    double vidya=b[at-2*n].Close;
                    for(int k=at-2*n+1;k<=at;k++)
                    {
                        int look=Math.Min(n,k-(at-2*n));
                        double gain=0,loss=0;
                        for(int j=k-look+1;j<=k;j++)
                        {
                            double d=b[j].Close-b[j-1].Close;
                            gain+=Math.Max(0,d);loss+=Math.Max(0,-d);
                        }
                        double cmo=Math.Abs(M.Div(gain-loss,gain+loss));
                        vidya+=2.0/(n+1)*cmo*(b[k].Close-vidya);
                    }
                    return (p-vidya)/atr;
                }
                case 55: // Zero-lag LSMA: 2*LSMA(n)-LSMA(n) lagged half
                    return (p-(2*M.Fit(b,at,n)-
                        M.Fit(b,at-half,n)))/atr;
                case 56: // EMA-smoothed momentum, n-lag
                {
                    int start=at-2*n,lag=Math.Max(2,n/2);
                    double alpha=2.0/(n+1);
                    double m=b[start].Close-b[start-lag].Close;
                    for(int k=start+1;k<=at;k++)
                        m+=alpha*((b[k].Close-b[k-lag].Close)-m);
                    return m/atr;
                }
            }
            throw new ArgumentOutOfRangeException("family");
        }
    }
}
