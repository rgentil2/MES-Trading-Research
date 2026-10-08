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
    /// futures 2020-2026. Downloads and stores the 2025 validation and 2026
    /// pseudo-forward data in separate directories (no outcome analysis).
    /// Uses one official BarsRequest per contract (DoNotMerge), Minute Last only.
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
                Description = "Export 2020-2026 NQ/MNQ 1m Last with isolated 2025/2026 holdouts";
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
                Header = "NQ/MNQ 2020-26 Research Export",
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
                    "NinjaTrader 8", "NQMNQ_Research_2020_2026");
                Directory.CreateDirectory(outputRoot);
                manifestPath = Path.Combine(outputRoot,"download_manifest.csv");
                if (!File.Exists(manifestPath))
                    File.WriteAllText(manifestPath,
                        "symbol,contract,year,expiry_month,rows,min_utc,max_utc,status,detail,files"+Environment.NewLine);
                BuildJobs();
                Log("Starting "+queue.Count+" contract requests (2020-2026; late Dec 2026 added once MAR27 can supply data). Folder: " + outputRoot);
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
                for (int year = 2020; year <= 2027; year++)
                    foreach (int month in new[] { 3, 6, 9, 12 })
                    {
                        // MAR27 is needed only to finish the Dec-2026 rollover.
                        if (year == 2027 && month != 3) continue;
                        DateTime from = month == 3
                            ? new DateTime(year-1,12,1)
                            : new DateTime(year,month-3,1);
                        if (year == 2020 && month == 3) from = new DateTime(2020,1,1);
                        DateTime to = month == 12
                            ? new DateTime(year,12,31)
                            : new DateTime(year,month,25);
                        DateTime allowed = DateTime.Today.AddDays(1);
                        if (allowed > new DateTime(2027,1,1))
                            allowed = new DateTime(2027,1,1);
                        if (to > allowed) to = allowed;
                        if (from > to) continue; // do not request future-only contracts
                        queue.Enqueue(new Job {
                            Symbol=symbol,Year=year,ExpiryMonth=month,Start=from,End=to,
                            InstrumentName=string.Format(CultureInfo.InvariantCulture,
                                "{0} {1:00}-{2:00}",symbol,month,year%100),
                            Filename=string.Format(CultureInfo.InvariantCulture,
                                "{0}_{1:00}-{2:00}_Minute_Last.txt",symbol,month,year%100)
                        });
                    }
        }

        // Separate the files by each recorded bar's UTC YEAR, not by expiry.
        // E.g. MAR25 December-2024 bars are development, Jan-March-2025 are held out.
        private static string StageForYear(int year)
        {
            if (year >= 2020 && year <= 2024) return "development_2020_2024";
            if (year == 2025) return "validation_holdout_2025";
            if (year == 2026) return "pseudo_forward_holdout_2026";
            throw new InvalidOperationException("Bar year outside 2020-2026");
        }
        private string MarkerFor(Job job)
        {
            return Path.Combine(outputRoot,"completed_jobs",
                Path.GetFileNameWithoutExtension(job.Filename)+".ok");
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
            // Past contracts resume from explicit completion markers; active
            // 2026/2027 requests are refreshed to collect new trading days.
            if (job.Year < 2026 && File.Exists(MarkerFor(job)))
            {
                Log("RESUME: completed "+job.Filename);
                Next();
                return;
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
                            Record(job,0,"FAILED",code+" "+message,"","","");
                        }
                        else
                        {
                            Save(job,request.Bars);
                        }
                    }
                    catch(Exception ex)
                    {
                        Log("ERROR saving "+job.InstrumentName+": "+ex.Message);
                        Record(job,0,"FAILED",ex.Message,"","","");
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
                Record(job,0,"FAILED",ex.Message,"","","");
                if(current!=null){try{current.Dispose();}catch{} current=null;}
                Core.Globals.RandomDispatcher.InvokeAsync(new Action(Next));
            }
        }

        private void Save(Job job, Bars bars)
        {
            if (bars == null || bars.Count == 0)
            {
                Record(job,0,"EMPTY","Provider returned no data","","","");
                Log("EMPTY "+job.InstrumentName);
                return;
            }
            var tz=NinjaTrader.Core.Globals.GeneralOptions.TimeZoneInfo;
            var writers=new Dictionary<int,StreamWriter>();
            var destinations=new Dictionary<int,string>();
            string first="",last="";
            int count=0;
            try
            {
                for(int i=0;i<bars.Count;i++)
                {
                    DateTime local=DateTime.SpecifyKind(bars.GetTime(i),DateTimeKind.Unspecified);
                    DateTime utc=TimeZoneInfo.ConvertTimeToUtc(local,tz);
                    if (utc.Year<2020 || utc.Year>2026) continue;
                    if (utc > DateTime.UtcNow.AddMinutes(1)) continue;
                    int barYear=utc.Year;
                    StreamWriter sw;
                    if (!writers.TryGetValue(barYear,out sw))
                    {
                        string directory=Path.Combine(outputRoot,StageForYear(barYear));
                        Directory.CreateDirectory(directory);
                        string name=job.Filename.Replace("_Minute_Last.txt",
                            "_"+barYear.ToString(CultureInfo.InvariantCulture)+"_Minute_Last.txt");
                        string destination=Path.Combine(directory,name);
                        destinations[barYear]=destination;
                        sw=new StreamWriter(destination+".partial",false,new UTF8Encoding(false));
                        writers[barYear]=sw;
                    }
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
            finally
            {
                foreach(var sw in writers.Values)sw.Dispose();
            }
            bool incomplete=count<20000;
            foreach(var dest in destinations.Values)
            {
                if(incomplete)continue; // preserve .partial until source QC/retry
                if(File.Exists(dest))File.Delete(dest);
                File.Move(dest+".partial",dest);
            }
            string files=string.Join("|",destinations.Values.Select(p=>
                p.Substring(outputRoot.Length+1)).ToArray());
            if(incomplete)
            {
                Record(job,count,"INCOMPLETE",
                    "Under 20000 bars; .partial files retained; check provider",
                    first,last,files);
                Log("INCOMPLETE "+job.InstrumentName+" "+count+" bars");
                return;
            }
            Record(job,count,"EXPORTED","Pending independent structural QC",
                first,last,files);
            if(job.Year<2026)
            {
                Directory.CreateDirectory(Path.GetDirectoryName(MarkerFor(job)));
                File.WriteAllText(MarkerFor(job),count.ToString(CultureInfo.InvariantCulture));
            }
            Log("EXPORTED "+job.InstrumentName+" "+count+" bars to "+files);
        }

        private void Record(Job job,int count,string status,string detail,string first,string last,string files)
        {
            string safe=detail.Replace(',',' ').Replace('\n',' ').Replace('\r',' ');
            var fields=new [] {job.Symbol,job.InstrumentName,job.Year.ToString(CultureInfo.InvariantCulture),
                job.ExpiryMonth.ToString(CultureInfo.InvariantCulture),count.ToString(CultureInfo.InvariantCulture),first,last,status,safe,files};
            File.AppendAllText(manifestPath,string.Join(",",fields)+Environment.NewLine);
        }
        private static void Log(string text)
        {
            NinjaTrader.Code.Output.Process("[NQ/MNQ BULK EXPORT] "+text,PrintTo.OutputTab1);
        }
    }
}