// S0.84 V23: one auditable, reproducible end-to-end research
// package. Executes the EXISTING V22 research funnel once, captures
// each V13 G0 rejection with real M1 fill receipts, writes every
// genetic candidate's full compact economic ranking (V21 ledger),
// audited 2020–22 month/year profiles, portfolio & walk-forward
// decisions, and immutable frozen-genes parameters ONLY on DEV PASS.
// No OOS data passed here. No native NinjaTrader order API.
// A frozen candidate is provisional research, NOT real market edge.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQCandidateAuditRecordV23
    {
        public string Canonical,AcceptedId,Reason;
        public bool Valid,PassedG0,PassedCostStress,PassedMonteCarlo;
        public int Trades,MonthsBelowFive;
        public double NetUSD,PF,DDUSD,CostStressNetUSD,BootstrapP95DD;
        public readonly List<NQPeriodMetricsV23> Monthly=
            new List<NQPeriodMetricsV23>();
        public readonly List<NQPeriodMetricsV23> Annual=
            new List<NQPeriodMetricsV23>();
    }
    public sealed class NQPeriodMetricsV23
    {
        public int Year,Month,Trades;
        public double NetUSD,ProfitFactor,ClosedDDUSD;
    }
    public sealed class NQCompleteRunV23
    {
        public string Reason,OutputDirectory,PackageSHA256;
        public bool Completed,HasFrozenCandidates;
        public int Generated,Audited,IndividualPassed,FreezeCount;
        public int FreshBacktests,ReusedBacktests;
        public NQResearchRunV22 Research;
        public readonly List<string> ArtifactNames=new List<string>();
    }

    public static class NQNativeCompleteGeneratorV23
    {
        static readonly CultureInfo I=CultureInfo.InvariantCulture;
        static string Num(double x){return x.ToString("R",I);}
        static string Int(int x){return x.ToString(I);}
        static string B64(string s)
        {return Convert.ToBase64String(Encoding.UTF8.GetBytes(s??""));}
        static string Genes(int[] g)
        {return String.Join("/",g.Select(x=>x.ToString(I)));}
        static string Safe(string s)
        {return (s??"").Replace("\r"," ").Replace("\n"," ")
                       .Replace("\t"," ");}

        static void Atomic(string path,Action<StreamWriter> render)
        {
            string pending=path+".tmp";
            try
            {
                using(var w=new StreamWriter(pending,false,
                    new UTF8Encoding(false)))
                    render(w);
                if(File.Exists(path))File.Delete(path);
                File.Move(pending,path);
            }
            finally{if(File.Exists(pending))File.Delete(pending);}
        }
        static NQPeriodMetricsV23 Period(
            IList<NQG0RiskTradeV7> trades,int year,int month)
        {
            double net=0,wins=0,loss=0,peak=0,dd=0;
            int n=0;
            foreach(var t in trades)
            {
                if(t.EntryTime.Year!=year||
                   month!=0&&t.EntryTime.Month!=month)
                    continue;
                n++;net+=t.NetProfitUSD;
                peak=Math.Max(peak,net);
                dd=Math.Max(dd,peak-net);
                if(t.NetProfitUSD>0)wins+=t.NetProfitUSD;
                else if(t.NetProfitUSD<0)loss-=t.NetProfitUSD;
            }
            return new NQPeriodMetricsV23{
                Year=year,Month=month,Trades=n,NetUSD=net,
                ProfitFactor=loss>0?wins/loss:wins>0?100:0,
                ClosedDDUSD=dd
            };
        }

        static NQCandidateAuditRecordV23 Observe(
            string canonical,string id,NQHistoricalResultV12 economic,
            NQRobustnessResultV13 robust)
        {
            var record=new NQCandidateAuditRecordV23{
                Canonical=canonical,AcceptedId=id,
                Valid=economic!=null&&economic.Valid,
                PassedG0=robust!=null&&robust.Valid&&
                    robust.ProvisionalG0Pass,
                PassedCostStress=robust!=null&&robust.Valid&&
                    robust.CostStressPositive,
                PassedMonteCarlo=robust!=null&&robust.Valid&&
                    robust.MonteCarloRiskPass,
                CostStressNetUSD=robust==null?0:robust.CostStressNetUSD,
                BootstrapP95DD=robust==null?0:
                    robust.BootstrapP95ClosedDrawdownUSD
            };
            var reasons=new List<string>();
            if(economic==null||!economic.Valid)
            {
                reasons.Add("V12_INVALID_"+(economic==null?
                    "NULL":economic.Reason));
                record.Reason=String.Join(",",reasons);
                return record;
            }
            record.Trades=economic.Trades.Count;
            record.NetUSD=economic.Net;
            double win=0,loss=0,peak=0,equity=0,dd=0;
            foreach(var trade in economic.Trades)
            {
                if(trade.NetProfitUSD>0)win+=trade.NetProfitUSD;
                if(trade.NetProfitUSD<0)loss-=trade.NetProfitUSD;
                equity+=trade.NetProfitUSD;
                peak=Math.Max(peak,equity);dd=Math.Max(dd,peak-equity);
            }
            record.PF=loss>0?win/loss:win>0?100:0;
            record.DDUSD=dd;
            for(int year=2020;year<=2022;year++)
            {
                record.Annual.Add(Period(economic.Trades,year,0));
                for(int month=1;month<=12;month++)
                {
                    var item=Period(economic.Trades,year,month);
                    record.Monthly.Add(item);
                    if(item.Trades<5)record.MonthsBelowFive++;
                }
            }
            if(robust==null||!robust.Valid)
                reasons.Add("V13_INVALID_"+(robust==null?
                    "NULL":robust.Reason));
            else
            {
                if(!robust.ProvisionalG0Pass)
                {
                    if(robust.G0Diagnostics!=null&&
                       robust.G0Diagnostics.AllFailures!=null)
                        reasons.AddRange(robust.G0Diagnostics.AllFailures);
                    else reasons.Add("V6_V7_G0_REJECT");
                }
                if(!robust.CostStressPositive)
                    reasons.Add("COST_1_5X_NONPOSITIVE");
                if(!robust.MonteCarloRiskPass)
                    reasons.Add("BOOTSTRAP_P95_DD_EXCEEDED");
            }
            record.Reason=reasons.Count==0?
                "INDIVIDUAL_G0_MC_STRESS_PASS":
                String.Join(",",reasons.Distinct());
            return record;
        }

        static void AuditTrades(StreamWriter writer,string canonical,
            string id,NQHistoricalResultV12 economic)
        {
            if(economic==null||!economic.Valid)return;
            if(economic.Executed.Count!=economic.Trades.Count)
                throw new InvalidOperationException(
                    "V23_AUDIT_TRADE_FILL_COUNT_MISMATCH");
            for(int i=0;i<economic.Executed.Count;i++)
            {
                var e=economic.Executed[i];
                var trade=economic.Trades[i];
                if(e.EntryTime!=trade.EntryTime||
                   e.ExitTime!=trade.ExitTime)
                    throw new InvalidOperationException(
                        "V23_AUDIT_ENTRY_EXIT_TIME_MISMATCH");
                writer.WriteLine(String.Join("\t",new[]{
                    B64(canonical),Safe(id),
                    e.EntryTime.ToString("yyyy-MM-ddTHH:mm:ss",I),
                    e.ExitTime.ToString("yyyy-MM-ddTHH:mm:ss",I),
                    Int(e.Side),Int(e.Quantity),
                    Num(e.EntryPrice),Num(e.ExitPrice),
                    Num(e.RoundTripFeesUSD),
                    Num(trade.NetProfitUSD),Num(trade.MaeCurrency),
                    Num(trade.MfeCurrency)
                }));
            }
        }

        public static NQCompleteRunV23 Run(
            NQDataLoadV16 development,NQGeneratorSettingsV23 cfg)
        {
            if(cfg==null||development==null||
               development.Manifest==null||development.Bars==null)
                throw new ArgumentException("V23_CONFIG_AND_DEV_SOURCE_REQUIRED");
            cfg.Validate();
            if(development.Manifest.Partition!=
                   NQDataPartitionV16.Development2020_2022||
               !String.Equals(development.Manifest.Instrument,
                   cfg.Instrument,StringComparison.Ordinal)||
               !String.Equals(development.Manifest.ContractPolicy,
                   cfg.ContractPolicy,StringComparison.Ordinal)||
               development.Manifest.FullSessionsByMonth==null||
               development.Manifest.FullSessionsByMonth.Length!=36)
                throw new InvalidOperationException(
                    "V23_DEVELOPMENT_SOURCE_OR_INSTRUMENT_MISMATCH");
            string target=Path.GetFullPath(cfg.OutputDirectory);
            Directory.CreateDirectory(target);
            string lockText=NQNativeReproducibilityV23.LockText(
                cfg,development);
            string lockPath=Path.Combine(target,"campaign.lock");
            if(File.Exists(lockPath)&&
               File.ReadAllText(lockPath)!=lockText)
                throw new InvalidOperationException(
                    "V23_CONFIG_SOURCE_OR_CODE_VERSION_MISMATCH");
            if(!File.Exists(lockPath))
                Atomic(lockPath,w=>w.Write(lockText));
            var observed=new Dictionary<string,NQCandidateAuditRecordV23>(
                StringComparer.Ordinal);
            string tradeFile=Path.Combine(target,"audited_trades.tsv");
            string auditPending=tradeFile+".tmp";
            NQResearchRunV22 research;
            try
            {
                using(var writer=new StreamWriter(auditPending,false,
                    new UTF8Encoding(false)))
                {
                    writer.WriteLine("canonicalBase64\tstrategyId\tentryET"+
                        "\texitET\tside\tcontracts\tentryPrice\texitPrice"+
                        "\tfeesUSD\tnetUSD\tMAEUSD\tMFEUSD");
                    research=NQNativeResearchRunnerV22.Run(
                        development,cfg.BaselineGenes,cfg.Research,
                        Path.Combine(target,"economics_ledger.tsv"),
                        Path.Combine(target,"ranking_top.tsv"),
                        Path.Combine(target,"finalist_trades.tsv"),
                        cfg.RankingCount,cfg.FeatureCacheBytes,cfg.Audit,
                        (key,id,run,risk)=>
                        {
                            if(observed.ContainsKey(key))
                                throw new InvalidOperationException(
                                    "V23_DUPLICATE_AUDIT_CANONICAL");
                            observed.Add(key,Observe(key,id,run,risk));
                            AuditTrades(writer,key,id,run);
                        });
                }
                if(File.Exists(tradeFile))File.Delete(tradeFile);
                File.Move(auditPending,tradeFile);
            }
            finally
            {if(File.Exists(auditPending))File.Delete(auditPending);}
            var result=new NQCompleteRunV23{
                Research=research,
                Reason=research.Reason,
                Completed=research.Completed,
                HasFrozenCandidates=research.HasFrozenCandidates,
                OutputDirectory=target,
                Generated=research.GeneticEvaluated,
                Audited=observed.Count,
                IndividualPassed=research.RobustnessPassed,
                FreshBacktests=research.Bulk==null?0:
                    research.Bulk.NewEconomicBacktests,
                ReusedBacktests=research.Bulk==null?0:
                    research.Bulk.ReusedEconomicBacktests,
                FreezeCount=research.Audit==null?0:
                    research.Audit.Frozen.Count
            };
            Publish(target,cfg,development,research,observed,result);
            return result;
        }

        static void Publish(string target,NQGeneratorSettingsV23 cfg,
            NQDataLoadV16 development,NQResearchRunV22 research,
            Dictionary<string,NQCandidateAuditRecordV23> observed,
            NQCompleteRunV23 result)
        {
            // V21 ledger exists even when the V22 portfolio cannot
            // pass; return one economic row per GA-scored unique genome.
            var ledgerRows=new Dictionary<string,NQEconomicRowV21>(
                StringComparer.Ordinal);
            string ledgerPath=Path.Combine(target,"economics_ledger.tsv");
            if(research.Bulk!=null)
            {
                using(var read=new NQNativeEconomicLedgerV21(
                    ledgerPath,development.Manifest.Sha256,
                    research.Bulk.CampaignSHA256))
                    foreach(var item in read.Ranked)
                        ledgerRows.Add(item.Canonical,item);
                if(ledgerRows.Count!=research.GeneticEvaluated)
                    throw new InvalidOperationException(
                        "V23_LEDGER_AND_GENETIC_RANK_COUNT_MISMATCH");
            }
            var ranked=research.Genetic==null?
                new List<NQEvolutionIndividualV12>():
                research.Genetic.Evaluated
                    .OrderByDescending(x=>x.Score)
                    .ThenBy(x=>x.Genome.Canonical.RuntimeKey,
                        StringComparer.Ordinal).ToList();
            var selected=new HashSet<string>(StringComparer.Ordinal);
            if(research.PortfolioRisk!=null&&
               research.PortfolioRisk.Selection!=null)
                foreach(var x in research.PortfolioRisk.Selection.Selected)
                    selected.Add(x.Id);
            var frozen=new HashSet<string>(StringComparer.Ordinal);
            if(research.Audit!=null)
                foreach(var x in research.Audit.Frozen)
                    frozen.Add(x.CanonicalId);
            Func<string,NQCandidateAuditRecordV23,string> stage=(key,a)=>
            {
                if(frozen.Contains(key))return "FROZEN_FOR_EXTERNAL_OOS";
                if(a==null)return "SCORED_NOT_AUDITED";
                if(String.IsNullOrWhiteSpace(a.AcceptedId))
                    return "REJECTED_INDIVIDUAL";
                if(selected.Contains(a.AcceptedId))
                    return "SELECTED_BUT_PORTFOLIO_OR_WF_BLOCKED";
                return "INDIVIDUAL_PASS_NOT_SELECTED";
            };
            Func<string,NQCandidateAuditRecordV23,string> why=(key,a)=>
            {
                if(frozen.Contains(key))return "DEV_PROVISIONAL_PASS";
                if(a==null)return "BEYOND_CANDIDATE_AUDIT_LIMIT";
                if(String.IsNullOrWhiteSpace(a.AcceptedId))
                    return a.Reason;
                if(selected.Contains(a.AcceptedId))
                    return research.Reason;
                return "PORTFOLIO_DIVERSITY_OR_RANK_NOT_SELECTED";
            };

            Atomic(Path.Combine(target,"candidates_full.tsv"),w=>
            {
                w.WriteLine("rank\tcanonicalBase64\tstrategyId"+
                    "\tbirthGeneration\tgeneticScore\tnetUSD"+
                    "\tprofitFactor\tclosedDDUSD\ttrades"+
                    "\tcostStressNetUSD\tbootstrapP95DDUSD"+
                    "\tauditStatus\treason\tgenes20");
                int rank=0;
                foreach(var v in ranked)
                {
                    string key=v.Genome.Canonical.RuntimeKey;
                    NQEconomicRowV21 e;NQCandidateAuditRecordV23 a;
                    if(!ledgerRows.TryGetValue(key,out e))
                        throw new InvalidOperationException(
                            "V23_MISSING_SCORE_LEDGER_ROW");
                    observed.TryGetValue(key,out a);
                    w.WriteLine(String.Join("\t",new[]{
                        Int(++rank),B64(key),a==null?"":Safe(a.AcceptedId),
                        Int(v.BirthGeneration),Num(v.Score),Num(e.Net),
                        Num(e.ProfitFactor),Num(e.ClosedDrawdown),
                        Int(e.Trades),
                        a==null?"":Num(a.CostStressNetUSD),
                        a==null?"":Num(a.BootstrapP95DD),
                        stage(key,a),Safe(why(key,a)),
                        Genes(v.Genome.Genes)
                    }));
                }
            });
            Atomic(Path.Combine(target,"rejected_candidates.tsv"),w=>
            {
                w.WriteLine("canonicalBase64\tstage\treason\t"+
                    "audited\tselectedPortfolio");
                foreach(var v in ranked)
                {
                    string key=v.Genome.Canonical.RuntimeKey;
                    if(frozen.Contains(key))continue;
                    NQCandidateAuditRecordV23 a;
                    observed.TryGetValue(key,out a);
                    w.WriteLine(String.Join("\t",new[]{
                        B64(key),stage(key,a),Safe(why(key,a)),
                        a==null?"0":"1",
                        a!=null&&selected.Contains(a.AcceptedId)?"1":"0"
                    }));
                }
            });
            Atomic(Path.Combine(target,"annual_development.tsv"),w=>
            {
                w.WriteLine("canonicalBase64\tstrategyId\tyear\ttrades"+
                    "\tnetUSD\tprofitFactor\tclosedDDUSD");
                foreach(var a in observed.Values.OrderBy(
                    x=>x.Canonical,StringComparer.Ordinal))
                    foreach(var p in a.Annual)
                        w.WriteLine(String.Join("\t",new[]{
                            B64(a.Canonical),Safe(a.AcceptedId),
                            Int(p.Year),Int(p.Trades),Num(p.NetUSD),
                            Num(p.ProfitFactor),Num(p.ClosedDDUSD)
                        }));
            });
            Atomic(Path.Combine(target,"monthly_development.tsv"),w=>
            {
                w.WriteLine("canonicalBase64\tyear\tmonth\ttrades"+
                    "\tnetUSD\tprofitFactor\tclosedDDUSD"+
                    "\tmeets5TradeMinimum");
                foreach(var a in observed.Values.OrderBy(
                    x=>x.Canonical,StringComparer.Ordinal))
                    foreach(var p in a.Monthly)
                        w.WriteLine(String.Join("\t",new[]{
                            B64(a.Canonical),Int(p.Year),Int(p.Month),
                            Int(p.Trades),Num(p.NetUSD),Num(p.ProfitFactor),
                            Num(p.ClosedDDUSD),p.Trades>=5?"1":"0"
                        }));
            });
            Atomic(Path.Combine(target,"robustness_audits.tsv"),w=>
            {
                w.WriteLine("canonicalBase64\tstrategyId\ttrades"+
                    "\tmonthsBelow5\tG0\tcost15x\tMonteCarlo"+
                    "\tcostStressNetUSD\tbootstrapP95DDUSD"+
                    "\tallReasons");
                foreach(var a in observed.Values.OrderBy(
                    x=>x.Canonical,StringComparer.Ordinal))
                    w.WriteLine(String.Join("\t",new[]{
                        B64(a.Canonical),Safe(a.AcceptedId),
                        Int(a.Trades),Int(a.MonthsBelowFive),
                        a.PassedG0?"1":"0",
                        a.PassedCostStress?"1":"0",
                        a.PassedMonteCarlo?"1":"0",
                        Num(a.CostStressNetUSD),Num(a.BootstrapP95DD),
                        Safe(a.Reason)
                    }));
            });
            Atomic(Path.Combine(target,"walkforward.tsv"),w=>
            {
                w.WriteLine("fold\ttrainingStart\ttrainingEnd"+
                    "\tvalidationStart\tvalidationEnd\twinnerBase64"+
                    "\ttrainingNetUSD\ttrainingPF\tvalidationNetUSD"+
                    "\tvalidationPF\tvalidationClosedDDUSD"+
                    "\tvalidationGate\tvalidatedOnDevOnly");
                if(research.WalkForward!=null)
                    for(int i=0;i<research.WalkForward.Folds.Count;i++)
                    {
                        var f=research.WalkForward.Folds[i];
                        w.WriteLine(String.Join("\t",new[]{
                            Int(i+1),f.TrainingBegin.ToString("yyyy-MM-dd",I),
                            f.TrainingEnd.ToString("yyyy-MM-dd",I),
                            f.ValidationBegin.ToString("yyyy-MM-dd",I),
                            f.ValidationEnd.ToString("yyyy-MM-dd",I),
                            B64(f.ChosenCanonicalId??""),
                            f.Training==null?"":Num(f.Training.NetUSD),
                            f.Training==null?"":Num(f.Training.ProfitFactor),
                            f.Validation==null?"":Num(f.Validation.NetUSD),
                            f.Validation==null?"":Num(f.Validation.ProfitFactor),
                            f.Validation==null?"":Num(f.Validation.ClosedDDUSD),
                            f.Validation!=null&&f.Validation.PeriodGatePass?"1":"0",
                            "1"
                        }));
                    }
            });
            Atomic(Path.Combine(target,"portfolio_decision.tsv"),w=>
            {
                w.WriteLine("result\tmembers\tnetUSD\tclosedDDUSD"+
                    "\tmaxMonthlyCorrelation\tmaxProfitContribution"+
                    "\tadversarialStressDDUSD\tmaxDailyLossUSD"+
                    "\tmaxConcurrentAdverseUSD\tmaxConcurrentContracts"+
                    "\tfreezeDigest");
                var r=research.PortfolioRisk;
                var p=r==null?null:r.Selection;
                var risk=r==null?null:r.Chronology;
                w.WriteLine(String.Join("\t",new[]{
                    Safe(research.Reason),
                    p==null?"":String.Join(",",p.Selected.Select(x=>x.Id)),
                    p==null?"":Num(p.NetProfitUSD),
                    p==null?"":Num(p.ClosedDrawdownUSD),
                    p==null?"":Num(p.WorstPairwiseMonthlyCorrelation),
                    p==null?"":Num(p.LargestProfitContribution),
                    risk==null?"":Num(risk.MaxAdversarialM1StressDDUSD),
                    risk==null?"":Num(risk.MaxSessionPeakToTroughUSD),
                    risk==null?"":Num(risk.MaxConcurrentAdverseUSD),
                    risk==null?"":Int(risk.MaxConcurrentContracts),
                    research.FrozenCampaign==null?"":research.FrozenCampaign.FreezeDigest
                }));
            });
            Atomic(Path.Combine(target,"definitive_parameters.tsv"),w=>
            {
                w.WriteLine("strategyId\tcanonicalBase64\tgeneIndex"+
                    "\tparameter\tvalue\tdescription");
                if(research.Audit!=null)
                    foreach(var x in research.Audit.Frozen.OrderBy(
                        s=>s.Id,StringComparer.Ordinal))
                    {
                        var g=x.Genes;
                        for(int j=0;j<g.Length;j++)
                        {
                            string param=j==0?"leafCount":
                                j<=8?(j%2==1?"signalType":"period"):
                                j<=11?"booleanOperator":
                                j==12?"reverse":j==13?"stopTicks":
                                j==14?"profitTargetTicks":
                                j==15?"dailyTradeLimit":
                                j==16?"exitMode":j==17?"atrPeriod":
                                j==18?"atrStopFactor":
                                "atrTakeProfitFactor";
                            string meaning="";
                            if(j<=8&&j>=1&&j%2==1&&
                               (j-1)/2<g[0])
                                meaning=NQNativeConditionCatalogV19.Name(g[j]);
                            w.WriteLine(String.Join("\t",new[]{
                                Safe(x.Id),B64(x.CanonicalId),
                                Int(j),param,Int(g[j]),Safe(meaning)
                            }));
                        }
                    }
            });
            Atomic(Path.Combine(target,"settings_snapshot.tsv"),w=>
            {
                w.WriteLine("configurationKey\tcanonicalValue");
                foreach(var line in NQNativeReproducibilityV23
                        .CanonicalSettings(cfg))
                {
                    int pos=line.IndexOf('=');
                    w.WriteLine(line.Substring(0,pos)+"\t"+
                        line.Substring(pos+1));
                }
            });
            Atomic(Path.Combine(target,"run_summary.txt"),w=>
            {
                w.WriteLine("S0.84 V23 COMPLETE GENERATOR RESEARCH ONLY");
                w.WriteLine("scope=V23_UNCHANGED");
                w.WriteLine("status="+Safe(research.Reason));
                w.WriteLine("sourcePartition=2020_2022_DEVELOPMENT_ONLY");
                w.WriteLine("rawSourceSHA256="+development.Manifest.Sha256);
                w.WriteLine("sourceBarsSHA256="+
                    NQNativeReproducibilityV23.SourceBarsHash(development));
                w.WriteLine("configurationSHA256="+
                    NQNativeReproducibilityV23.ConfigurationHash(cfg));
                w.WriteLine("instrument="+Safe(development.Manifest.Instrument));
                w.WriteLine("indicatorFormulas=120");
                w.WriteLine("conditionTypes=1320");
                w.WriteLine("GAUniqueGenomes="+result.Generated);
                // Replay must produce byte-identical reports. Fresh vs
                // reused callbacks belong to the CLI runtime message,
                // not to the canonical frozen research package.
                w.WriteLine("economicGenomeRows="+result.Generated);
                w.WriteLine("robustAudited="+result.Audited);
                w.WriteLine("individualPassed="+result.IndividualPassed);
                w.WriteLine("frozenForExternal="+result.FreezeCount);
                w.WriteLine("externalOosOpened=false");
                w.WriteLine("finalOosOpened=false");
                w.WriteLine("NinjaTraderNativeFillsValidated=false");
                w.WriteLine("fundedAccountApproved=false");
                w.WriteLine("noApprovedPortfolioIsNotFailureOfSoftware=true");
                w.WriteLine("auditedTrades=ALL_SHORTLIST_ONLY");
                w.WriteLine("annualMonthlyReports=ROBUSTNESS_AUDITED_ONLY");
                w.WriteLine("walkForwardMeaning=GENERATOR_TRAIN_ONLY_4_FOLDS");
                w.WriteLine("contractRollAuditsNotRepeated=true");
                w.WriteLine("V24=LONG_HORIZON_100K_ECONOMIC_SCALING");
                w.WriteLine("V25=SINGLE_FINAL_NT8_VALIDATION");
            });

            // Every resulting file gets a content checksum. File list is
            // stable and sorted; manifest digest is its exact SHA256.
            var files=Directory.GetFiles(target,"*.tsv")
                .Select(Path.GetFileName).ToList();
            files.Add("campaign.lock");files.Add("run_summary.txt");
            files=files.Distinct(StringComparer.Ordinal)
                .OrderBy(s=>s,StringComparer.Ordinal).ToList();
            string checksumPath=Path.Combine(target,"artifacts.sha256");
            Atomic(checksumPath,w=>
            {
                foreach(var file in files)
                    w.WriteLine(NQNativeReproducibilityV23.SHAFile(
                        Path.Combine(target,file))+"  "+file);
            });
            result.ArtifactNames.AddRange(files);
            result.ArtifactNames.Add("artifacts.sha256");
            result.PackageSHA256=NQNativeReproducibilityV23.SHAFile(
                checksumPath);
        }

        public static void Verify(string directory)
        {
            string root=Path.GetFullPath(directory);
            string checks=Path.Combine(root,"artifacts.sha256");
            if(!File.Exists(checks))
                throw new FileNotFoundException(
                    "V23_MISSING_ARTIFACT_MANIFEST",checks);
            var files=new HashSet<string>(StringComparer.Ordinal);
            foreach(string line in File.ReadAllLines(checks))
            {
                int pos=line.IndexOf("  ",StringComparison.Ordinal);
                if(pos!=64||line.Length<=66)
                    throw new InvalidDataException(
                        "V23_INVALID_ARTIFACT_CHECKSUM_ENTRY");
                string name=line.Substring(66);
                if(name!=Path.GetFileName(name)||
                   !files.Add(name)||!File.Exists(Path.Combine(root,name))||
                   !String.Equals(line.Substring(0,64),
                       NQNativeReproducibilityV23.SHAFile(
                           Path.Combine(root,name)),
                       StringComparison.Ordinal))
                    throw new InvalidDataException(
                        "V23_ARTIFACT_MISSING_OR_MODIFIED "+name);
            }
            if(!files.Contains("campaign.lock")||
               !files.Contains("run_summary.txt")||
               !files.Contains("candidates_full.tsv")||
               !files.Contains("rejected_candidates.tsv"))
                throw new InvalidDataException(
                    "V23_REQUIRED_AUDIT_FILES_ABSENT");
        }
    }
}
