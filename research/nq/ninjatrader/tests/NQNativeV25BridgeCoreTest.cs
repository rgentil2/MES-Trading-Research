// V25 offline contract QA: one-shot frozen transfer, all 120
// V19 families' actual completed-bar directions, M1 stamp, full
// synthetic 36-month NinjaTrader bar evidence, native-vs-V12 fill
// comparisons and fail-closed unsigned/unfrozen input cases.
// NO NinjaTrader runtime, real NQ price series or native validation.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using NinjaTrader.NinjaScript.Strategies;
internal static class NQNativeV25BridgeCoreTest
{
    static readonly CultureInfo I=CultureInfo.InvariantCulture;
    static void A(bool ok,string why)
    {if(!ok)throw new Exception("NQ_V25_BRIDGE_FAIL "+why);}
    static int[] Genes(int family)
    {
        return new[]{1,family*11,12,789,12,999,12,1319,12,
            0,0,0,0,20,32,2,0,14,15,25};
    }
    static string Date(DateTime t)
    {return t.ToString("yyyy-MM-ddTHH:mm:ss",I);}
    static string Num(double v)
    {return v.ToString("R",I);}
    static void WriteNativeBars(string path,
        NQDataLoadV16 source,string freeze)
    {
        using(var w=new StreamWriter(path,false,new UTF8Encoding(false)))
        {
            w.WriteLine("V25LockSHA256\t"+freeze);
            w.WriteLine("minuteStartET\topen\thigh\tlow\tclose\tvolume");
            foreach(var x in source.Bars)
                w.WriteLine(String.Join("\t",new[]{
                    Date(x.Time),Num(x.Bar.Open),Num(x.Bar.High),
                    Num(x.Bar.Low),Num(x.Bar.Close),Num(x.Bar.Volume)
                }));
        }
    }
    static void Sign(string dir)
    {
        var files=Directory.GetFiles(dir)
            .Where(x=>Path.GetFileName(x)!="artifacts.sha256")
            .OrderBy(x=>Path.GetFileName(x),StringComparer.Ordinal)
            .ToArray();
        using(var w=new StreamWriter(
            Path.Combine(dir,"artifacts.sha256"),false,
            new UTF8Encoding(false)))
            foreach(var f in files)
                w.WriteLine(NQNativeReproducibilityV23.SHAFile(f)+
                    "  "+Path.GetFileName(f));
    }
    static void Fixture(string dir,int count,bool approved)
    {
        File.WriteAllText(Path.Combine(dir,"campaign.lock"),
            "version=S0.84_V23_COMPLETE_GENERATOR_FIXED\n"+
            "configSHA256="+new string('b',64)+"\n"+
            "rawSourceSHA256="+new string('c',64)+"\n"+
            "barSeriesSHA256="+new string('a',64)+"\n"+
            "sourcePartition=Development2020_2022\n"+
            "features=120\nconditions=1320\n"+
            "finalInstrument=NQ DEC2026\n"+
            "outOfSampleEvaluated=false\n");
        string result=approved?
            "FROZEN_DEVELOPMENT_ONLY_READY_FOR_EXTERNAL":
            "PORTFOLIO_RISK_OR_DIVERSITY_REJECT";
        File.WriteAllText(Path.Combine(dir,"run_summary.txt"),
            "S0.84 V23 COMPLETE GENERATOR RESEARCH ONLY\n"+
            "status="+result+"\n"+
            "sourceBarsSHA256="+new string('a',64)+"\n"+
            "configurationSHA256="+new string('b',64)+"\n"+
            "instrument=NQ DEC2026\n"+
            "frozenForExternal="+(approved?count:0)+"\n"+
            "externalOosOpened=false\nfinalOosOpened=false\n");
        var ids=Enumerable.Range(1,count).Select(x=>
            "NQ-"+x.ToString("D5")).ToArray();
        File.WriteAllText(Path.Combine(dir,"portfolio_decision.tsv"),
            "result\tmembers\tnetUSD\tclosedDDUSD\tmaxMonthlyCorrelation"+
            "\tmaxProfitContribution\tadversarialStressDDUSD"+
            "\tmaxDailyLossUSD\tmaxConcurrentAdverseUSD"+
            "\tmaxConcurrentContracts\tfreezeDigest\n"+
            result+"\t"+String.Join(",",ids)+
            "\t900\t500\t0.1\t0.35\t900\t450\t250\t3\t"+
            new string('d',64)+"\n");
        var frozen=new List<NQFrozenCandidateV16>();
        for(int i=0;i<count;i++)
            frozen.Add(new NQFrozenCandidateV16(ids[i],
                Genes(36+i),NQNativeExitCanonicalV19.Analyze));
        NQNativeCompleteGeneratorV23.WriteFrozenParameterFile(
            Path.Combine(dir,"definitive_parameters.tsv"),
            approved?frozen:new List<NQFrozenCandidateV16>());
        File.WriteAllText(Path.Combine(dir,"settings_snapshot.tsv"),
            "configurationKey\tcanonicalValue\n"+
            "V23.ContractPolicy\t"+
            Convert.ToBase64String(Encoding.UTF8.GetBytes(
                "SYNTHETIC_WEEKDAY_ONLY"))+"\n"+
            "V23.MinimumFullSessionsPerMonth\t15\n"+
            "V23.Research.AccountRisk.MaxAccountStressDDUSD\t2000\n"+
            "V23.Research.AccountRisk.MaxSessionPeakToTroughUSD\t1000\n"+
            "V23.Research.AccountRisk.MaxConcurrentAdverseUSD\t1000\n"+
            "V23.Research.AccountRisk.PointValueUSD\t20\n");
        File.WriteAllText(Path.Combine(dir,"candidates_full.tsv"),
            "synthetic-contract-test-only\n");
        File.WriteAllText(Path.Combine(dir,"rejected_candidates.tsv"),
            "synthetic-contract-test-only\n");
        Sign(dir);
    }
    static void SignalParity()
    {
        int matched=0,emitted=0;
        var source=NQNativeSynthetic36V24.Build();
        var sample=source.Bars.Take(210*25).ToArray();
        for(int family=0;family<120;family++)
        {
            var g=Genes(family);
            var core=new NQNativeV25FrozenSignalCore(g);
            var prefix=new List<NQBarV11>();
            DateTime lastDay=DateTime.MinValue;
            foreach(var item in sample)
            {
                if(item.Time.Date!=lastDay)
                {prefix.Clear();lastDay=item.Time.Date;}
                int clock=item.Time.Hour*100+item.Time.Minute;
                if(clock>=930&&clock<=1127)
                    prefix.Add(item.Bar);
                var decision=core.PushCompletedBar(item.Time,item.Bar);
                bool b=false,s=false;
                if(clock>=935&&clock<=1127 &&
                   prefix.Count>=NQNativeConditionCatalogV19.RequiredBars(12))
                    NQNativeConditionCatalogV19.TryEvaluate(
                        prefix,family*11,12,out b,out s);
                int direction=b==s?0:b?1:-1;
                A((decision==null?0:decision.Side)==direction,
                  "V25 frozen signal diverged from V19 formula f="+family);
                matched++;
                if(decision!=null)emitted++;
            }
        }
        A(matched==120*sample.Length&&emitted>1000,
          "all 120 exact indicator formulas signal-core parity");
        A(NQNativeV25FrozenSignalCore.NinjaTraderMinuteStart(
            new DateTime(2026,3,9,9,31,0))==
            new DateTime(2026,3,9,9,30,0),
          "NT8 end-stamped minute subtract 1m after DST switch");
        try
        {
            NQNativeV25FrozenSignalCore.NinjaTraderMinuteStart(
                DateTime.SpecifyKind(
                    new DateTime(2026,3,9,9,31,0),DateTimeKind.Utc));
            throw new Exception("V25_ACCEPTED_UTC_NT8_BAR");
        }
        catch(ArgumentException){}
        Console.WriteLine("NQ_V25_SIGNAL_PARITY_PASS families=120"+
            " checked="+matched+" emitted="+emitted+
            " EOD_M1_to_ET_start=TRUE");
    }
    static void FillAudit()
    {
        var expected=new NQHistoricalResultV12{Valid=true};
        var when=new DateTime(2020,1,2,10,25,0);
        for(int k=0;k<2;k++)
        {
            DateTime entry=when.AddDays(k),exit=entry.AddMinutes(3);
            int side=k==0?1:-1;
            double ep=15000+k*25,xp=ep+side*2.0;
            double pnl=(xp-ep)*side*20-4.68;
            expected.Executed.Add(new NQExecutionFillV12(
                entry,exit,side,1,ep,xp,4.68));
            expected.Trades.Add(new NQG0RiskTradeV7(
                entry,exit,pnl,25,50));
            expected.Net+=pnl;
        }
        var native=expected.Executed.Select(x=>
            new NQNativeV25NativeTrade{
                EntryTimeET=x.EntryTime,ExitTimeET=x.ExitTime,
                Side=x.Side,Quantity=x.Quantity,
                EntryPrice=x.EntryPrice,ExitPrice=x.ExitPrice,
                NetUnderResearchFee=
                    (x.ExitPrice-x.EntryPrice)*x.Side*20-4.68
            }).ToList();
        var ok=NQNativeV25ParityAudit.Compare(expected,native,
            new NQNativeV25ParityTolerance());
        A(ok.Complete&&ok.ProvisionalPass&&ok.Matched==2,
          "native identical expected time/price/fee P&L and DD passes");
        native[1].ExitPrice+=5.0;
        native[1].NetUnderResearchFee+=5*20*(-1);
        var bad=NQNativeV25ParityAudit.Compare(expected,native,
            new NQNativeV25ParityTolerance());
        A(bad.Complete&&!bad.ProvisionalPass&&bad.Matched==1,
          "wrong native exit price and net reject");
        native.RemoveAt(1);
        A(NQNativeV25ParityAudit.Compare(expected,native,
            new NQNativeV25ParityTolerance()).Status==
            "TRADE_COUNT_MISMATCH",
          "dropped native trade cannot pass reconciliation");
        Console.WriteLine("NQ_V25_NATIVE_FILL_COMPARISON_PASS "+
            "exactAccepted=2 changedPriceRejected=TRUE"+
            " missingTradeRejected=TRUE");
    }
    public static int Main()
    {
        string dir=Path.Combine(Path.GetTempPath(),
            "NQV25_"+Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(dir);
        try
        {
            SignalParity();FillAudit();
            string package=Path.Combine(dir,"v23");
            Directory.CreateDirectory(package);
            Fixture(package,3,true);
            var three=NQNativeV25FrozenImporter.Load(package);
            A(three.Candidates.Count==3&&
              three.Candidates.Select(x=>x.CanonicalId)
                .Distinct().Count()==3&&
              three.MinimumFullSessionsPerMonth==15&&
              three.AccountRisk.MaxAccountStressDDUSD==2000,
              "3 approved fixture candidates map to exact 20 genes and risks");
            string handoff=Path.Combine(dir,"handoff.tsv");
            NQNativeV25FrozenImporter.WriteHandoff(three,handoff);
            A(File.ReadAllLines(handoff).Length==8&&
              File.ReadAllText(handoff).Contains(three.V25LockSHA256),
              "versioned frozen transfer contains same immutable 3 genomes");
            Fixture(package,5,true);
            var five=NQNativeV25FrozenImporter.Load(package);
            A(five.Candidates.Count==5&&
              five.Candidates.All(x=>x.CanonicalId.StartsWith("EXCANv19:")),
              "5 member handoff is also accepted");
            Fixture(package,3,false);
            try
            {
                NQNativeV25FrozenImporter.Load(package);
                throw new Exception("V25_UNFROZEN_DEV_ACCEPTED");
            }
            catch(InvalidDataException ex)
            {A(ex.Message.Contains("NO_REAL_DEV_APPROVED"),
                "real V23 rejected research cannot be promoted to NT8");}
            Fixture(package,3,true);
            File.AppendAllText(Path.Combine(package,
                "definitive_parameters.tsv"),"tamper");
            try
            {
                NQNativeV25FrozenImporter.Load(package);
                throw new Exception("V25_BAD_FROZEN_FILE_ACCEPTED");
            }
            catch(InvalidDataException ex)
            {A(ex.Message.Contains("ARTIFACT"),
                "tampered V23 gene artifact fails before NT8");}

            // 164430 synthetic bars, 36 complete months with >=15
            // weekdays. Native receipts must reproduce source BAR BY
            // BAR (times, prices and volume), not merely trade totals.
            var synthetic=NQNativeSynthetic36V24.Build();
            var barFile=Path.Combine(dir,"nativeBars.tsv");
            WriteNativeBars(barFile,synthetic,three.V25LockSHA256);
            var parsed=NQNativeV25NativeBarsReader.Load(
                barFile,three.V25LockSHA256,
                NQDataPartitionV16.Development2020_2022,
                "NQ DEC2026","SYNTHETIC_WEEKDAY_ONLY",15);
            NQNativeV25NativeBarsReader.RequireBarByBarEquality(
                synthetic.Bars,parsed.Bars);
            A(parsed.Bars.Count==164430&&
              parsed.Manifest.CompleteRthDays==783,
              "164430 native M1, 783 full synthetic sessions 2020-22");
            var perturbed=parsed.Bars.ToArray();
            var b=perturbed[10];
            var x=b.Bar;
            perturbed[10]=new NQTimedBarV12(b.Time,new NQBarV11(
                x.Open,x.High,x.Low,x.Close,x.Volume+1));
            try
            {
                NQNativeV25NativeBarsReader.RequireBarByBarEquality(
                    synthetic.Bars,perturbed);
                throw new Exception("V25_BAR_DIFF_ACCEPTED");
            }
            catch(InvalidDataException ex)
            {A(ex.Message.Contains("SOURCE_MISMATCH"),
                "a single volume difference fails source parity");}
            Console.WriteLine("NQ_V25_FROZEN_HANDOFF_PASS "+
                "approvedFixture3And5=TRUE rejectedDevFailClosed=TRUE"+
                " alteredGeneSHARejected=TRUE"+
                " strictNativeBars=164430"+
                " sourceBarMismatchRejected=TRUE");
            Console.WriteLine("V25_CI_SYNTHETIC_OR_FIXED_FIXTURES_ONLY "+
                "NO_ACTUAL_NQ_FROZEN_PORTFOLIO_OR_NATIVE_NT8_RUN");
            return 0;
        }
        finally{Directory.Delete(dir,true);}
    }
}
