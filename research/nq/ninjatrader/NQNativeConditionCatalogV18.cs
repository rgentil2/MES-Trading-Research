// S0.79 V18 — 24 additional DISTINCT OHLCV formula families.
// Preserves exact V11 identifiers 0..131 and their original formulas.
// New IDs 132..395: family index 12..35, 11 SAME predicates per family.
// Thus 36 mathematical feature families and 396 directional conditions.
// This is NOT "396 independent indicators" and not NinjaTrader vendor
// indicator parity. Fixed finite warmup, completed M1 bars only.
// No volume order flow, quotes, bid/ask, ticks or future bars assumed.
using System;
using System.Collections.Generic;

namespace NinjaTrader.NinjaScript.Strategies
{
    public static class NQNativeConditionCatalogV18
    {
        public const int LegacyFamilies=12;
        public const int AddedFamilies=24;
        public const int Families=LegacyFamilies+AddedFamilies;
        public const int Rules=NQNativeConditionsV11.Rules;
        public const int Count=Families*Rules;
        public const int MinPeriod=NQNativeConditionsV11.MinPeriod;
        public const int MaxPeriod=NQNativeConditionsV11.MaxPeriod;

        public static readonly string[] AddedNames={
            "Least-squares price slope / ATR",                   // 12
            "Rolling VWAP displacement / ATR",                  // 13
            "Hull moving-average displacement / ATR",          // 14
            "Zero-lag EMA displacement / ATR",                  // 15
            "Double EMA displacement / ATR",                    // 16
            "Signed on-balance volume flow",                    // 17
            "Chaikin money flow",                               // 18
            "Accumulation/distribution line momentum",          // 19
            "Elder force-index / ATR and volume",               // 20
            "Ease-of-movement scaled pressure",                 // 21
            "Wilder directional movement +DI minus -DI",       // 22
            "Directional movement weighted by local DX (ADX proxy)",            // 23
            "Aroon oscillator",                                 // 24
            "Vortex oscillator",                                // 25
            "Signed Kaufman efficiency ratio",                 // 26
            "Chande momentum oscillator",                      // 27
            "True strength index",                              // 28
            "Triple exponential average rate-of-change",       // 29
            "Detrended price oscillator / ATR",                 // 30
            "MACD histogram / ATR",                             // 31
            "Volume price trend momentum / ATR",               // 32
            "Fisher transformed stochastic position",           // 33
            "Relative vigor index",                            // 34
            "Directional range-expansion impulse"              // 35
        };

