#region Using declarations
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Windows;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.Gui;
using NinjaTrader.Gui.Tools;
using NinjaTrader.NinjaScript;
#endregion

namespace NinjaTrader.NinjaScript.AddOns
{
    /// <summary>
    /// Research-only minute Last batch exporter for NQ/MNQ individual quarterly
    /// futures 2020-2024. Uses one official BarsRequest at a time (DoNotMerge).
    /// Does not place orders, does not read 2025/2026, and does not fetch tick data.
    ///
    /// NOTE: source needs compiling in NinjaTrader 8 on Windows; no runtime
    /// NinjaTrader instance is available in this research environment.
    /// </summary>
    public class NQMNQBulkMinuteExporter : AddOnBase
    {
        private NTMenuItem menuItem;
        private NTMenuItem existingMenu;
        private BarsRequest current;
        private readonly Queue<Job> queue = new Queue<Job>();
        private readonly object gate = new object();
        private bool active;
        private string outputRoot;
        private string manifestPath;

        private sealed class Job
        {
            public string Symbol;
            public int Year;
            public int ExpiryMonth;
            public DateTime Start;
            public DateTime End;
            public string InstrumentName;
            public string Filename;
        }

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Name = "NQMNQBulkMinuteExporter";
                Description = "Export 2020-2024 NQ & MNQ 1m Last by contract, DoNotMerge";
            }
            else if (State == State.Terminated)
            {
                if (current != null)
                {
                    try { current.Dispose(); } catch { }
                    current = null;
                }
            }
        }

        protected override void OnWindowCreated(Window window)
        {
            ControlCenter cc = window as ControlCenter;
            if (cc == null) return;
            existingMenu = cc.FindFirst("ControlCenterMenuItemNew") as NTMenuItem;
            if (existingMenu == null) return;
            menuItem = new NTMenuItem
            {
                Header = "NQ/MNQ 2020-24 Research Export",
                Style = Application.Current.TryFindResource("MainMenuItem") as Style
            };
            menuItem.Click += ClickExport;
            existingMenu.Items.Add(menuItem);
        }

        protected override void OnWindowDestroyed(Window window)
        {
            ControlCenter cc = window as ControlCenter;
            if (cc == null) return;
            if (menuItem != null)
            {
                menuItem.Click -= ClickExport;
                if (existingMenu != null) existingMenu.Items.Remove(menuItem);
                menuItem = null;
            }
            existingMenu = null;
        }

        private void ClickExport(object sender, RoutedEventArgs args)
        {
            lock (gate)
            {
                if (active)
                {
                    Log("Exporter is already running; duplicate click ignored.");
                    return;
                }
                active = true;
            }
            try
            {
                outputRoot = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),
                    "NinjaTrader 8", "NQMNQ_Research_2020_2024");
                Directory.CreateDirectory(outputRoot);
                manifestPath = Path.Combine(outputRoot,"download_manifest.csv");
                if (!File.Exists(manifestPath))
                    File.WriteAllText(manifestPath,
                        "symbol,contract,year,expiry_month,rows,min_local,max_local,status,detail,filename"+Environment.NewLine);
                BuildJobs();
                Log("Starting 40 queued contract requests (20 NQ + 20 MNQ). Export folder: " + outputRoot);
                Next();
            }
            catch (Exception ex)
            {
                Log("EXPORT INIT FAILURE " + ex.Message);
                lock (gate) active = false;
            }
        }

        private void BuildJobs()
        {
            queue.Clear();
            foreach (string symbol in new[] { "NQ", "MNQ" })
                for (int year = 2020; year <= 2024; year++)
                    foreach (int month in new[] {3,6,9,12})
                    {
                        // Source quarters deliberately overlap; Python will stitch and
                        // deduplicate by raw UTC timestamp with explicit rollovers.
                        int startMonth = month == 3 ? 1 : month-3;
                        var from = new DateTime(year, startMonth, 1);
                        var to = new DateTime(year, month, 25);
                        // Each job is explicitly confined to development calendar years.
                        queue.Enqueue(new Job {
                            Symbol=symbol,Year=year,ExpiryMonth=month,Start=from,End=to,
                            InstrumentName=string.Format(CultureInfo.InvariantCulture,"{0} {1:00}-{2:00}",symbol,month,year%100),
                            Filename=string.Format(CultureInfo.InvariantCulture,"{0}_{1:00}-{2:00}_Minute_Last.txt",symbol,month,year%100)
                        });
                    }
        }

        private void Next()
        {
            if (queue.Count == 0)
            {
                lock (gate) active=false;
                Log("Export batch finished. Open the manifest and check FAILED / INCOMPLETE rows.");
                return;
            }
            Job job=queue.Dequeue();
            string path=Path.Combine(outputRoot,job.Filename);
            if (File.Exists(path))
            {
                // Strict resume: skip only when file has substantial content.
                // The Python QC script later validates full year range and gaps.
                var size=new FileInfo(path).Length;
                if (size > 1000000)
                {
                    Log("RESUME: existing "+job.Filename+" ("+size+" bytes). Validate with Python QC.");
                    Next();
                    return;
                }
                Log("Partial file detected; retry "+job.Filename);
            }
            try
            {
                var instrument=Instrument.GetInstrument(job.InstrumentName);
                if (instrument == null) throw new InvalidOperationException("Unknown instrument "+job.InstrumentName);
                current=new BarsRequest(instrument,job.Start,job.End);
                current.BarsPeriod=new BarsPeriod { BarsPeriodType=BarsPeriodType.Minute,Value=1 };
                current.MergePolicy=MergePolicy.DoNotMerge;
                current.LookupPolicy=LookupPolicies.Provider;
                current.TradingHours=TradingHours.Get("CME US Index Futures ETH");
                // BarsRequest.Request is async; do not dispose before callback.
                current.Request((request,code,message) => {
                    try
                    {
                        if (code != ErrorCode.NoError)
                        {
                            Log("ERROR " + job.InstrumentName+" "+code+" "+message);
                            Record(job,0,"FAILED",code+" "+message,"","");
                        }
                        else
                        {
                            Save(job,request.Bars);
                        }
                    }
                    catch(Exception ex)
                    {
                        Log("ERROR saving "+job.InstrumentName+": "+ex.Message);
                        Record(job,0,"FAILED",ex.Message,"","");
                    }
                    finally
                    {
                        try { if(current!=null)current.Dispose(); }catch{}
                        current=null;
                        // Sequential scheduling avoids overloading the data provider.
                        Core.Globals.RandomDispatcher.InvokeAsync(new Action(Next));
                    }
                });
            }
            catch(Exception ex)
            {
                Log("ERROR fetching "+job.InstrumentName+": "+ex.Message);
                Record(job,0,"FAILED",ex.Message,"","");
                if(current!=null){try{current.Dispose();}catch{} current=null;}
                Core.Globals.RandomDispatcher.InvokeAsync(new Action(Next));
            }
        }

        private void Save(Job job, Bars bars)
        {
            if (bars == null || bars.Count == 0)
            {
                Record(job,0,"EMPTY","No historical minute data returned","","");
                Log("EMPTY "+job.InstrumentName);
                return;
            }
            string path=Path.Combine(outputRoot,job.Filename);
            string temp=path+".partial";
            var tz=NinjaTrader.Core.Globals.GeneralOptions.TimeZoneInfo;
            string first="",last="";
            int count=0;
            using (var sw=new StreamWriter(temp,false,new UTF8Encoding(false)))
            {
                for(int i=0;i<bars.Count;i++)
                {
                    // BarsRequest GetTime uses NinjaTrader platform time zone; convert
                    // to UTC for the established research raw-file convention.
                    DateTime local=DateTime.SpecifyKind(bars.GetTime(i),DateTimeKind.Unspecified);
                    DateTime utc=TimeZoneInfo.ConvertTimeToUtc(local,tz);
                    if (utc.Year<2020 || utc.Year>2024) continue;
                    string stamp=utc.ToString("yyyyMMdd HHmmss",CultureInfo.InvariantCulture);
                    if(count==0) first=stamp;
                    last=stamp;
                    sw.Write(stamp);sw.Write(';');
                    sw.Write(bars.GetOpen(i).ToString(CultureInfo.InvariantCulture));sw.Write(';');
                    sw.Write(bars.GetHigh(i).ToString(CultureInfo.InvariantCulture));sw.Write(';');
                    sw.Write(bars.GetLow(i).ToString(CultureInfo.InvariantCulture));sw.Write(';');
                    sw.Write(bars.GetClose(i).ToString(CultureInfo.InvariantCulture));sw.Write(';');
                    sw.WriteLine(bars.GetVolume(i).ToString(CultureInfo.InvariantCulture));
                    count++;
                }
            }
            if (count<20000)
            {
                Record(job,count,"INCOMPLETE","Fewer than 20,000 minute records; provider might not offer 2020-24 history",first,last);
                Log("INCOMPLETE "+job.InstrumentName+": "+count+" bars (not accepting result). Inspect .partial file.");
                return;  // leave *.partial for inspection, don't replace old data
            }
            if(File.Exists(path))File.Delete(path);
            File.Move(temp,path);
            Record(job,count,"EXPORTED","Pending independent SHA256/coverage QC",first,last);
            Log("EXPORTED "+job.InstrumentName+" "+count+" bars to "+job.Filename);
        }

        private void Record(Job job,int count,string status,string detail,string first,string last)
        {
            string safe=detail.Replace(',',' ').Replace('\n',' ').Replace('\r',' ');
            var fields=new [] {job.Symbol,job.InstrumentName,job.Year.ToString(CultureInfo.InvariantCulture),
                job.ExpiryMonth.ToString(CultureInfo.InvariantCulture),count.ToString(CultureInfo.InvariantCulture),first,last,status,safe,job.Filename};
            File.AppendAllText(manifestPath,string.Join(",",fields)+Environment.NewLine);
        }
        private static void Log(string text)
        {
            NinjaTrader.Code.Output.Process("[NQ/MNQ BULK EXPORT] "+text,PrintTo.OutputTab1);
        }
    }
}