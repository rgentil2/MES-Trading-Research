// S0.76 — READ-ONLY loader for documented NinjaTrader 8 1-MINUTE
// LAST .txt exports: yyyyMMdd HHmmss;open;high;low;close;volume.
// Official NT8 exports UTC END-OF-BAR timestamps. Convert UTC -> America/
// New_York (observing actual DST), THEN subtract 1 minute to get START of
// completed bar expected by V11–V15. Only 08:00–11:29 ET M1 kept.
// This removes ambiguous 01:00 fall-back duplicated local-time hours and
// contains 90 RTH-preface bars for 7–28 bar ATR, while preserving original
// minute closes/opens. Does not prove contract merge/roll/price parity.
// No NinjaTrader API dependency; never trades, never queries heldout years.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;

namespace NinjaTrader.NinjaScript.Strategies
{
    public enum NQDataPartitionV16
    {
        Development2020_2022=0,
        ExternalValidation2023_2024=1,
        FinalHoldout2025_2026=2
    }

    public sealed class NQDataManifestV16
    {
        public readonly NQDataPartitionV16 Partition;
        public readonly string Instrument, ContractPolicy, Sha256;
        public readonly DateTime FirstUTC,LastUTC,FirstEastern,LastEastern;
        public readonly int RawRows,KeptMorningRows,CompleteRthDays;
        public readonly int[] FullSessionsByMonth;

        public NQDataManifestV16(NQDataPartitionV16 partition,string instrument,
            string contractPolicy,string sha256,DateTime firstUTC,
            DateTime lastUTC,DateTime firstET,DateTime lastET,
            int raw,int kept,int days,int[] monthly)
        {
            Partition=partition;Instrument=instrument;ContractPolicy=contractPolicy;
            Sha256=sha256;FirstUTC=firstUTC;LastUTC=lastUTC;
            FirstEastern=firstET;LastEastern=lastET;
            RawRows=raw;KeptMorningRows=kept;CompleteRthDays=days;
            FullSessionsByMonth=(int[])monthly.Clone();
        }
    }

    public sealed class NQDataLoadV16
    {
        public readonly NQDataManifestV16 Manifest;
        public readonly IList<NQTimedBarV12> Bars;
        public NQDataLoadV16(NQDataManifestV16 manifest,
                             IList<NQTimedBarV12> bars)
        {Manifest=manifest;Bars=bars;}
    }

    public static class NQNativeDataLoaderV16
    {
        private const string DatePattern="yyyyMMdd HHmmss";
        private static readonly CultureInfo Invariant=CultureInfo.InvariantCulture;
        private static bool Finite(double a)
        {return !Double.IsNaN(a)&&!Double.IsInfinity(a);}
        private static TimeZoneInfo Eastern()
        {
            foreach(string name in new[]{"Eastern Standard Time","America/New_York"})
                try{return TimeZoneInfo.FindSystemTimeZoneById(name);}
                catch(TimeZoneNotFoundException){}
                catch(InvalidTimeZoneException){}
            throw new InvalidOperationException("No United States Eastern DST time zone");
        }

        public static int FirstYear(NQDataPartitionV16 p)
        {
            switch(p)
            {
                case NQDataPartitionV16.Development2020_2022:return 2020;
                case NQDataPartitionV16.ExternalValidation2023_2024:return 2023;
                case NQDataPartitionV16.FinalHoldout2025_2026:return 2025;
                default:throw new ArgumentOutOfRangeException("p");
            }
        }
        public static int LastYear(NQDataPartitionV16 p)
        {
            switch(p)
            {
                case NQDataPartitionV16.Development2020_2022:return 2022;
                case NQDataPartitionV16.ExternalValidation2023_2024:return 2024;
                case NQDataPartitionV16.FinalHoldout2025_2026:return 2026;
                default:throw new ArgumentOutOfRangeException("p");
            }
        }
        private static bool Quarter(double x)
        {
            return Math.Abs(x/0.25-Math.Round(x/0.25))<1e-7;
        }
        private static int Clock(DateTime t)
        {return 100*t.Hour+t.Minute;}

