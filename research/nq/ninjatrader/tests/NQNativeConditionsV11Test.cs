// Pure C# numeric contract for 132 V11 signal conditions.
// Compiles exactly the same NQNativeConditionsV11.cs as NT8 strategy uses.
using System;
using System.Collections.Generic;
using System.Linq;
using NinjaTrader.NinjaScript.Strategies;
internal static class V11ConditionsTest
{
    private static void Assert(bool ok,string msg)
    {if(!ok)throw new Exception("V11_CHECK_FAIL "+msg);}
    private static List<NQBarV11> Build(int count,int seed,double priceScale=1,
                                        double volScale=1,bool flat=false)
    {
        var r=new List<NQBarV11>();
        var rng=new Random(seed);
        double p=15000;
        for(int i=0;i<count;i++)
        {
            double op=p;
            double ch=flat?0:Math.Sin(i/13.0)*2.5 +
                Math.Cos(i/41.0)*3.3 + (i%65<25?5:-3) +
                (rng.NextDouble()-0.5)*19;
            p+=ch;
            double hi=flat?p:Math.Max(op,p)+rng.NextDouble()*8;
            double lo=flat?p:Math.Min(op,p)-rng.NextDouble()*8;
            double vol=flat?100:40+rng.Next(1000);
            r.Add(new NQBarV11(op*priceScale,hi*priceScale,
                lo*priceScale,p*priceScale,vol*volScale));
        }
        return r;
    }
    public static int Main()
    {
        Assert(NQNativeConditionsV11.Count==132,"catalog count");
        Assert(NQNativeConditionsV11.FamilyNames.Length==12,"12 families");
        Assert(NQNativeConditionsV11.RuleNames.Length==11,"11 predicates");
        Assert(Enumerable.Range(0,132).Select(NQNativeConditionsV11.Name)
            .Distinct(StringComparer.Ordinal).Count()==132,"132 unique names");
        Assert(NQNativeConditionsV11.RequiredBars(6)==40,"warmup formula");
        bool bull,bear;
        Assert(!NQNativeConditionsV11.TryEvaluate(null,0,6,
            out bull,out bear),"null must reject");
        Assert(!NQNativeConditionsV11.TryEvaluate(Build(150,3),132,6,
            out bull,out bear),"out of range condition");
        Assert(!NQNativeConditionsV11.TryEvaluate(Build(150,3),0,3,
            out bull,out bear),"out of range period");
        Assert(!NQNativeConditionsV11.TryEvaluate(Build(39,3),0,6,
            out bull,out bear),"not enough bars");
        Assert(NQNativeConditionsV11.TryEvaluate(Build(40,3),0,6,
            out bull,out bear),"exact warmup boundary");
        try {new NQBarV11(1,0,2,1,1);throw new Exception("should reject");}
        catch(ArgumentException) {}
        try {new NQBarV11(1,2,0,1,-1);throw new Exception("should reject");}
        catch(ArgumentException) {}
        var a=Build(360,20261105);
        var scaled=Build(360,20261105,3,5);
        var signatures=new HashSet<string>();
        int active=0,checkedStates=0;
        for(int type=0;type<132;type++)
        {
            var sig=new System.Text.StringBuilder();
            for(int at=180;at<360;at+=7)
            {
                int period=6+(type%6)*3; // 6...21
                var prefix=a.GetRange(0,at+1);
                var scaledPrefix=scaled.GetRange(0,at+1);
                bool up,down,sUp,sDown;
                bool ok=NQNativeConditionsV11.TryEvaluate(prefix,type,period,
                    out up,out down);
                bool scaledOk=NQNativeConditionsV11.TryEvaluate(
                    scaledPrefix,type,period,out sUp,out sDown);
                Assert(ok&&scaledOk,"ready feature type="+type);
                Assert(!(up&&down),"mutual exclusion type="+type);
                Assert(up==sUp&&down==sDown,
                    "positive price & volume scaling invariant type="+type);
                sig.Append(up?'L':down?'S':'.');
                if(up||down)active++;
                checkedStates++;
            }
            signatures.Add(sig.ToString());
        }
        Assert(signatures.Count>=30,"condition signatures should be diverse, "+
            signatures.Count);
        Assert(active>1000,"condition family not emitting enough signals "+active);
        var flat=Build(200,10,1,1,true);
        for(int type=0;type<132;type++)
        {
            bool up,down;
            Assert(NQNativeConditionsV11.TryEvaluate(flat,type,6,
                out up,out down),"flat evaluates");
            Assert(!up&&!down,"flat OHLC must be directionless type="+type);
        }
        Console.WriteLine("NQ_V11_132_CONDITIONS_PASS checked="+checkedStates+
            " active="+active+" distinctSignatures="+signatures.Count+
            " NO_LOOKAHEAD_CONTRACT=COMPLETED_BARS_ONLY");
        return 0;
    }
}
