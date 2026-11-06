// S0.80 V19 independent formula test: 120 registered technical
// functions, 1,320 valid directional conditions, backward parity
// of V11+V18 and numeric reference checks. ALL synthetic OHLCV.
using System;
using System.Collections.Generic;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;

internal static class V19FormulaTest
{
    private static void A(bool yes,string why)
    {if(!yes)throw new Exception("NQ_V19_FORMULA_FAIL "+why);}
    private static List<NQBarV11> Bars(int seed,int size=230)
    {
        var rng=new Random(seed);
        var x=new List<NQBarV11>();
        double p=15000+seed%17;
        for(int i=0;i<size;i++)
        {
            double o=p;
            p+=0.65+Math.Sin((i+seed%13)*0.11)*2.1+
                Math.Cos(i*0.19)*1.4+
                (rng.NextDouble()-0.5)*5;
            double h=Math.Max(o,p)+0.5+rng.NextDouble()*2;
            double l=Math.Min(o,p)-0.5-rng.NextDouble()*2;
            x.Add(new NQBarV11(o,h,l,p,50+rng.Next(1000)));
        }
        return x;
    }
    // Sparse event families require explicit trigger fixtures; random
    // paths alone commonly contain zero engulfings/NR7 breakouts.
    private static List<NQBarV11> EventPath(bool engulf)
    {
        var b=Enumerable.Range(0,230)
            .Select(_=>new NQBarV11(15000,15003,14997,15000,200))
            .ToList();
        if(engulf)
        {
            b[224]=new NQBarV11(15001,15002,14997,14998,200);
            b[225]=new NQBarV11(14997.5,15002.5,14997,15002,300);
        }
        else
        {
            b[224]=new NQBarV11(15000,15000.25,14999.75,15000,200);
            b[225]=new NQBarV11(15000,15002.5,14999.75,15002,300);
        }
        return b;
    }
    private static double SMA(IList<NQBarV11> b,int at,int n)
    {
        double sum=0;
        for(int i=at-n+1;i<=at;i++)sum+=b[i].Close;
        return sum/n;
    }
    private static double TR(IList<NQBarV11> b,int i)
    {
        double p=b[i-1].Close;
        return Math.Max(b[i].High-b[i].Low,Math.Max(
            Math.Abs(b[i].High-p),Math.Abs(b[i].Low-p)));
    }
    private static double AvgTR(IList<NQBarV11> b,int at,int n)
    {
        double x=0;for(int k=at-n+1;k<=at;k++)x+=TR(b,k);
        return x/n;
    }
    public static int Main()
    {
        A(NQNativeConditionsV11.Count==132&&
          NQNativeConditionCatalogV18.Count==396&&
          NQNativeConditionCatalogV19.Families==120&&
          NQNativeConditionCatalogV19.NewFamilies==84&&
          NQNativeConditionCatalogV19.Count==1320,
          "12 + 24 + 84 = 120 formulas and 1320 conditions");
        A(NQNativeConditionCatalogV19.AddedNames.Length==84 &&
          NQNativeConditionCatalogV19.AddedNames.Distinct(
              StringComparer.Ordinal).Count()==84,
          "84 uniquely described mathematical families");
        for(int id=0;id<396;id++)
            A(NQNativeConditionCatalogV19.Name(id)==
              NQNativeConditionCatalogV18.Name(id),
              "existing V11/V18 ID unchanged "+id);
        var b=Bars(20261106);
        int comparisons=0,original=0,directional=0;
        foreach(int n in new[]{6,12,24,30})
        {
            int start=NQNativeConditionCatalogV19.RequiredBars(n)-1;
            for(int end=start;end<b.Count;end+=31)
            {
                var prefix=b.GetRange(0,end+1);
                for(int id=0;id<1320;id++)
                {
                    bool bull=false,bear=false;
                    A(NQNativeConditionCatalogV19.TryEvaluate(
                        prefix,id,n,out bull,out bear),
                      "condition ready "+id+" n="+n+" at="+end);
                    A(!(bull&&bear),"no contradictory signal "+id);
                    if(bull||bear)directional++;
                    if(id<396)
                    {
                        bool u,v;
                        A(NQNativeConditionCatalogV18.TryEvaluate(
                           prefix,id,n,out u,out v)&&
                          u==bull&&v==bear,
                          "all 396 original signal results preserved");
                        original++;
                    }
                    comparisons++;
                }
            }
        }
        A(comparisons>=15000&&original>=4500,
            "large direct computed condition coverage");
        // Flat zero-volume bars: safe normalization must never emit
        // an invalid numerical signal, including 7 range-vol models.
        var flat=Enumerable.Range(0,210).Select(_=>
            new NQBarV11(15000,15000,15000,15000,0)).ToList();
        int flatReady=0;
        for(int id=396;id<1320;id++)
        {
            bool bull,bear;
            A(NQNativeConditionCatalogV19.TryEvaluate(
               flat,id,12,out bull,out bear),
              "finite on flat zero-volume OHLCV id "+id);
            A(!(bull&&bear),"flat cannot be simultaneous long+short");
            flatReady++;
        }
        A(flatReady==924,"every new condition finite on flat input");
        // Numerical reference #1: 36 fast SMA vs SMA price / ATR.
        int at=b.Count-1,n1=12;
        double expected=(SMA(b,at,6)-SMA(b,at,12))/
            AvgTR(b,at,12);
        double actual=NQNativeConditionCatalogV19.Feature(b,
            at,36,n1);
        A(Math.Abs(expected-actual)<1e-10,
            "reference fast/slow SMA distance");
        // Reference #2: Williams A/D, distinct from stochastic %K.
        double wad=0,tr=0;
        for(int k=at-n1+1;k<=at;k++)
        {
            double prev=b[k-1].Close;
            double refPrice=b[k].Close>prev?
                Math.Min(b[k].Low,prev):
                b[k].Close<prev?Math.Max(b[k].High,prev):
                b[k].Close;
            wad+=b[k].Close-refPrice;
            tr+=TR(b,k);
        }
        A(Math.Abs(wad/tr-
            NQNativeConditionCatalogV19.Feature(b,at,57,n1))<1e-10,
            "Williams AD has own volume-independent accumulation formula");
        // Reference #3: prior Donchian breakout cannot use current high/low.
        double priorHigh=Double.NegativeInfinity,
            priorLow=Double.PositiveInfinity;
        for(int k=at-12;k<at;k++)
        {
            priorHigh=Math.Max(priorHigh,b[k].High);
            priorLow=Math.Min(priorLow,b[k].Low);
        }
        expected=b[at].Close>priorHigh?
            (b[at].Close-priorHigh)/AvgTR(b,at,12):
            b[at].Close<priorLow?
            (b[at].Close-priorLow)/AvgTR(b,at,12):0;
        A(Math.Abs(expected-
            NQNativeConditionCatalogV19.Feature(b,at,80,12))<1e-10,
            "prior Donchian breakout does not peek at current high/low");
        // Reference #4: volumetric RSI gain/loss.
        double up=0,down=0;
        for(int k=at-11;k<=at;k++)
        {
            double d=b[k].Close-b[k-1].Close;
            up+=Math.Max(0,d)*b[k].Volume;
            down+=Math.Max(0,-d)*b[k].Volume;
        }
        expected=up+down==0?0:(up-down)/(up+down);
        A(Math.Abs(expected-
            NQNativeConditionCatalogV19.Feature(b,at,108,12))<1e-10,
            "volume-weighted RSI independently calculated");
        // Reference #5: Hurst statistic must be finite on random bars.
        double hurst=NQNativeConditionCatalogV19.Feature(b,at,119,12);
        A(!Double.IsNaN(hurst)&&!Double.IsInfinity(hurst)&&
          hurst>=-1&&hurst<=1,"Hurst signed R/S in safe range");

        // 84 feature formulas must not be identical stub expressions.
        // Fingerprint each one on three DISTINCT synthetic paths / bars.
        var bullishEngulf=EventPath(true);
        var narrowBreakout=EventPath(false);
        A(NQNativeConditionCatalogV19.Feature(
            bullishEngulf,225,115,12)==1,
          "true bullish engulfing must activate family 115");
        A(NQNativeConditionCatalogV19.Feature(
            narrowBreakout,225,117,12)>0,
          "true NR7 breakout must activate family 117");
        var paths=new[]{Bars(111),Bars(222),Bars(333),
            bullishEngulf,narrowBreakout};
        var fingerprints=new HashSet<string>(StringComparer.Ordinal);
        int varying=0;
        for(int f=36;f<120;f++)
        {
            var values=new List<double>();
            foreach(var series in paths)
                foreach(int last in new[]{155,191,225})
                    values.Add(NQNativeConditionCatalogV19.Feature(
                        series,last,f,12));
            A(values.All(x=>!Double.IsNaN(x)&&!Double.IsInfinity(x)),
              "finite sampled formula "+f);
            fingerprints.Add(String.Join("|",values.Select(x=>
                x.ToString("R",System.Globalization.CultureInfo.InvariantCulture))));
            if(values.Max()-values.Min()>1e-10)varying++;
        }
        A(fingerprints.Count==84,
            "all 84 numeric formulas distinguishable across random and event fixtures");
        A(varying==84,
            "all 84 formulas vary across completed-bar inputs");
        bool tb,ts;
        A(!NQNativeConditionCatalogV19.TryEvaluate(
            b,1320,12,out tb,out ts),
          "no out-of-catalog 1320 index accepted");
        A(!NQNativeConditionCatalogV19.TryEvaluate(
            b,500,3,out tb,out ts),
          "minimum period must be honored");
        A(!NQNativeConditionCatalogV19.TryEvaluate(
            b.GetRange(0,10),900,12,out tb,out ts),
          "incomplete warmup rejects novel technical formula");

        Console.WriteLine("NQ_V19_120_FORMULAS_PASS families=120 "+
            "newFormulas=84 conditions=1320 legacyParity="+original+
            " evaluated="+comparisons+" directional="+directional+
            " flatFinite="+flatReady+
            " numericalFingerprints="+fingerprints.Count+
            " varying="+varying+" independentReference=5");
        Console.WriteLine("120_FORMULAS_NOT_120_STATISTICALLY_INDEPENDENT_OR_NT8_VENDOR_PARITY");
        return 0;
    }
}
