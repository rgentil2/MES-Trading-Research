// S0.85 V24 long-horizon benchmark fixture; 36 FULL calendar
// months 2020–22, Monday–Friday complete synthetic M1 sessions,
// every day 08:00–11:29 ET (210 bars, 120 RTH). No external data,
// no real NQ instrument, no claim of historical market realism.
// Separately from 2025/26 frozen OOS partitions.
using System;
using System.Collections.Generic;
using System.Linq;
namespace NinjaTrader.NinjaScript.Strategies
{
    public static class NQNativeSynthetic36V24
    {
        public static NQDataLoadV16 Build(int seed=20261106,
            bool flipLate=false)
        {
            var random=new Random(seed);
            var bars=new List<NQTimedBarV12>(175000);
            var counts=new int[36];
            double price=15000;
            for(int year=2020;year<=2022;year++)
                for(int month=1;month<=12;month++)
                {
                    int days=DateTime.DaysInMonth(year,month);
                    for(int day=1;day<=days;day++)
                    {
                        DateTime date=new DateTime(year,month,day);
                        if(date.DayOfWeek==DayOfWeek.Saturday||
                           date.DayOfWeek==DayOfWeek.Sunday)
                            continue;
                        counts[(year-2020)*12+month-1]++;
                        for(int i=0;i<210;i++)
                        {
                            double open=price;
                            double underlying=
                                0.3+Math.Sin((i+13*month+day)*0.093)*2.3+
                                (random.NextDouble()-0.5)*2.7;
                            if(flipLate&&year==2022&&month>=7)
                                underlying=-1.2+Math.Sin(i*0.11)*1.1;
                            double change=0.25*Math.Round(underlying/0.25);
                            price=Math.Max(100,price+change);
                            var bar=new NQBarV11(open,
                                Math.Max(open,price)+0.75,
                                Math.Min(open,price)-0.75,price,
                                150+random.Next(1800));
                            bars.Add(new NQTimedBarV12(
                                date.AddHours(8).AddMinutes(i),bar));
                        }
                    }
                }
            // The manifest hash is intentionally held constant even
            // on flipLate changes: V24 additionally SHA's actual bars
            // to prevent stale results if caller supplies bad provenance.
            var manifest=new NQDataManifestV16(
                NQDataPartitionV16.Development2020_2022,
                "NQ DEC2026","SYNTHETIC_WEEKDAY_ONLY",
                new string('a',64),
                new DateTime(2020,1,1),new DateTime(2022,12,31),
                bars[0].Time,bars[bars.Count-1].Time,
                bars.Count,bars.Count,counts.Sum(),counts);
            return new NQDataLoadV16(manifest,bars.AsReadOnly());
        }
    }
}
