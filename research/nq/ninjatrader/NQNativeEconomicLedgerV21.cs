// S0.82 V21 durable FULL ECONOMIC SUMMARY journal, not just fitness.
// Each uniquely scored EXCANv19 genome records V12 simulated closed
// trades, net USD, realized DD, PF, SL/TP/time exits and ambiguous bars.
// Append-only per-row SHA256, strict source/genetic/scorer campaign lock,
// deterministic GA replay with 0 repeated backtest callbacks on resume.
// Rank/trade ledger export replays only top-N winners, not all 100k.
// RESEARCH ONLY; no actual NT8 historical fills / production execution.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQEconomicRowV21
    {
        public string Canonical;
        public int[] Genes;
        public double Score,Net,ProfitFactor,ClosedDrawdown;
        public int Trades,StopFills,TargetFills,TimeFills,AmbiguousStops;
        public static NQEconomicRowV21 From(
            NQGenomeV11 genome,NQHistoricalResultV12 result)
        {
            if(genome==null||result==null)
                throw new ArgumentNullException("V21 economic row input");
            double profit=0,loss=0,equity=0,peak=0,dd=0;
            foreach(var x in result.Trades)
            {
                if(x.NetProfitUSD>0)profit+=x.NetProfitUSD;
                else loss-=x.NetProfitUSD;
                equity+=x.NetProfitUSD;
                peak=Math.Max(peak,equity);
                dd=Math.Max(dd,peak-equity);
            }
            if(result.Valid&&
               (Math.Abs(equity-result.Net)>0.03||
                result.Trades.Count!=result.Executed.Count))
                throw new InvalidOperationException("INVALID_V12_TRADE_RECONCILIATION");
            double score=result.Score;
            if(Double.IsNaN(score)||Double.IsInfinity(score))
                score=-1.0e12;
            return new NQEconomicRowV21{
                Canonical=genome.Canonical.RuntimeKey,
                Genes=(int[])genome.Genes.Clone(),
                Score=score,Net=result.Net,
                ProfitFactor=loss>0?profit/loss:profit>0?100:0,
                ClosedDrawdown=dd,Trades=result.Trades.Count,
                StopFills=result.StopFills,
                TargetFills=result.TargetFills,
                TimeFills=result.TimeFills,
                AmbiguousStops=result.AmbiguousStops
            };
        }
    }
    public sealed class NQNativeEconomicLedgerV21 : IDisposable
    {
        public const string Format="NQ_V21_COMPLETE_ECONOMIC_LEDGER_1";
        public readonly string DevelopmentSHA256,ConfigSHA256;
        private readonly Dictionary<string,NQEconomicRowV21> known=
            new Dictionary<string,NQEconomicRowV21>(StringComparer.Ordinal);
        private readonly StreamWriter output;
        private readonly FileStream file;
        private readonly int flushEvery;
        private int pending;
        private bool disposed;
        public int Reused{get;private set;}
        public int Fresh{get;private set;}
        public int Count{get{return known.Count;}}
        public IList<NQEconomicRowV21> Ranked
        {
            get
            {
                return known.Values.OrderByDescending(x=>x.Score)
                    .ThenBy(x=>x.Canonical,StringComparer.Ordinal)
                    .ToArray();
            }
        }
        static string SHA(string text)
        {
            using(var s=SHA256.Create())
                return BitConverter.ToString(s.ComputeHash(
                    Encoding.UTF8.GetBytes(text))).Replace("-","")
                    .ToLowerInvariant();
        }
        static string Enc(string value)
        {return Convert.ToBase64String(Encoding.UTF8.GetBytes(value));}
        static string Dec(string value)
        {return Encoding.UTF8.GetString(Convert.FromBase64String(value));}
        static string Num(double x)
        {return x.ToString("R",CultureInfo.InvariantCulture);}
        static double ParseDouble(string s)
        {
            double x;
            if(!Double.TryParse(s,NumberStyles.Float,
                CultureInfo.InvariantCulture,out x)||
               Double.IsNaN(x)||Double.IsInfinity(x))
                throw new InvalidDataException("INVALID_OR_NONFINITE_NUMERIC_ROW");
            return x;
        }
        static int ParseInt(string s)
        {
            int x;
            if(!Int32.TryParse(s,NumberStyles.Integer,
                CultureInfo.InvariantCulture,out x)||x<0)
                throw new InvalidDataException("INVALID_INTEGER_FIELD");
            return x;
        }
        static string Genes(int[] genes)
        {return String.Join("/",genes.Select(x=>
            x.ToString(CultureInfo.InvariantCulture)));}
        static int[] ParseGenes(string s)
        {
            var values=s.Split('/');
            if(values.Length!=20)
                throw new InvalidDataException("WRONG_GENOME_LENGTH");
            try{return values.Select(x=>Int32.Parse(x,
                    CultureInfo.InvariantCulture)).ToArray();}
            catch(FormatException ex)
            {throw new InvalidDataException("BAD_GENOME_INTEGER",ex);}
        }
        static string Fields(NQEconomicRowV21 row)
        {
            return String.Join("\t",new[]{
                Enc(row.Canonical),Enc(Genes(row.Genes)),
                Num(row.Score),Num(row.Net),Num(row.ProfitFactor),
                Num(row.ClosedDrawdown),
                row.Trades.ToString(CultureInfo.InvariantCulture),
                row.StopFills.ToString(CultureInfo.InvariantCulture),
                row.TargetFills.ToString(CultureInfo.InvariantCulture),
                row.TimeFills.ToString(CultureInfo.InvariantCulture),
                row.AmbiguousStops.ToString(CultureInfo.InvariantCulture)
            });
        }

        public static string Fingerprint(NQEvolutionConfigV12 cfg,
            int[] baseline,bool exploreExits)
        {
            var ranges=NQNativeExitCanonicalV19.DefaultDomains(
                baseline,exploreExits);
            return NQNativeScoreJournalV17.Fingerprint(cfg,ranges,
                "V21_V19_1320_RULES_V12_M1_COSTS_V9_FITNESS"+
                "_COMPLETE_ECON_LEDGER_1");
        }

        public NQNativeEconomicLedgerV21(
            string path,string developmentSha256,string cfgHash,
            int flushInterval=32)
        {
            if(String.IsNullOrWhiteSpace(path)||
               developmentSha256==null||developmentSha256.Length!=64||
               cfgHash==null||cfgHash.Length!=64||
               flushInterval<1||flushInterval>10000)
                throw new ArgumentException("Source SHA, settings and output path required");
            DevelopmentSHA256=developmentSha256;
            ConfigSHA256=cfgHash;
            string header=Format+"\t"+developmentSha256+"\t"+cfgHash;
            if(File.Exists(path))
            {
                int lineNo=0;
                foreach(var line in File.ReadLines(path,Encoding.UTF8))
                {
                    lineNo++;
                    if(lineNo==1)
                    {
                        if(line!=header)
                            throw new InvalidOperationException(
                                "ECONOMIC_LEDGER_SOURCE_OR_SCORER_MISMATCH");
                        continue;
                    }
                    int lastTab=line.LastIndexOf('\t');
                    if(lastTab<0 ||
                       SHA(line.Substring(0,lastTab))!=
                         line.Substring(lastTab+1))
                        throw new InvalidDataException(
                            "ECONOMIC_LEDGER_ROW_CHECKSUM_INVALID at "+lineNo);
                    var columns=line.Substring(0,lastTab).Split('\t');
                    if(columns.Length!=11)
                        throw new InvalidDataException("INVALID_LEDGER_COLUMNS");
                    string key,genes;
                    try{key=Dec(columns[0]);genes=Dec(columns[1]);}
                    catch(FormatException ex)
                    {throw new InvalidDataException("INVALID_BASE64_LEDGER_ROW",ex);}
                    var g=ParseGenes(genes);
                    NQExitIdentityV11 identity;
                    try{identity=NQNativeExitCanonicalV19.Analyze(g);}
                    catch(ArgumentException ex)
                    {throw new InvalidDataException("INVALID_CANONICAL_GENOME",ex);}
                    if(identity.IsRedundant||identity.RuntimeKey!=key)
                        throw new InvalidDataException("INVALID_V19_CANONICAL_ID");
                    var row=new NQEconomicRowV21{
                        Canonical=key,Genes=g,Score=ParseDouble(columns[2]),
                        Net=ParseDouble(columns[3]),
                        ProfitFactor=ParseDouble(columns[4]),
                        ClosedDrawdown=ParseDouble(columns[5]),
                        Trades=ParseInt(columns[6]),
                        StopFills=ParseInt(columns[7]),
                        TargetFills=ParseInt(columns[8]),
                        TimeFills=ParseInt(columns[9]),
                        AmbiguousStops=ParseInt(columns[10])
                    };
                    if(!known.TryAdd(key,row))
                        throw new InvalidDataException("DUPLICATE_LEDGER_GENOME");
                }
                if(lineNo==0)
                    throw new InvalidDataException("MISSING_LEDGER_HEADER");
            }
            else File.WriteAllText(path,header+"\n",
                    new UTF8Encoding(false));
            file=new FileStream(path,FileMode.Append,FileAccess.Write,
                FileShare.None,65536);
            output=new StreamWriter(file,new UTF8Encoding(false),65536,true);
            flushEvery=flushInterval;
        }
        public double Score(NQGenomeV11 genome,
            Func<int[],NQHistoricalResultV12> evaluator)
        {
            if(disposed)throw new ObjectDisposedException("economic ledger");
            if(genome==null||evaluator==null)
                throw new ArgumentNullException("V21 score inputs");
            NQEconomicRowV21 row;
            if(known.TryGetValue(genome.Canonical.RuntimeKey,out row))
            {
                if(Genes(row.Genes)!=Genes(genome.Genes))
                    throw new InvalidDataException(
                        "SAME_CANONICAL_KEY_DIFFERENT_GENOME");
                Reused++;
                return row.Score;
            }
            row=NQEconomicRowV21.From(genome,evaluator(genome.Genes));
            var line=Fields(row);
            output.Write(line);
            output.Write('\t');
            output.WriteLine(SHA(line));
            known.Add(row.Canonical,row);
            Fresh++;
            if(++pending>=flushEvery)Flush();
            return row.Score;
        }
        public void Flush()
        {
            if(disposed)throw new ObjectDisposedException("ledger");
            output.Flush();file.Flush(true);pending=0;
        }
        public void Dispose()
        {
            if(disposed)return;
            Flush();output.Dispose();file.Dispose();disposed=true;
        }
        public void WriteRanking(string path,int topCount)
        {
            if(topCount<1||topCount>1000000)
                throw new ArgumentOutOfRangeException("topCount");
            using(var stream=new StreamWriter(path,false,
                new UTF8Encoding(false)))
            {
                stream.WriteLine("rank\tcanonicalBase64\tscore\tnetUSD\ttrades"+
                    "\tprofitFactor\tclosedDrawdownUSD\tstopExits"+
                    "\ttargetExits\ttimeExits\tambiguousStopAndTarget");
                int rank=0;
                foreach(var row in Ranked.Take(topCount))
                {
                    stream.WriteLine(String.Join("\t",new[]{
                        (++rank).ToString(CultureInfo.InvariantCulture),
                        Enc(row.Canonical),Num(row.Score),Num(row.Net),
                        row.Trades.ToString(CultureInfo.InvariantCulture),
                        Num(row.ProfitFactor),Num(row.ClosedDrawdown),
                        row.StopFills.ToString(CultureInfo.InvariantCulture),
                        row.TargetFills.ToString(CultureInfo.InvariantCulture),
                        row.TimeFills.ToString(CultureInfo.InvariantCulture),
                        row.AmbiguousStops.ToString(CultureInfo.InvariantCulture)
                    }));
                }
            }
        }
    }
}
