// V19 families 78..98: channels, volatility estimators, stop bands
// and dispersion regimes. Volatility-only measurements are assigned
// direction using observed close returns: no implied future direction.
using System;
using System.Collections.Generic;
using M = NinjaTrader.NinjaScript.Strategies.NQFeatureMathV19;

namespace NinjaTrader.NinjaScript.Strategies
{
    internal static class NQVolatilityFeaturesV19
    {
        private static double LogReturn(IList<NQBarV11> b,int at)
        {return Math.Log(b[at].Close/b[at-1].Close);}
        private static double StdLog(IList<NQBarV11> b,int at,int n)
        {
            double mean=0,s=0;
            for(int k=at-n+1;k<=at;k++)mean+=LogReturn(b,k);
            mean/=n;
            for(int k=at-n+1;k<=at;k++)
            {
                double d=LogReturn(b,k)-mean;s+=d*d;
            }
            return Math.Sqrt(s/n);
        }
        private static double Parkinson(IList<NQBarV11> b,int at,int n)
        {
            double v=0;
            for(int k=at-n+1;k<=at;k++)
            {
                double x=Math.Log(b[k].High/b[k].Low);
                v+=x*x;
            }
            return Math.Sqrt(v/(4*n*Math.Log(2)));
        }
        private static double GarmanKlass(IList<NQBarV11> b,int at,int n)
        {
            double v=0;
            for(int k=at-n+1;k<=at;k++)
            {
                double hl=Math.Log(b[k].High/b[k].Low),
                    co=Math.Log(b[k].Close/b[k].Open);
                v+=0.5*hl*hl-(2*Math.Log(2)-1)*co*co;
            }
            return Math.Sqrt(Math.Max(0,v/n));
        }
        private static double RogersSatchell(IList<NQBarV11> b,int at,int n)
        {
            double v=0;
            for(int k=at-n+1;k<=at;k++)
            {
                var c=b[k];
                v+=Math.Log(c.High/c.Close)*Math.Log(c.High/c.Open)+
                    Math.Log(c.Low/c.Close)*Math.Log(c.Low/c.Open);
            }
            return Math.Sqrt(Math.Max(0,v/n));
        }
        private static double YangZhang(IList<NQBarV11> b,int at,int n)
        {
            double meanOvernight=0,meanDay=0,overnight=0,day=0,rs=0;
            for(int k=at-n+1;k<=at;k++)
            {
                meanOvernight+=Math.Log(b[k].Open/b[k-1].Close);
                meanDay+=Math.Log(b[k].Close/b[k].Open);
            }
            meanOvernight/=n;meanDay/=n;
            for(int k=at-n+1;k<=at;k++)
            {
                double o=Math.Log(b[k].Open/b[k-1].Close)-meanOvernight;
                double d=Math.Log(b[k].Close/b[k].Open)-meanDay;
                overnight+=o*o;day+=d*d;
                var c=b[k];
                rs+=Math.Log(c.High/c.Close)*Math.Log(c.High/c.Open)+
                    Math.Log(c.Low/c.Close)*Math.Log(c.Low/c.Open);
            }
            double w=0.34/(1.34+(n+1.0)/Math.Max(1,n-1));
            return Math.Sqrt(Math.Max(0,
                overnight/n+w*day/n+(1-w)*rs/n));
        }
        public static double Compute(IList<NQBarV11> b,int at,int n,int f)
        {
            double p=b[at].Close,atr=M.ATR(b,at,n);
            double trend=M.Div(p-b[at-n].Close,n*atr);
            int h=Math.Max(2,n/2),start=at-n+1;
            switch(f)
            {
                case 78: // Keltner breakout beyond EMA +/- 1.5 ATR
                {
                    double deviation=M.Div(p-M.EMA(b,at,n),atr);
                    return Math.Sign(deviation)*
                        Math.Max(0,Math.Abs(deviation)-1.5);
                }
                case 79: // Donchian centerline slope, price units / ATR
                {
                    double old=(M.Highest(b,at-n/2,n,2)+
                        M.Lowest(b,at-n/2,n,3))/2;
                    double now=(M.Highest(b,at,n,2)+
                        M.Lowest(b,at,n,3))/2;
                    return (now-old)/atr;
                }
                case 80: // breakout beyond prior n bars, no current bar
                {
                    double hi=M.Highest(b,at-1,n,2),
                        lo=M.Lowest(b,at-1,n,3);
                    if(p>hi)return (p-hi)/atr;
                    if(p<lo)return (p-lo)/atr;
                    return 0;
                }
                case 81: // close - Donchian high/low midpoint
                    return (p-(M.Highest(b,at,n,2)+
                        M.Lowest(b,at,n,3))/2)/atr;
                case 82: // adaptive ATR band angle / smoothed center
                {
                    double w=atr/M.ATR(b,at-1,n);
                    return M.Div(M.EMA(b,at,n)-M.EMA(b,at-1,n),
                        atr)*w;
                }
                case 83: // Bollinger bandwidth regime weighted by trend
                    return trend*M.Div(4*M.Std(b,at,n),p);
                case 84: // signed change in realized price deviation
                    return M.Direction(b,at,h)*
                        (M.Std(b,at,n)-M.Std(b,at-1,n))/atr;
                case 85: // realized log-volatility expansion
                    return M.Direction(b,at,h)*
                        M.Div(StdLog(b,at,n)-StdLog(b,at-1,n),
                              Math.Max(StdLog(b,at-1,n),M.Eps));
                case 86: // normalized ATR change in price-normalized units
                    return M.Direction(b,at,h)*
                        (atr/p-M.ATR(b,at-1,n)/b[at-1].Close);
                case 87: // Parkinson high-low volatility signed by trend
                    return Math.Sign(trend)*Parkinson(b,at,n);
                case 88: // Garman-Klass OHLC volatility signed by trend
                    return Math.Sign(trend)*GarmanKlass(b,at,n);
                case 89: // Rogers-Satchell stochastic OHLC volatility
                    return Math.Sign(trend)*RogersSatchell(b,at,n);
                case 90: // Yang-Zhang overnight + intrabar volatility
                    return Math.Sign(trend)*YangZhang(b,at,n);
                case 91: // Chaikin volatility of EMA high-low spread
                {
                    double current=M.EMA(b,at,n,9);
                    double old=M.EMA(b,at-h,n,9);
                    return M.Direction(b,at,h)*M.Div(current-old,old);
                }
                case 92: // downside ulcer drawdown scaled by trend
                {
                    double ulcer=0;
                    for(int k=start;k<=at;k++)
                    {
                        double hi=M.Highest(b,k,Math.Min(n,k+1),0);
                        double dd=M.Div(b[k].Close-hi,hi);
                        ulcer+=dd*dd;
                    }
                    return M.Div(trend,
                        Math.Max(Math.Sqrt(ulcer/n),M.Eps));
                }
                case 93: // Chande-Kroll protective channel distance
                {
                    double hi=M.Highest(b,at,n,2)-2*atr;
                    double lo=M.Lowest(b,at,n,3)+2*atr;
                    return (p-(hi+lo)/2)/atr;
                }
                case 94: // Supertrend stop-band signed close distance
                {
                    // Sequential prior bands; never shift a band forward.
                    double lower=Double.NaN,upper=Double.NaN;
                    bool up=true;
                    for(int k=at-2*n+1;k<=at;k++)
                    {
                        double local=M.ATR(b,k,Math.Min(n,k));
                        double mid=(b[k].High+b[k].Low)/2;
                        double lo=mid-2*local,hi=mid+2*local;
                        if(Double.IsNaN(lower)){lower=lo;upper=hi;}
                        else
                        {
                            if(b[k-1].Close>upper)up=true;
                            if(b[k-1].Close<lower)up=false;
                            lower=b[k-1].Close>lower?
                                Math.Max(lower,lo):lo;
                            upper=b[k-1].Close<upper?
                                Math.Min(upper,hi):hi;
                        }
                    }
                    return up?(p-lower)/atr:(p-upper)/atr;
                }
                case 95: // Ichimoku tenkan versus kijun CURRENT lines
                {
                    double tenkan=(M.Highest(b,at,h,2)+
                        M.Lowest(b,at,h,3))/2;
                    double kijun=(M.Highest(b,at,n,2)+
                        M.Lowest(b,at,n,3))/2;
                    return (tenkan-kijun)/atr;
                }
                case 96: // Ichimoku non-forward projected cloud spread
                {
                    double tenkan=(M.Highest(b,at,h,2)+
                        M.Lowest(b,at,h,3))/2,
                        kijun=(M.Highest(b,at,n,2)+
                        M.Lowest(b,at,n,3))/2,
                        spanA=(tenkan+kijun)/2,
                        spanB=(M.Highest(b,at,2*n,2)+
                        M.Lowest(b,at,2*n,3))/2;
                    return (spanA-spanB)/atr;
                }
                case 97: // DeMark-style pivot from prior completed n window
                {
                    double high=M.Highest(b,at-1,n,2),
                        low=M.Lowest(b,at-1,n,3),
                        close=b[at-1].Close,open=b[at-1].Open;
                    double x=close<open?high+2*low+close:
                        close>open?2*high+low+close:
                        high+low+2*close;
                    return (p-x/4)/atr;
                }
                case 98: // Bollinger-vs-Keltner squeeze directional momentum
                {
                    double band=2*M.Std(b,at,n);
                    double channel=1.5*atr;
                    double ratio=M.Div(band,channel);
                    return trend*(ratio<1?1.0/Math.Max(0.1,ratio):
                        Math.Min(ratio,5));
                }
            }
            throw new ArgumentOutOfRangeException("family");
        }
    }
}
