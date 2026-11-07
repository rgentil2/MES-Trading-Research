// S0.86 — regression for Mar 2020 audited V2 excluded sessions.
// V14 original >5-day guard must remain DEFAULT; only independently
// audited removed WEEKDAYS can cause an opt-in exception.
// Synthetic bar prices in this test, not market NQ data.
using System;
using System.Collections.Generic;
using NinjaTrader.NinjaScript.Strategies;
internal static class NQAuditedGapWhitelistTest
{
    static void A(bool pass,string why)
    {if(!pass)throw new Exception("NQ_AUDITED_GAP_FAIL "+why);}
    static NQBarV11 Bar()
    {return new NQBarV11(12000,12001,11999,12000,200);}
    static List<NQTimedBarV12> Source(
        DateTime first,DateTime next)
    {
        return new List<NQTimedBarV12>{
            new NQTimedBarV12(first,Bar()),
            new NQTimedBarV12(next,Bar())
        };
    }
    static bool Accepted(List<NQTimedBarV12> b,
        ISet<DateTime> excluded=null)
    {
        try
        {
            var cache=new NQNativeSignalCacheV14(b,1024*1024,
                1024*1024,NQNativeConditionsV11.Count,null,excluded);
            return cache.SourceBars==b.Count;
        }
        catch(ArgumentException){return false;}
    }
    public static int Main()
    {
        DateTime m11=new DateTime(2020,3,11,11,29,0);
        DateTime m17=new DateTime(2020,3,17,9,30,0);
        var source=Source(m11,m17);
        var audited=new HashSet<DateTime>{
            new DateTime(2020,3,12),
            new DateTime(2020,3,13),
            new DateTime(2020,3,16)
        };
        A(!Accepted(source),"default V14 must reject >5 day gap");
        A(Accepted(source,audited),
          "audited Mar12/13/16 allow unique calendar gap");
        A(!Accepted(source,new HashSet<DateTime>{
            new DateTime(2020,3,12),
            new DateTime(2020,3,16)
        }),"missing audited Mar13 must fail");
        A(!Accepted(source,new HashSet<DateTime>{
            new DateTime(2020,3,12),
            new DateTime(2020,3,13)
        }),"missing audited Mar16 must fail");
        A(!Accepted(new List<NQTimedBarV12>{
            new NQTimedBarV12(m17,Bar()),
            new NQTimedBarV12(m11,Bar())
        },audited),"unordered bars always reject");
        A(!Accepted(new List<NQTimedBarV12>{
            new NQTimedBarV12(m11,Bar()),
            new NQTimedBarV12(new DateTime(2023,3,17,9,30,0),Bar())
        },audited),"held out 2023 always rejects");
        DateTime far=new DateTime(2020,4,2,9,30,0);
        var allWeekdays=new HashSet<DateTime>();
        for(var d=m11.Date.AddDays(1);d<far.Date;d=d.AddDays(1))
            if(d.DayOfWeek!=DayOfWeek.Saturday&&
               d.DayOfWeek!=DayOfWeek.Sunday)
                allWeekdays.Add(d);
        A(!Accepted(Source(m11,far),allWeekdays),
          ">12-day gap must reject even if allowlisted");
        A(Accepted(Source(new DateTime(2020,3,5,9,30,0),
            new DateTime(2020,3,9,9,30,0))),
          "normal weekend remains supported without allowlist");
        Console.WriteLine("NQ_NATIVE_AUDITED_GAP_V3_PASS "+
            "march12_13_16_allowlisted=true"+
            " defaultStillStrict=true"+
            " missingWeekdayRejected=true"+
            " unorderedRejected=true futureRejected=true"+
            " over12DayRejected=true weekendAccepted=true");
        return 0;
    }
}
