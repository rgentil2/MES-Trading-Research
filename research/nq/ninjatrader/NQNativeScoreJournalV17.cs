// S0.77 V17 — append-only deterministic GA score journal.
// Supports replay/resume by regenerating the SAME seeded evolutionary
// genome sequence and reusing already persisted scores WITHOUT repeating
// expensive historical callback calls. Generation count MAY increase.
// All other GA settings, gene domains, score implementation ID and source
// SHA-256 must match exactly. Not an NT8 GUI optimizer or live trading bot.
// Flushes every N candidates; a crash can lose at most buffered scores.
// A truncated/incomplete journal line FAILS CLOSED; never repairs silently.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;

namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQNativeScoreJournalV17 : IDisposable
    {
        public const string Format="NQ_GENETIC_SCORE_JOURNAL_V17";
        private const char Sep='\t';
        private readonly StreamWriter writer;
        private readonly FileStream stream;
        private readonly Dictionary<string,double> known=
            new Dictionary<string,double>(StringComparer.Ordinal);
        private readonly int flushEvery;
        private readonly Func<int[],NQExitIdentityV11> canonicalizer;
        private bool disposed;
        private int pending;
        public readonly string CampaignHash,SourceSHA256;
        public int Reused {get;private set;}
        public int NewScored {get;private set;}
        public int RecoveredCount {get{return known.Count-NewScored;}}

        private static bool ValidHexSha(string s)
        {
            return !String.IsNullOrEmpty(s)&&s.Length==64&&
                s.All(c=>c>='0'&&c<='9'||c>='a'&&c<='f');
        }

        private static string Sha256(string value)
        {
            using(var hash=SHA256.Create())
                return BitConverter.ToString(hash.ComputeHash(
                    Encoding.UTF8.GetBytes(value)))
                    .Replace("-","").ToLowerInvariant();
        }

        private static string Enc(string s)
        {return Convert.ToBase64String(Encoding.UTF8.GetBytes(s));}
        private static string Dec(string s)
        {return Encoding.UTF8.GetString(Convert.FromBase64String(s));}

        public static string Fingerprint(NQEvolutionConfigV12 cfg,
            NQGeneRangeV11[] ranges,string scorerVersion)
        {
            if(cfg==null||ranges==null||ranges.Length!=20||
               String.IsNullOrWhiteSpace(scorerVersion))
                throw new ArgumentException("Complete journal signature required");
            cfg.Validate();
            // Deliberately omit Generations to allow deterministic extension
            // of a saved 4-generation run to e.g. 190 generations.
            // Freeze every other evolution parameter and gene domain.
            var fields=new[]{
                cfg.Seed,cfg.Population,cfg.Elites,cfg.Tournament,
                cfg.ImmigrantPercent,cfg.MutationPercent,cfg.MaxAttempts,
                cfg.ResetAfterStagnantGenerations
            };
            string spec=Format+"\n"+scorerVersion+"\n"+
                String.Join("/",fields)+"\n"+
                String.Join("|",ranges.Select(r=>
                    r.Min.ToString(CultureInfo.InvariantCulture)+"/"+
                    r.Max.ToString(CultureInfo.InvariantCulture)+"/"+
                    r.Step.ToString(CultureInfo.InvariantCulture)));
            return Sha256(spec);
        }

        public NQNativeScoreJournalV17(string path,string sourceSha,
            string campaignHash,int flushInterval=64,
            Func<int[],NQExitIdentityV11> canonical=null)
        {
            if(String.IsNullOrWhiteSpace(path)||
               !ValidHexSha(sourceSha)||!ValidHexSha(campaignHash)||
               flushInterval<1||flushInterval>10000)
                throw new ArgumentException("File path, source SHA, campaign hash and flush interval required");
            canonicalizer=canonical??NQNativeExitCanonicalV11.Analyze;
            SourceSHA256=sourceSha;
            CampaignHash=campaignHash;
            string header=Format+Sep+sourceSha+Sep+campaignHash;
            if(File.Exists(path))
            {
                foreach(string line in File.ReadAllLines(path,Encoding.UTF8)
                    .Select((l,i)=>l+"\u0000"+i))
                {
                    int n=line.LastIndexOf('\u0000');
                    string content=line.Substring(0,n);
                    int index=Int32.Parse(line.Substring(n+1),
                        CultureInfo.InvariantCulture);
                    if(index==0)
                    {
                        if(content!=header)
                            throw new InvalidOperationException(
                                "JOURNAL_SOURCE_OR_GENETIC_SETTINGS_MISMATCH");
                        continue;
                    }
                    string[] f=content.Split(Sep);
                    if(f.Length!=4)
                        throw new InvalidDataException(
                            "Corrupted/truncated GA score row "+index);
                    string key,genes;
                    try{key=Dec(f[0]);genes=Dec(f[1]);}
                    catch(FormatException ex)
                    {throw new InvalidDataException("Invalid base64 journal row",ex);}
                    if(Sha256(key+"\n"+genes+"\n"+f[2])!=f[3])
                        throw new InvalidDataException("Invalid row checksum "+index);
                    double score;
                    if(!Double.TryParse(f[2],NumberStyles.Float,
                        CultureInfo.InvariantCulture,out score)||
                        Double.IsNaN(score)||Double.IsInfinity(score))
                        throw new InvalidDataException("Nonfinite persisted score");
                    int[] g;
                    try{g=genes.Split('/').Select(x=>Int32.Parse(x,
                        CultureInfo.InvariantCulture)).ToArray();}
                    catch(FormatException ex)
                    {throw new InvalidDataException("Invalid genes",ex);}
                    if(g.Length!=20 ||
                       canonicalizer(g).RuntimeKey!=key ||
                       !known.TryAdd(key,score))
                        throw new InvalidDataException(
                            "Duplicate or noncanonical journal genome");
                }
            }
            else
                File.WriteAllText(path,header+"\n",new UTF8Encoding(false));
            stream=new FileStream(path,FileMode.Append,FileAccess.Write,
                FileShare.None,65536);
            writer=new StreamWriter(stream,new UTF8Encoding(false),65536,true);
            flushEvery=flushInterval;
        }

        public double Score(NQGenomeV11 genome,
            Func<NQGenomeV11,double> underlyingFitness)
        {
            if(disposed)throw new ObjectDisposedException("journal");
            if(genome==null||underlyingFitness==null)
                throw new ArgumentNullException("genome or fitness");
            string key=genome.Canonical.RuntimeKey;
            double v;
            if(known.TryGetValue(key,out v))
            {Reused++;return v;}
            v=underlyingFitness(genome);
            if(Double.IsNaN(v)||Double.IsInfinity(v))
                v=-1.0e12;
            string genes=String.Join("/",genome.Genes.Select(x=>
                x.ToString(CultureInfo.InvariantCulture)));
            string raw=v.ToString("R",CultureInfo.InvariantCulture);
            writer.Write(Enc(key));writer.Write(Sep);
            writer.Write(Enc(genes));writer.Write(Sep);
            writer.Write(raw);writer.Write(Sep);
            writer.WriteLine(Sha256(key+"\n"+genes+"\n"+raw));
            known.Add(key,v);
            NewScored++;
            if(++pending>=flushEvery)Flush();
            return v;
        }

        public void Flush()
        {
            if(disposed)throw new ObjectDisposedException("journal");
            writer.Flush();
            stream.Flush(true);
            pending=0;
        }

        public void Dispose()
        {
            if(disposed)return;
            Flush();
            writer.Dispose();
            stream.Dispose();
            disposed=true;
        }

        public static NQEvolutionSummaryV12 RunWithHistoricalJournal(
            NQNativeSignalCacheV14 cache,int[] baseline,
            NQEvolutionConfigV12 cfg,string journalPath,
            string developmentSha256)
        {
            if(cache==null||baseline==null||baseline.Length!=20)
                throw new ArgumentException("V14 cache and 20 baseline genes");
            var ranges=NQEvolutionEngineV12.DefaultDomains(baseline,true);
            string tag="V11_V12_V14_V9_M1_2020_22_COSTS_FROZEN_V1";
            string sig=Fingerprint(cfg,ranges,tag);
            using(var journal=new NQNativeScoreJournalV17(journalPath,
                developmentSha256,sig))
            {
                var engine=new NQEvolutionEngineV12(ranges,cfg);
                return engine.Run(g=>journal.Score(g,
                    candidate=>cache.Evaluate(candidate.Genes).Score));
            }
        }
    }
}
