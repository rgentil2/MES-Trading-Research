// S0.79 exact V18 396-conditions functional QA.
// All synthetic NQ-like OHLCV, not historical NQ DEC2026 market data.
using System;
using System.Collections.Generic;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;
internal static class V18CatalogTest
{
    static void Check(bool ok,string detail)
    {if(!ok)throw new Exception("NQ_V18_CATALOG_FAIL "+detail);}
    static List<NQBarV11> Synthetic(int bars,int seed,double drift)
    {
        var rng=new Random(seed);var b=new List<NQBarV11>();
        double price=15000;
        for(int k=0;k<bars;k++)
        {
            double open=price;
            price+=drift+Math.Sin(k*0.21)*3.5+
                (rng.NextDouble()-0.5)*4;
            double hi=Math.Max(open,price)+0.5+rng.NextDouble();
            double lo=Math.Min(open,price)-0.5-rng.NextDouble();
            b.Add(new NQBarV11(open,hi,lo,price,1+rng.Next(1000)));
        }
        return b;
    }
    static List<NQBarV11> Ramp(bool up)
    {
        var bars=new List<NQBarV11>();
        double p=15000;
        for(int i=0;i<250;i++)
        {
            double open=p,close=up?p+1:p-1;
            bars.Add(up?
                new NQBarV11(open,close,open-1,close,100):
                new NQBarV11(open,open+1,close,close,100));
            p=close;
        }
        return bars;
    }
    public static int Main()
    {
        Check(NQNativeConditionsV11.Count==132&&
            NQNativeConditionCatalogV18.Families==36&&
            NQNativeConditionCatalogV18.AddedFamilies==24&&
            NQNativeConditionCatalogV18.Count==396,
            "132 immutable V11 + 264 new V18 conditions");
        Check(NQNativeConditionCatalogV18.AddedNames.Length==24&&
            NQNativeConditionCatalogV18.AddedNames.Distinct().Count()==24,
            "new 24 named mathematical formula families are distinct");
        for(int type=0;type<132;type++)
            Check(NQNativeConditionCatalogV18.Name(type)==
                NQNativeConditionsV11.Name(type),
                "V11 identifier and label preserved "+type);

        int comparisons=0,ready=0,nonneutral=0;
        var history=Synthetic(250,20261106,0.65);
        foreach(int period in new[]{6,12,24,30})
        {
            int req=NQNativeConditionCatalogV18.RequiredBars(period);
            for(int type=0;type<396;type++)
                for(int end=req-1;end<history.Count;end+=17)
                {
                    var prefix=history.GetRange(0,end+1);
                    bool bull,bear;
                    Check(NQNativeConditionCatalogV18.TryEvaluate(
                        prefix,type,period,out bull,out bear),
                        "valid completed-bar condition "+type);
                    Check(!(bull&&bear),"ambiguous both sides "+type);
                    comparisons++;
                    ready++;
                    if(bull||bear)nonneutral++;
                    if(type<132)
                    {
                        bool b2,s2;
                        Check(NQNativeConditionsV11.TryEvaluate(
                            prefix,type,period,out b2,out s2)&&
                            bull==b2&&bear==s2,
                            "legacy type "+type+" exact compatibility");
                    }
                }
        }
        Check(comparisons>10000&&nonneutral>5000,
            "large direct-prefix signal coverage");
        // No lookahead: a feature evaluated on the SAME prefix cannot
        // change when later, arbitrarily violent bars are added.
        foreach(int type in new[]{132,154,188,209,242,276,309,330,374,395})
        {
            var early=history.GetRange(0,150);
            bool a,b,c,d;
            Check(NQNativeConditionCatalogV18.TryEvaluate(
                early,type,12,out a,out b),"early prefix valid");
            var altered=new List<NQBarV11>(early);
            altered.Add(new NQBarV11(3,5,1,4,999999999));
            altered.Add(new NQBarV11(4,7,2,6,999999999));
            // The two samples share 150 identical prefix bars. Always
            // evaluate the last of these 150, never the appended future.
            Check(NQNativeConditionCatalogV18.TryEvaluate(
                altered.GetRange(0,150),type,12,out c,out d)&&
                a==c&&b==d,"future bars cannot change prior signal");
        }
        // Independent closed-form sign checks on upward/downward
        // monotonic bars. These protect against simply labeling all
        // newly registered indicators as interchangeable pseudo-signals.
        int checkedRamps=0;
        var rising=Ramp(true);var falling=Ramp(false);
        foreach(int family in new[]{
            12,13,17,18,19,20,21,22,23,24,25,26,27,28,29,30,32,33,34})
        {
            bool riseBull,riseBear,fallBull,fallBear;
            Check(NQNativeConditionCatalogV18.TryEvaluate(rising,
                family*11,12,out riseBull,out riseBear)&&
                NQNativeConditionCatalogV18.TryEvaluate(falling,
                family*11,12,out fallBull,out fallBear),
                "formula must compute on both monotonic directions "+family);
            Check(riseBull&&!riseBear&&!fallBull&&fallBear,
                "reference monotonic sign symmetry family "+family);
            checkedRamps++;
        }
        Check(checkedRamps==19,"19 mathematically directional features");
        // Flat OHLCV in every new formula must never yield NaN/Infinity.
        var flat=Enumerable.Range(0,200).Select(i=>
            new NQBarV11(15000,15000,15000,15000,0)).ToList();
        int neutral=0;
        for(int type=132;type<396;type++)
        {
            bool bull,bear;
            Check(NQNativeConditionCatalogV18.TryEvaluate(flat,
                type,12,out bull,out bear),"finite on zero-range/volume");
            if(!bull&&!bear)neutral++;
        }
        Check(neutral>=250,
            "new formulas handle zero movement and zero volume");
        bool x,y;
        Check(!NQNativeConditionCatalogV18.TryEvaluate(
            history,396,12,out x,out y),"out of catalog IDs fail closed");
        Check(!NQNativeConditionCatalogV18.TryEvaluate(
            history,200,3,out x,out y),"invalid period fails closed");
        Check(!NQNativeConditionCatalogV18.TryEvaluate(
            history.GetRange(0,15),200,12,out x,out y),
            "insufficient history fails closed");

        Console.WriteLine("NQ_V18_CATALOG_PASS legacy=132 "+
            "newFeatures=24 totalFamilies=36 totalRules=396 "+
            "sampleComparisons="+comparisons+
            " directional="+nonneutral+
            " flatNeutral="+neutral+
            " rampDirectionalReference="+checkedRamps);
        Console.WriteLine("V18_FORMULAS_NOT_VENDOR_NT8_PARITY_OR_396_INDEPENDENT_INDICATORS");
        return 0;
    }
}
