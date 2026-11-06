// V19 families 99..119: volume-flow indicators and price-action
// measurements, all from COMPLETED 1-minute OHLCV only.
// "Delta" is a candle-direction PROXY, NOT exchange order-flow delta.
using System;
using System.Collections.Generic;
using M = NinjaTrader.NinjaScript.Strategies.NQFeatureMathV19;

namespace NinjaTrader.NinjaScript.Strategies
{
    internal static class NQVolumeActionFeaturesV19
    {
        private static double Vema(IList<NQBarV11> b,int at,int n)
        {
            // EMA of price*volume / EMA of volume. The zero-volume
            // edge case uses close, never a future quote.
            double a=M.EMA(b,at,n,4),s=0;
            double alpha=2.0/(n+1);
            int from=Math.Max(0,at-3*n-5);
            double numerator=b[from].Close*b[from].Volume;
            for(int k=from+1;k<=at;k++)
                numerator+=alpha*(b[k].Close*b[k].Volume-numerator);
            return a>M.Eps?numerator/a:b[at].Close;
        }
        private static double Flow(IList<NQBarV11> b,int k)
        {
            double previous=M.P(b,k-1,5),now=M.P(b,k,5);
            return Math.Sign(now-previous)*b[k].Volume;
        }
        public static double Compute(IList<NQBarV11> b,int at,int n,int f)
        {
            int start=at-n+1,half=Math.Max(2,n/2);
            double price=b[at].Close,atr=M.ATR(b,at,n);
            double volume=Math.Max(M.SumVolume(b,at,n),M.Eps);
            switch(f)
            {
                case 99: // volume oscillator × signed price direction
                    return M.Direction(b,at,half)*M.Div(
                        M.SMA(b,at,half,4)-M.SMA(b,at,n,4),
                        M.SMA(b,at,n,4));
                case 100: // relative volume surprise weighted price ROC
                    return M.ROC(b,at,half)*
                        M.Div(b[at].Volume,M.SMA(b,at,n,4));
                case 101: // NVI: cumulative return on declining volume days
                {
                    double value=0;
                    for(int k=start;k<=at;k++)
                        if(b[k].Volume<b[k-1].Volume)
                            value+=M.ROC(b,k,1);
                    return value;
                }
                case 102: // PVI: cumulative return on rising volume days
                {
                    double value=0;
                    for(int k=start;k<=at;k++)
                        if(b[k].Volume>b[k-1].Volume)
                            value+=M.ROC(b,k,1);
                    return value;
                }
                case 103: // VFI: capped typical change times traded volume
                {
                    double flow=0,total=0,vola=0;
                    for(int k=start;k<=at;k++)
                    {
                        double pct=M.Div(M.P(b,k,5)-M.P(b,k-1,5),
                            M.P(b,k-1,5));
                        vola+=pct*pct;
                    }
                    double cutoff=0.2*Math.Sqrt(vola/n);
                    double average=M.SMA(b,at,n,4);
                    for(int k=start;k<=at;k++)
                    {
                        double diff=M.Div(M.P(b,k,5)-M.P(b,k-1,5),
                            M.P(b,k-1,5));
                        double capped=Math.Min(b[k].Volume,2.5*average);
                        flow+=diff>cutoff?capped:
                            diff< -cutoff?-capped:0;
                        total+=capped;
                    }
                    return M.Div(flow,total);
                }
                case 104: // Accumulated volume-weighted price change
                {
                    double a=0;
                    for(int k=start;k<=at;k++)
                        a+=M.ROC(b,k,1)*b[k].Volume;
                    return M.Div(a,volume);
                }
                case 105: // PVT smoothed momentum, not raw PVT (V18)
                {
                    int from=at-2*n,alphaN=n;
                    double alpha=2.0/(alphaN+1),raw=0,smoothed=0;
                    for(int k=from+1;k<=at;k++)
                    {
                        raw+=M.ROC(b,k,1)*b[k].Volume;
                        smoothed+=alpha*(raw-smoothed);
                    }
                    return M.Div(raw-smoothed,volume);
                }
                case 106: // Klinger-like dual EMA volume-force oscillator
                {
                    int from=Math.Max(1,at-3*n-5);
                    double eShort=Flow(b,from),eLong=eShort;
                    double ashort=2.0/(half+1),along=2.0/(n+1);
                    for(int k=from+1;k<=at;k++)
                    {
                        double force=Flow(b,k);
                        eShort+=ashort*(force-eShort);
                        eLong+=along*(force-eLong);
                    }
                    return M.Div(eShort-eLong,
                        Math.Max(1,M.SMA(b,at,n,4)));
                }
                case 107: // Twiggs-like smoothed money flow
                {
                    int from=at-2*n;
                    double numerator=0,den=0,alpha=2.0/(n+1);
                    for(int k=from;k<=at;k++)
                    {
                        var x=b[k];
                        double spread=Math.Max(x.High,
                            b[Math.Max(0,k-1)].Close)-
                            Math.Min(x.Low,b[Math.Max(0,k-1)].Close);
                        double mf=M.Div(2*x.Close-
                            Math.Max(x.High,b[k-1].Close)-
                            Math.Min(x.Low,b[k-1].Close),spread)*
                            x.Volume;
                        if(k==from){numerator=mf;den=x.Volume;}
                        else
                        {
                            numerator+=alpha*(mf-numerator);
                            den+=alpha*(x.Volume-den);
                        }
                    }
                    return M.Div(numerator,den);
                }
                case 108: // volume-weighted RSI of signed price changes
                {
                    double up=0,down=0;
                    for(int k=start;k<=at;k++)
                    {
                        double d=b[k].Close-b[k-1].Close;
                        up+=Math.Max(0,d)*b[k].Volume;
                        down+=Math.Max(0,-d)*b[k].Volume;
                    }
                    return M.Div(up-down,up+down);
                }
                case 109: // VEMA fast-slow volume-adjusted MACD / ATR
                    return (Vema(b,at,half)-Vema(b,at,n))/atr;
                case 110: // price-candle up-volume minus down-volume
                {
                    double up=0,down=0;
                    for(int k=start;k<=at;k++)
                    {
                        if(b[k].Close>b[k].Open)up+=b[k].Volume;
                        if(b[k].Close<b[k].Open)down+=b[k].Volume;
                    }
                    return M.Div(up-down,up+down);
                }
                case 111: // signed momentum weighted by volume anomaly
                    return M.Div(price-b[at-half].Close,atr)*
                        M.Div(b[at].Volume,
                            Math.Max(1,M.SMA(b,at,n,4)));
                case 112: // tick-free proportional body/volume delta
                {
                    double delta=0;
                    for(int k=start;k<=at;k++)
                        delta+=M.Div(b[k].Close-b[k].Open,
                            b[k].High-b[k].Low)*b[k].Volume;
                    return M.Div(delta,volume);
                }
                case 113: // Heikin Ashi causal candle body strength
                {
                    int from=at-n+1;
                    double haOpen=(b[from].Open+b[from].Close)/2;
                    double haClose=(b[from].Open+b[from].High+
                        b[from].Low+b[from].Close)/4;
                    for(int k=from+1;k<=at;k++)
                    {
                        double prevOpen=haOpen,prevClose=haClose;
                        haOpen=(prevOpen+prevClose)/2;
                        haClose=(b[k].Open+b[k].High+
                            b[k].Low+b[k].Close)/4;
                    }
                    return M.Div(haClose-haOpen,atr);
                }
                case 114: // body-to-upper/lower-wick pressure imbalance
                {
                    double body=price-b[at].Open;
                    double upper=b[at].High-Math.Max(price,b[at].Open);
                    double lower=Math.Min(price,b[at].Open)-b[at].Low;
                    return M.Div(body+lower-upper,
                        b[at].High-b[at].Low);
                }
                case 115: // two-candle engulfing body pattern
                {
                    var prev=b[at-1];var curr=b[at];
                    bool bull=prev.Close<prev.Open&&curr.Close>curr.Open&&
                        curr.Open<=prev.Close&&curr.Close>=prev.Open;
                    bool bear=prev.Close>prev.Open&&curr.Close<curr.Open&&
                        curr.Open>=prev.Close&&curr.Close<=prev.Open;
                    return bull?1:bear?-1:0;
                }
                case 116: // inside / outside bar directional breakout
                {
                    var x=b[at];var prev=b[at-1];
                    bool inside=x.High<prev.High&&x.Low>prev.Low;
                    bool outside=x.High>prev.High&&x.Low<prev.Low;
                    if(outside)return M.Div(x.Close-x.Open,atr);
                    if(inside)return M.Div(x.Close-prev.Close,2*atr);
                    return 0;
                }
                case 117: // NR7 narrow-range compression / breakout
                {
                    int lag=7;
                    double range=b[at-1].High-b[at-1].Low;
                    bool min=true;
                    for(int k=at-lag;k<at-1;k++)
                        if(range>=b[k].High-b[k].Low){min=false;break;}
                    if(!min)return 0;
                    if(price>b[at-1].High)
                        return (price-b[at-1].High)/atr;
                    if(price<b[at-1].Low)
                        return (price-b[at-1].Low)/atr;
                    return 0;
                }
                case 118: // polarized fractal efficiency, signed path ratio
                {
                    double path=0;
                    for(int k=start;k<=at;k++)
                    {
                        double delta=b[k].Close-b[k-1].Close;
                        path+=Math.Sqrt(delta*delta+1);
                    }
                    double net=price-b[at-n].Close;
                    double direct=Math.Sqrt(net*net+n*n);
                    return Math.Sign(net)*M.Div(direct,path);
                }
                case 119: // Hurst rescaled-range exponent × signed trend
                {
                    double mean=0,variance=0,cumulative=0;
                    double hi=Double.NegativeInfinity,
                        lo=Double.PositiveInfinity;
                    for(int k=start;k<=at;k++)
                        mean+=b[k].Close-b[k-1].Close;
                    mean/=n;
                    for(int k=start;k<=at;k++)
                    {
                        double d=b[k].Close-b[k-1].Close-mean;
                        variance+=d*d;
                        cumulative+=d;
                        hi=Math.Max(hi,cumulative);
                        lo=Math.Min(lo,cumulative);
                    }
                    double s=Math.Sqrt(variance/n);
                    double hurst=s<=M.Eps?0.5:
                        Math.Log(Math.Max(1,(hi-lo)/s))/Math.Log(n);
                    return M.Direction(b,at,n)*
                        (M.Clip(hurst,0,1)-0.5)*2;
                }
            }
            throw new ArgumentOutOfRangeException("family");
        }
    }
}
