// S0.86 V25: read ORIGINAL NinjaTrader Analyzer end-stamped
// M1 data re-exported by NQ_V25_FrozenAnalyzer as ET minute START.
// Strict frozen SHA, scope, 08:00–11:29 window, monotonic OHLCV and
// >=15 full RTH sessions each required month; no roll-policy guesses.
// All numbers invariant; no strategy optimization or native orders.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
namespace NinjaTrader.NinjaScript.Strategies
{
    public static class NQNativeV25NativeBarsReader
    {
        static readonly CultureInfo I=CultureInfo.InvariantCulture;
        private static TimeZoneInfo ET()
        {
            foreach(string name in new[]{
                "Eastern Standard Time","America/New_York"})
                try{return TimeZoneInfo.FindSystemTimeZoneById(name);}
                catch(TimeZoneNotFoundException){}
                catch(InvalidTimeZoneException){}
            throw new InvalidOperationException(
                "V25_ET_DST_ZONE_NOT_FOUND");
        }
        private static int Months(NQDataPartitionV16 scope)
        {
            return scope==NQDataPartitionV16.Development2020_2022?36:
                scope==NQDataPartitionV16.ExternalValidation2023_2024?24:24;
        }
        private static DateTime End(NQDataPartitionV16 scope)
        {
            return scope==NQDataPartitionV16.Development2020_2022?
                new DateTime(2023,1,1):
                scope==NQDataPartitionV16.ExternalValidation2023_2024?
                new DateTime(2025,1,1):new DateTime(2026,11,1);
        }
        public static NQDataLoadV16 Load(string path,
            string expectedV25Lock,NQDataPartitionV16 scope,
            string instrument,string policy,int minFullSessions=15)
        {
            if(String.IsNullOrWhiteSpace(path)||
               String.IsNullOrWhiteSpace(expectedV25Lock)||
               expectedV25Lock.Length!=64||
               String.IsNullOrWhiteSpace(instrument)||
               String.IsNullOrWhiteSpace(policy)||
               minFullSessions<1||minFullSessions>23)
                throw new ArgumentException("V25_BARS_INPUTS_INVALID");
            var lines=File.ReadAllLines(path);
            if(lines.Length<3||
               lines[0]!="V25LockSHA256\t"+expectedV25Lock||
               lines[1]!="minuteStartET\topen\thigh\tlow\tclose\tvolume")
                throw new InvalidDataException("V25_BAR_LOCK_OR_COLUMNS_MISMATCH");
            var source=new List<NQTimedBarV12>(lines.Length-2);
            var monthly=new int[Months(scope)];
            int firstYear=NQNativeDataLoaderV16.FirstYear(scope);
            DateTime begin=new DateTime(firstYear,1,1);
            DateTime until=End(scope);
            DateTime prior=DateTime.MinValue,day=DateTime.MinValue;
            var rth=new List<DateTime>(120);
            Action finish=()=>
            {
                if(day==DateTime.MinValue||rth.Count==0)return;
                if(rth.Count!=120)
                    throw new InvalidDataException(
                        "V25_PARTIAL_RTH_DAY_NOT_ALLOWED "+day.ToString("yyyy-MM-dd"));
                var anchor=day.AddHours(9).AddMinutes(30);
                for(int k=0;k<120;k++)
                    if(rth[k]!=anchor.AddMinutes(k))
                        throw new InvalidDataException(
                            "V25_RTH_MINUTE_GAP "+day.ToString("yyyy-MM-dd"));
                int m=(day.Year-firstYear)*12+day.Month-1;
                if(m<0||m>=monthly.Length)
                    throw new InvalidDataException("V25_RTH_MONTH_OUTSIDE_SCOPE");
                monthly[m]++;
            };
            for(int i=2;i<lines.Length;i++)
            {
                var p=lines[i].Split('\t');
                if(p.Length!=6)
                    throw new InvalidDataException("V25_BAR_FIELD_COUNT");
                DateTime at;
                if(!DateTime.TryParseExact(p[0],"yyyy-MM-ddTHH:mm:ss",
                    I,DateTimeStyles.None,out at)||
                   at<begin||at>=until||at.Second!=0)
                    throw new InvalidDataException("V25_BAR_TIME_OUTSIDE_SCOPE");
                if(at<=prior||
                   (prior!=DateTime.MinValue&&
                    at-prior>TimeSpan.FromDays(5)))
                    throw new InvalidDataException("V25_BAR_ORDER_OR_GAP");
                double[] values=new double[5];
                for(int j=0;j<5;j++)
                    if(!Double.TryParse(p[j+1],NumberStyles.Float,I,
                        out values[j]))
                        throw new InvalidDataException("V25_M1_NONNUMERIC_BAR");
                NQBarV11 bar;
                try{bar=new NQBarV11(values[0],values[1],
                        values[2],values[3],values[4]);}
                catch(ArgumentException ex)
                {throw new InvalidDataException("V25_INVALID_OHLCV_BAR",ex);}
                int clock=at.Hour*100+at.Minute;
                if(clock<800||clock>1129)
                    throw new InvalidDataException("V25_OUTSIDE_0800_1129_ET");
                if(at.Date!=day)
                {
                    finish();day=at.Date;rth.Clear();
                }
                if(clock>=930&&clock<=1129)rth.Add(at);
                source.Add(new NQTimedBarV12(at,bar));
                prior=at;
            }
            finish();
            int requiredMonths=scope==
                NQDataPartitionV16.FinalHoldout2025_2026?22:monthly.Length;
            for(int i=0;i<requiredMonths;i++)
                if(monthly[i]<minFullSessions)
                    throw new InvalidDataException(
                        "V25_INCOMPLETE_M1_HISTORY_MONTH_"+i);
            if(scope==NQDataPartitionV16.FinalHoldout2025_2026&&
               monthly.Skip(22).Any(x=>x!=0))
                throw new InvalidDataException("V25_FINAL_CUTOFF_BREACHED");
            var zone=ET();
            DateTime firstUtc=TimeZoneInfo.ConvertTimeToUtc(
                source[0].Time,zone);
            DateTime lastUtc=TimeZoneInfo.ConvertTimeToUtc(
                source[source.Count-1].Time,zone);
            var manifest=new NQDataManifestV16(
                scope,instrument,policy,
                NQNativeReproducibilityV23.SHAFile(path),
                firstUtc,lastUtc,source[0].Time,
                source[source.Count-1].Time,
                lines.Length-2,source.Count,monthly.Sum(),monthly);
            return new NQDataLoadV16(manifest,source.AsReadOnly());
        }

        public static void RequireBarByBarEquality(
            IList<NQTimedBarV12> original,
            IList<NQTimedBarV12> native)
        {
            if(original==null||native==null||
               original.Count!=native.Count)
                throw new InvalidDataException(
                    "V25_REFERENCE_AND_NATIVE_BAR_COUNT_MISMATCH");
            for(int i=0;i<original.Count;i++)
            {
                var a=original[i];var b=native[i];
                if(a.Time!=b.Time||
                   Math.Abs(a.Bar.Open-b.Bar.Open)>1e-8||
                   Math.Abs(a.Bar.High-b.Bar.High)>1e-8||
                   Math.Abs(a.Bar.Low-b.Bar.Low)>1e-8||
                   Math.Abs(a.Bar.Close-b.Bar.Close)>1e-8||
                   Math.Abs(a.Bar.Volume-b.Bar.Volume)>1e-7)
                    throw new InvalidDataException(
                        "V25_BAR_SOURCE_MISMATCH_AT_"+i);
            }
        }
    }
}
