// V16 UTC-end timestamp / DST adapter tests. All text is generated
// from a controlled NT8-compatible synthetic minute fixture, NOT a real
// NQ export. No direct NT8 execution occurs.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using NinjaTrader.NinjaScript.Strategies;

internal static class V16DataLoaderTest
{
    static void A(bool yes,string message)
    {if(!yes)throw new Exception("NQ_V16_DATA_FAIL "+message);}
    static TimeZoneInfo Eastern()
    {
        foreach(string name in new[]{"Eastern Standard Time","America/New_York"})
            try{return TimeZoneInfo.FindSystemTimeZoneById(name);}
            catch(TimeZoneNotFoundException){}
        throw new Exception("No US Eastern zone on test runner");
    }
    static string Text(params DateTime[] dates)
    {
        var tz=Eastern();
        var sb=new StringBuilder();
        foreach(var day in dates.OrderBy(x=>x))
        {
            // Construct 08:00..11:29 Eastern START, convert to UTC END.
            // A winter 09:30 ET minute ends 14:31 UTC; a summer minute
            // ends 13:31 UTC. This must not shift the 09:30 signal.
            for(int minute=0;minute<210;minute++)
            {
                var start=DateTime.SpecifyKind(
                    day.Date.AddHours(8).AddMinutes(minute),
                    DateTimeKind.Unspecified);
                DateTime endUTC=TimeZoneInfo.ConvertTimeToUtc(
                    start.AddMinutes(1),tz);
                string ts=endUTC.ToString("yyyyMMdd HHmmss",
                    CultureInfo.InvariantCulture);
                decimal p=15000m+minute/4m;
                sb.Append(ts).Append(';')
                  .Append(p.ToString(CultureInfo.InvariantCulture))
                  .Append(';')
                  .Append((p+0.5m).ToString(CultureInfo.InvariantCulture))
                  .Append(';')
                  .Append((p-0.5m).ToString(CultureInfo.InvariantCulture))
                  .Append(';')
                  .Append(p.ToString(CultureInfo.InvariantCulture))
                  .Append(";120").Append('\n');
            }
        }
        return sb.ToString();
    }
    static NQDataLoadV16 Load(string source,
        NQDataPartitionV16 partition,int minimum=0)
    {
        using(var stream=new MemoryStream(Encoding.UTF8.GetBytes(source)))
            return NQNativeDataLoaderV16.Load(stream,partition,
                "NQ 03-22", "DECLARED_BACKADJUSTED_NOT_VERIFIED",minimum);
    }
    static void Reject(string payload,NQDataPartitionV16 p,
                       string reason)
    {
        try{Load(payload,p);throw new Exception("ACCEPTED_CORRUPT_"+reason);}
        catch(Exception ex)when(ex is FormatException ||
            ex is InvalidOperationException ||
            ex is ArgumentException)
        {
            A(ex.Message.Contains(reason),"expected fail-closed "+
                reason+" actual "+ex.Message);
        }
    }
    public static int Main()
    {
        var days=new List<DateTime>();
        for(int year=2020;year<=2022;year++)
            for(int m=1;m<=12;m++)
                days.Add(new DateTime(year,m,10));
        // Add explicit dates immediately around US DST changes.
        days.Add(new DateTime(2020,3,6));
        days.Add(new DateTime(2020,3,9));
        days.Add(new DateTime(2020,11,2));
        string raw=Text(days.ToArray());
        var parsed=Load(raw,NQDataPartitionV16.Development2020_2022,1);
        A(parsed.Bars.Count==210*days.Count,
            "all 210 morning minute bars retained per day");
        A(parsed.Manifest.RawRows==parsed.Bars.Count &&
          parsed.Manifest.CompleteRthDays==days.Count,
          "all 09:30-11:29 sessions complete");
        A(parsed.Manifest.FullSessionsByMonth.Length==36 &&
          parsed.Manifest.FullSessionsByMonth.All(x=>x>=1),
          "36-month development coverage");
        A(parsed.Manifest.Sha256.Length==64 &&
          parsed.Manifest.Sha256.All(x=>
            "0123456789abcdef".IndexOf(x)>=0),
          "SHA256 canonical lowercase dataset manifest");
        A(parsed.Manifest.FirstEastern==
          new DateTime(2020,1,10,8,0,0),
          "conversion preserves exact beginning of minute");
        A(parsed.Bars.All(x=>x.Time.Hour>=8&&
          x.Time.Hour<=11),"nothing outside morning research");
        foreach(var date in new[]{
            new DateTime(2020,3,6,9,30,0),
            new DateTime(2020,3,9,9,30,0),
            new DateTime(2020,11,2,9,30,0)})
            A(parsed.Bars.Any(x=>x.Time==date),
              "RTH 09:30 unaffected across DST "+date);
        var parsedAgain=Load(raw,NQDataPartitionV16.Development2020_2022,1);
        A(parsedAgain.Manifest.Sha256==parsed.Manifest.Sha256,
          "exact stream hash reproducible");
        A(!Object.ReferenceEquals(parsed.Manifest.FullSessionsByMonth,
             parsedAgain.Manifest.FullSessionsByMonth),
          "independent immutable output session counts");

        // A single March 2020 bar may still be valid development, but
        // fails 36-month minimum-session production presence control.
        try
        {Load(Text(new DateTime(2020,3,9)),
             NQDataPartitionV16.Development2020_2022,1);
         throw new Exception("ACCEPTED_INCOMPLETE_36_MONTHS");}
        catch(InvalidOperationException ex)
        {A(ex.Message.Contains("Insufficient"),
           "fail closed on missing required development months");}
        A(NQNativeDataLoaderV16.FirstYear(
            NQDataPartitionV16.ExternalValidation2023_2024)==2023 &&
          NQNativeDataLoaderV16.LastYear(
            NQDataPartitionV16.FinalHoldout2025_2026)==2026,
          "explicit partition bounds");

        string external=Text(new DateTime(2023,3,10));
        A(Load(external,NQDataPartitionV16.ExternalValidation2023_2024)
              .Bars.Count==210,
            "external segment allowed only in external adapter");
        Reject(external,NQDataPartitionV16.Development2020_2022,
            "Partition violation");
        Reject(raw,NQDataPartitionV16.FinalHoldout2025_2026,
            "Partition violation");

        string[] lines=Text(new DateTime(2020,3,9))
            .Split(new[]{'\n'},StringSplitOptions.RemoveEmptyEntries);
        var corrupt=(string[])lines.Clone();
        corrupt[15]=corrupt[14];
        Reject(String.Join("\n",corrupt)+"\n",
            NQDataPartitionV16.Development2020_2022,
            "Duplicate or non-increasing UTC");
        corrupt=(string[])lines.Clone();
        corrupt[5]=corrupt[5].Replace(";15001.25;",";15001.13;");
        Reject(String.Join("\n",corrupt)+"\n",
            NQDataPartitionV16.Development2020_2022,
            "quarter-point");
        corrupt=(string[])lines.Clone();
        corrupt[5]=corrupt[5].Replace(";120",";-3");
        Reject(String.Join("\n",corrupt)+"\n",
            NQDataPartitionV16.Development2020_2022,
            "Negative/non-integer");
        corrupt=(string[])lines.Clone();
        corrupt[5]+=";99";
        Reject(String.Join("\n",corrupt)+"\n",
            NQDataPartitionV16.Development2020_2022,
            "exactly 6");
        using(var s=new MemoryStream(Encoding.UTF8.GetBytes(raw)))
        {
            try{NQNativeDataLoaderV16.Load(s,
                NQDataPartitionV16.Development2020_2022,
                "ES 03-22","RAW",1);
                throw new Exception("ACCEPTED_ES_AS_NQ");}
            catch(ArgumentException ex)
            {A(ex.Message.Contains("NQ instrument"),"instrument guard");}
        }
        Console.WriteLine("NQ_V16_NT8_UTC_EXPORT_PASS rows="+
            parsed.Manifest.RawRows+" completeDays="+
            parsed.Manifest.CompleteRthDays+
            " SHA256="+parsed.Manifest.Sha256.Substring(0,16)+
            " dstMarch=PASS dstNovember=PASS partitions=3");
        Console.WriteLine("SYNTHETIC_NT8_TEXT_FIXTURE_ONLY_NOT_REAL_NQ");
        return 0;
    }
}