        // Contract metadata is declared by operator and stored in manifest.
        // This code cannot independently inspect NT8's merge-policy setting.
        // Thus never imply contract backadjustment or continuous contract
        // continuity were verified from a filename.
        public static NQDataLoadV16 Load(Stream input,
            NQDataPartitionV16 partition,string instrument,
            string contractPolicy,int minimumCompleteDaysPerMonth)
        {
            if(input==null||!input.CanSeek||!input.CanRead||
               String.IsNullOrWhiteSpace(instrument)||
               !instrument.StartsWith("NQ",StringComparison.OrdinalIgnoreCase)||
               String.IsNullOrWhiteSpace(contractPolicy)||
               minimumCompleteDaysPerMonth<0||
               minimumCompleteDaysPerMonth>23)
                throw new ArgumentException("Read-only seekable UTC LAST stream, NQ instrument and metadata required");
            int first=FirstYear(partition),last=LastYear(partition);
            if(input.Position!=0)
                throw new ArgumentException("Export input must begin at byte 0");
            string checksum;
            using(var sha=SHA256.Create())
            {
                byte[] digest=sha.ComputeHash(input);
                checksum=BitConverter.ToString(digest).Replace("-","").ToLowerInvariant();
            }
            input.Position=0;
            var eastern=Eastern();
            var result=new List<NQTimedBarV12>();
            int raw=0;
            DateTime firstUTC=DateTime.MinValue,lastUTC=DateTime.MinValue;
            DateTime priorUTC=DateTime.MinValue,priorET=DateTime.MinValue;
            // leaveOpen protects callers who want to reuse the stream.
            using(var reader=new StreamReader(input,Encoding.UTF8,true,65536,true))
            {
                string line;
                while((line=reader.ReadLine())!=null)
                {
                    if(line.Length==0)
                        throw new FormatException("Empty exported M1 row");
                    raw++;
                    string[] v=line.Split(';');
                    if(v.Length!=6)
                        throw new FormatException("M1 export needs exactly 6 semicolon columns, line "+raw);
                    DateTime time;
                    if(!DateTime.TryParseExact(v[0],DatePattern,Invariant,
                        DateTimeStyles.None,out time))
                        throw new FormatException("Bad UTC end-of-minute stamp at line "+raw);
                    DateTime utc=DateTime.SpecifyKind(time,DateTimeKind.Utc);
                    if(utc<=priorUTC)
                        throw new FormatException("Duplicate or non-increasing UTC timestamp at line "+raw);
                    priorUTC=utc;
                    if(raw==1)firstUTC=utc;
                    lastUTC=utc;
                    double[] p=new double[5];
                    for(int i=0;i<5;i++)
                        if(!Double.TryParse(v[i+1],NumberStyles.Float,
                                Invariant,out p[i])||!Finite(p[i]))
                            throw new FormatException("Non-numeric price/volume at line "+raw);
                    for(int i=0;i<4;i++)
                        if(p[i]<=0||!Quarter(p[i]))
                            throw new FormatException("Invalid NQ quarter-point price at line "+raw);
                    if(p[4]<0||Math.Abs(p[4]-Math.Round(p[4]))>1e-6)
                        throw new FormatException("Negative/non-integer traded volume at line "+raw);
                    NQBarV11 bar;
                    try{bar=new NQBarV11(p[0],p[1],p[2],p[3],p[4]);}
                    catch(ArgumentException ex)
                    {throw new FormatException("Invalid OHLC at line "+raw,ex);}
                    // Convert END UTC to start-of-completed-minute Eastern.
                    DateTime et=TimeZoneInfo.ConvertTimeFromUtc(utc,eastern)
                        .AddMinutes(-1);
                    int hhmm=Clock(et);
                    if(hhmm<800||hhmm>1129)continue;
                    if(et.Year<first||et.Year>last)
                        throw new InvalidOperationException(
                            "Partition violation: a relevant RTH bar outside "+first+"–"+last);
                    if(et<=priorET)
                        throw new FormatException(
                            "Duplicate/nonincreasing Eastern research M1 timestamp");
                    priorET=et;
                    result.Add(new NQTimedBarV12(et,bar));
                }
            }
            if(result.Count==0)
                throw new InvalidOperationException("No 08:00–11:29 ET morning bars");
            var sessions=new int[(last-first+1)*12];
            int complete=0;
            DateTime day=DateTime.MinValue;
            int[] flags=new int[120];
            int dayObserved=0;
            Action count=()=>
            {
                if(dayObserved==120 && flags.All(x=>x==1))
                {
                    complete++;
                    sessions[(day.Year-first)*12+day.Month-1]++;
                }
            };
            foreach(var row in result)
            {
                if(row.Time.Date!=day)
                {
                    if(day!=DateTime.MinValue)count();
                    day=row.Time.Date;
                    Array.Clear(flags,0,flags.Length);
                    dayObserved=0;
                }
                int min=Clock(row.Time);
                if(min>=930&&min<=1129)
                {
                    int index=(row.Time.Hour-9)*60+row.Time.Minute-30;
                    // 10:00 onwards calculation: 60-30+minute.
                    if(index<0||index>=120||flags[index]!=0)
                        throw new FormatException("Bad/duplicate RTH index");
                    flags[index]=1;dayObserved++;
                }
            }
            count();
            if(sessions.Any(x=>x<minimumCompleteDaysPerMonth))
                throw new InvalidOperationException(
                    "Insufficient complete 09:30–11:29 Eastern sessions for partition");
            var a=result[0].Time;var z=result[result.Count-1].Time;
            var manifest=new NQDataManifestV16(partition,instrument,
                contractPolicy,checksum,firstUTC,lastUTC,a,z,
                raw,result.Count,complete,sessions);
            // Immutable collection stops downstream mutation of dataset.
            return new NQDataLoadV16(manifest,
                Array.AsReadOnly(result.ToArray()));
        }
    }
}