        public static int RequiredBars(int period)
        {
            return NQNativeConditionsV11.RequiredBars(period);
        }
        public static string Name(int type)
        {
            if(type<0||type>=Count)
                throw new ArgumentOutOfRangeException("type");
            if(type<NQNativeConditionsV11.Count)
                return NQNativeConditionsV11.Name(type);
            return AddedNames[type/Rules-LegacyFamilies]+" / "+
                NQNativeConditionsV11.RuleNames[type%Rules];
        }
        private static bool Finite(double x)
        {return !Double.IsNaN(x)&&!Double.IsInfinity(x);}
        private static double Div(double n,double d)
        {return Math.Abs(d)<1e-12?0:n/d;}
        private static double TrueRange(IList<NQBarV11> b,int i)
        {
            double p=b[Math.Max(0,i-1)].Close;
            return Math.Max(b[i].High-b[i].Low,
                Math.Max(Math.Abs(b[i].High-p),Math.Abs(b[i].Low-p)));
        }
        private static double Atr(IList<NQBarV11> b,int at,int n)
        {
            double sum=0;
            for(int k=at-n+1;k<=at;k++)sum+=TrueRange(b,k);
            return Math.Max(sum/n,1e-12);
        }
        private static double Sma(IList<NQBarV11> b,int at,int n)
        {
            double a=0;
            for(int j=at-n+1;j<=at;j++)a+=b[j].Close;
            return a/n;
        }
        private static double Weighted(IList<NQBarV11> b,int at,int n)
        {
            double s=0,total=n*(n+1)/2.0;
            for(int j=0;j<n;j++)s+=(n-j)*b[at-j].Close;
            return s/total;
        }
        private static double EMA(IList<NQBarV11> b,int at,int n,
                                  Func<int,double> value)
        {
            int start=Math.Max(0,at-3*n-5);
            double mean=value(start),a=2.0/(n+1);
            for(int k=start+1;k<=at;k++)
                mean+=a*(value(k)-mean);
            return mean;
        }
        private static double Dema(IList<NQBarV11> b,int at,int n)
        {
            int start=Math.Max(0,at-3*n-5);
            double a=2.0/(n+1),e1=b[start].Close,e2=e1;
            for(int k=start+1;k<=at;k++)
            {
                e1+=a*(b[k].Close-e1);
                e2+=a*(e1-e2);
            }
            return 2*e1-e2;
        }
        private static double Hma(IList<NQBarV11> b,int at,int n)
        {
            int half=Math.Max(2,n/2),root=Math.Max(2,(int)Math.Sqrt(n));
            double sum=0,den=0;
            for(int j=0;j<root;j++)
            {
                int index=at-j;
                double v=2*Weighted(b,index,half)-Weighted(b,index,n);
                sum+=(root-j)*v;den+=root-j;
            }
            return sum/den;
        }
        private static double Clv(NQBarV11 b)
        {
            return Div(2*b.Close-b.High-b.Low,b.High-b.Low);
        }
        private static double RSIFlux(IList<NQBarV11> b,int at,int n,
                                      bool plus)
        {
            double s=0;
            for(int k=at-n+1;k<=at;k++)
            {
                double d=b[k].Close-b[k-1].Close;
                if(plus)s+=Math.Max(0,d);
                else s+=Math.Max(0,-d);
            }
            return s;
        }
        private static double Feature(IList<NQBarV11> b,int at,int family,int n)
        {
            double close=b[at].Close,atr=Atr(b,at,n);
            int start=at-n+1;
            switch(family)
            {
                case 12:
                {
                    // OLS slope normalized by mean true range, dimensionless.
                    double meanX=(n-1)*0.5,meanY=Sma(b,at,n);
                    double num=0,den=0;
                    for(int j=0;j<n;j++)
                    {
                        double x=j-meanX;
                        num+=x*(b[start+j].Close-meanY);den+=x*x;
                    }
                    return Div(num,den*atr);
                }
                case 13:
                {
                    double p=0,v=0;
                    for(int j=start;j<=at;j++)
                    {
                        double typical=(b[j].High+b[j].Low+b[j].Close)/3.0;
                        p+=typical*b[j].Volume;v+=b[j].Volume;
                    }
                    return v==0?0:(close-p/v)/atr;
                }
                case 14: return (close-Hma(b,at,n))/atr;
                case 15:
                {
                    int lag=Math.Max(1,(n-1)/2);
                    double z=EMA(b,at,n,k=>2*b[k].Close-
                        b[Math.Max(0,k-lag)].Close);
                    return (close-z)/atr;
                }
                case 16: return (close-Dema(b,at,n))/atr;
                case 17:
                {
                    double signed=0,volume=0;
                    for(int k=start;k<=at;k++)
                    {
                        signed+=Math.Sign(b[k].Close-b[k-1].Close)*
                            b[k].Volume;
                        volume+=b[k].Volume;
                    }
                    return Div(signed,volume);
                }
                case 18:
                {
                    double flow=0,v=0;
                    for(int k=start;k<=at;k++)
                    {
                        flow+=Clv(b[k])*b[k].Volume;
                        v+=b[k].Volume;
                    }
                    return Div(flow,v);
                }
                case 19:
                {
                    // ADL slope uses volume flow; unlike CMF it divides
                    // by a rolling mean volume, keeping direction.
                    double current=0,first=0,vol=0;
                    for(int k=start;k<=at;k++)
                    {
                        current+=Clv(b[k])*b[k].Volume;
                        vol+=b[k].Volume;
                        if(k==start)first=current;
                    }
                    return Div(current-first,vol);
                }
                case 20:
                {
                    double sum=0,volume=0;
                    for(int k=start;k<=at;k++)
                    {
                        sum+=(b[k].Close-b[k-1].Close)*b[k].Volume;
                        volume+=b[k].Volume;
                    }
                    return Div(sum,volume*atr);
                }
                case 21:
                {
                    // EOM: midpoint displacement per normalized volume
                    // and range. Zero volume is treated as neutral.
                    double meanV=0;
                    for(int k=start;k<=at;k++)meanV+=b[k].Volume;
                    meanV/=n;
                    double sum=0;
                    for(int k=start;k<=at;k++)
                    {
                        if(b[k].Volume<=0)continue;
                        double mid=(b[k].High+b[k].Low)/2;
                        double prev=(b[k-1].High+b[k-1].Low)/2;
                        sum+=(mid-prev)/atr*
                            (b[k].High-b[k].Low)/atr*
                            Div(meanV,b[k].Volume);
                    }
                    return sum/n;
                }
                case 22:
                case 23:
                {
                    double p=0,m=0,tr=0,dx=0;
                    for(int k=start;k<=at;k++)
                    {
                        double u=b[k].High-b[k-1].High;
                        double d=b[k-1].Low-b[k].Low;
                        p+=u>d && u>0?u:0;
                        m+=d>u && d>0?d:0;
                        tr+=TrueRange(b,k);
                    }
                    double dmi=Div(p-m,tr);
                    if(family==22)return dmi;
                    // Wilder/ADX-inspired finite window signed strength
                    // term: DX magnitude applied to prevailing DI sign.
                    for(int k=start;k<=at;k++)
                    {
                        double u=b[k].High-b[k-1].High;
                        double d=b[k-1].Low-b[k].Low;
                        dx+=Div(Math.Abs((u>d?Math.Max(0,u):0)-
                            (d>u?Math.Max(0,d):0)),
                            TrueRange(b,k));
                    }
                    return dmi*dx/n;
                }
                case 24:
                {
                    int hiAge=0,loAge=0;
                    double hi=Double.NegativeInfinity,
                           lo=Double.PositiveInfinity;
                    for(int j=0;j<n;j++)
                    {
                        int k=at-j;
                        if(b[k].High>hi){hi=b[k].High;hiAge=j;}
                        if(b[k].Low<lo){lo=b[k].Low;loAge=j;}
                    }
                    return (loAge-hiAge)/(double)n;
                }
                case 25:
                {
                    double plus=0,minus=0,tr=0;
                    for(int k=start;k<=at;k++)
                    {
                        plus+=Math.Abs(b[k].High-b[k-1].Low);
                        minus+=Math.Abs(b[k].Low-b[k-1].High);
                        tr+=TrueRange(b,k);
                    }
                    return Div(plus-minus,tr);
                }
                case 26:
                {
                    double changes=0;
                    for(int k=start;k<=at;k++)
                        changes+=Math.Abs(b[k].Close-b[k-1].Close);
                    return Div(close-b[at-n].Close,changes);
                }
                case 27:
                {
                    double gain=RSIFlux(b,at,n,true);
                    double loss=RSIFlux(b,at,n,false);
                    return Div(gain-loss,gain+loss);
                }
                case 28:
                {
                    // TSI from two cascaded EMA smoothings of momenta
                    // using the SAME n, denominator uses abs momentum.
                    int from=Math.Max(1,at-3*n-5);
                    double alpha=2.0/(n+1);
                    double s=b[from].Close-b[from-1].Close;
                    double a=Math.Abs(s),d=s,e=a;
                    for(int k=from+1;k<=at;k++)
                    {
                        double change=b[k].Close-b[k-1].Close;
                        s+=alpha*(change-s);
                        a+=alpha*(Math.Abs(change)-a);
                        d+=alpha*(s-d);
                        e+=alpha*(a-e);
                    }
                    return Div(d,e);
                }
                case 29:
                {
                    double alpha=2.0/(n+1);
                    int from=Math.Max(0,at-3*n-5);
                    double e1=b[from].Close,e2=e1,e3=e2,prior=e3;
                    for(int k=from+1;k<=at;k++)
                    {
                        prior=e3;
                        e1+=alpha*(b[k].Close-e1);
                        e2+=alpha*(e1-e2);
                        e3+=alpha*(e2-e3);
                    }
                    return Div(e3-prior,atr);
                }
                case 30:
                {
                    // DPO with a fixed n/2+1 retrospective lag;
                    // only historical closes, never centered/future bars.
                    int lag=n/2+1;
                    int k=at-lag;
                    return (b[k].Close-Sma(b,k,n))/atr;
                }
                case 31:
                {
                    // MACD histogram: EMA(n)-EMA(2n)-EMA(n) of their
                    // past MACD sequence; normalized by ATR.
                    double signal=0,a=2.0/(n+1);
                    int from=at-n+1;
                    for(int k=from;k<=at;k++)
                    {
                        double macd=EMA(b,k,n,j=>b[j].Close)-
                            EMA(b,k,2*n,j=>b[j].Close);
                        if(k==from)signal=macd;
                        else signal+=a*(macd-signal);
                    }
                    double last=EMA(b,at,n,k=>b[k].Close)-
                        EMA(b,at,2*n,k=>b[k].Close);
                    return (last-signal)/atr;
                }
                case 32:
                {
                    double pvt=0,normalized=0;
                    for(int k=start;k<=at;k++)
                    {
                        double change=Div(b[k].Close-b[k-1].Close,
                                          b[k-1].Close);
                        pvt+=change*b[k].Volume;
                        normalized+=b[k].Volume;
                    }
                    return Div(pvt*close,normalized*atr);
                }
                case 33:
                {
                    double hi=Double.NegativeInfinity,lo=Double.PositiveInfinity;
                    for(int k=start;k<=at;k++)
                    {
                        hi=Math.Max(hi,b[k].High);
                        lo=Math.Min(lo,b[k].Low);
                    }
                    double x=Div(2*close-hi-lo,hi-lo);
                    x=Math.Max(-0.98,Math.Min(0.98,x));
                    return Math.Log((1+x)/(1-x))/2.0;
                }
                case 34:
                {
                    double num=0,den=0;
                    for(int k=start;k<=at;k++)
                    {
                        num+=b[k].Close-b[k].Open;
                        den+=b[k].High-b[k].Low;
                    }
                    return Div(num,den);
                }
                case 35:
                {
                    double expansion=0,direction=0;
                    for(int k=start;k<=at;k++)
                    {
                        double range=b[k].High-b[k].Low;
                        double prev=b[k-1].High-b[k-1].Low;
                        double impulse=Math.Max(0,range-prev);
                        expansion+=impulse;
                        direction+=Math.Sign(b[k].Close-b[k-1].Close)*
                            impulse;
                    }
                    return Div(direction,expansion);
                }
            }
            throw new ArgumentOutOfRangeException("family");
        }

        public static bool TryEvaluate(IList<NQBarV11> bars,int type,
            int period,out bool bull,out bool bear)
        {
            bull=false;bear=false;
            if(bars==null||type<0||type>=Count||
               period<MinPeriod||period>MaxPeriod||
               bars.Count<RequiredBars(period))
                return false;
            if(type<NQNativeConditionsV11.Count)
                return NQNativeConditionsV11.TryEvaluate(bars,type,
                    period,out bull,out bear);
            int f=type/Rules,rule=type%Rules,at=bars.Count-1;
            double x=Feature(bars,at,f,period);
            double y=Feature(bars,at-1,f,period);
            double z=Feature(bars,at-2,f,period);
            if(!Finite(x)||!Finite(y)||!Finite(z))return false;
            switch(rule)
            {
                case 0: bull=x>0;bear=x<0;break;
                case 1: bull=x>y;bear=x<y;break;
                case 2: bull=y<=0&&x>0;bear=y>=0&&x<0;break;
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
