// S0.84 V23 — immutable scope: ONE configurable offline research
// generator + complete results / rejection reports / reproducibility.
// V24 is performance scaling, V25 a SINGLE final NinjaTrader bridge.
// This source never instantiates a native NinjaTrader Strategy.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQGeneratorSettingsV23
    {
        public string InputPath="";
        public string OutputDirectory="";
        public string Instrument="NQ DEC2026";
        public string ContractPolicy="USER_CONFIRMED_VISIBLE_SERIES_NOT_AUDITED";
        public string SourceRevision="S0.84_V23_INTEGRATED_RESEARCH";
        public int MinimumFullSessionsPerMonth=15;
        public int[] BaselineGenes={
            2,396,12,789,12,999,12,1319,12,
            0,0,0,0,20,32,2,0,14,15,25
        };
        public int RankingCount=20;
        public int FeatureCacheBytes=64*1024*1024;
        public NQResearchConfigV16 Research=new NQResearchConfigV16();
        public NQPortfolioAuditConfigV22 Audit=
            new NQPortfolioAuditConfigV22();

        public void Validate()
        {
            if(String.IsNullOrWhiteSpace(OutputDirectory)||
               String.IsNullOrWhiteSpace(Instrument)||
               !Instrument.StartsWith("NQ",StringComparison.OrdinalIgnoreCase)||
               String.IsNullOrWhiteSpace(ContractPolicy)||
               String.IsNullOrWhiteSpace(SourceRevision)||
               MinimumFullSessionsPerMonth<1||
               MinimumFullSessionsPerMonth>23||
               BaselineGenes==null||BaselineGenes.Length!=20||
               RankingCount<1||RankingCount>1000||
               FeatureCacheBytes<1024*1024||
               Research==null||Audit==null)
                throw new ArgumentException("INVALID_V23_RESEARCH_CONFIG");
            Research.Validate();Audit.Validate();
            if(Research.MinimumFullDaysPerMonth!=
               MinimumFullSessionsPerMonth ||
               Research.WalkForward.MinimumFullSessionsPerMonth!=
               MinimumFullSessionsPerMonth)
                throw new ArgumentException(
                    "V23_COVERAGE_POLICY_MUST_MATCH_LOADER_RUNNER_WALKFORWARD");
            var identity=NQNativeExitCanonicalV19.Analyze(BaselineGenes);
            if(identity.IsRedundant)
                throw new ArgumentException("V23_BASELINE_IS_STRUCTURALLY_REDUNDANT");
            // All knobs are explicit. Do not allow the operator to
            // configure a two-strategy portfolio or relax the mandatory
            // original research gates silently.
            if(Research.Portfolio.TargetStrategies<3||
               Research.Portfolio.TargetStrategies>5||
               Research.Robustness.CostMultiplier<1.5||
               Research.AccountRisk.MaxAccountStressDDUSD>2000||
               Research.AccountRisk.MaxSessionPeakToTroughUSD>1000||
               Research.AccountRisk.MaxConcurrentAdverseUSD>1000||
               Research.Portfolio.MaximumPositiveMonthlyCorrelation>0.45||
               Research.Portfolio.MaximumProfitConcentration>0.40||
               Research.Portfolio.MaximumClosedPortfolioDDUSD>2000||
               Research.Portfolio.MaximumOverlappingMaeProxyUSD>1000)
                throw new ArgumentException(
                    "V23_CANNOT_WEAKEN_DEFINED_G0_MFFU_PROXY_LIMITS");
        }
    }

    public static class NQNativeReproducibilityV23
    {
        public const string Version="S0.84_V23_COMPLETE_GENERATOR_FIXED";
        static readonly CultureInfo I=CultureInfo.InvariantCulture;
        static string SHA(byte[] bytes)
        {
            using(var s=SHA256.Create())
                return BitConverter.ToString(s.ComputeHash(bytes))
                    .Replace("-","").ToLowerInvariant();
        }
        public static string SHA(string data)
        {return SHA(Encoding.UTF8.GetBytes(data));}
        public static string SHAFile(string path)
        {
            using(var stream=System.IO.File.OpenRead(path))
            using(var s=SHA256.Create())
                return BitConverter.ToString(s.ComputeHash(stream))
                    .Replace("-","").ToLowerInvariant();
        }
        static void Add(List<string> target,string path,object obj,int depth)
        {
            if(depth>12)throw new InvalidOperationException(
                "V23_CONFIG_OBJECT_DEPTH_EXCEEDED");
            if(obj==null)
            {target.Add(path+"=null");return;}
            if(obj is string)
            {
                var value=(string)obj;
                target.Add(path+"="+Convert.ToBase64String(
                    Encoding.UTF8.GetBytes(value)));
                return;
            }
            if(obj is DateTime)
            {
                target.Add(path+"="+((DateTime)obj).ToString(
                    "O",I));return;
            }
            if(obj is Array)
            {
                var values=(Array)obj;
                target.Add(path+".Length="+values.Length.ToString(I));
                int index=0;
                foreach(object x in values)
                    Add(target,path+"["+(index++).ToString(I)+"]",
                        x,depth+1);
                return;
            }
            Type t=obj.GetType();
            if(t.IsPrimitive||t.IsEnum||obj is decimal)
            {
                target.Add(path+"="+Convert.ToString(obj,I));
                return;
            }
            var fields=t.GetFields(BindingFlags.Instance|BindingFlags.Public)
                .OrderBy(x=>x.Name,StringComparer.Ordinal).ToArray();
            if(fields.Length==0)
                throw new InvalidOperationException(
                    "V23_UNSERIALIZABLE_CONFIG_FIELD "+path);
            foreach(var field in fields)
                Add(target,path+"."+field.Name,field.GetValue(obj),
                    depth+1);
        }
        public static IList<string> CanonicalSettings(
            NQGeneratorSettingsV23 settings)
        {
            if(settings==null)
                throw new ArgumentNullException("settings");
            var result=new List<string>();
            Add(result,"V23",settings,0);
            return result.AsReadOnly();
        }
        public static string ConfigurationHash(
            NQGeneratorSettingsV23 settings)
        {
            // Output path and input file path are intentionally
            // NOT removed: a resumed campaign must be identical
            // to the operator-supplied configuration as a whole.
            return SHA(Version+"\n"+
                String.Join("\n",CanonicalSettings(settings)));
        }
        public static string SourceBarsHash(
            NQDataLoadV16 source)
        {
            if(source==null||source.Manifest==null||
               source.Bars==null||source.Bars.Count==0)
                throw new ArgumentException("INVALID_V23_DEVELOPMENT_SOURCE");
            var builder=new StringBuilder();
            builder.Append(source.Manifest.Sha256).Append('\n')
                .Append(source.Manifest.Instrument).Append('\n')
                .Append(source.Manifest.ContractPolicy).Append('\n')
                .Append(source.Bars.Count.ToString(I)).Append('\n');
            foreach(var item in source.Bars)
            {
                if(item==null)throw new ArgumentException("NULL_M1_BAR");
                var b=item.Bar;
                builder.Append(item.Time.ToString("O",I)).Append('|')
                  .Append(b.Open.ToString("R",I)).Append('|')
                  .Append(b.High.ToString("R",I)).Append('|')
                  .Append(b.Low.ToString("R",I)).Append('|')
                  .Append(b.Close.ToString("R",I)).Append('|')
                  .Append(b.Volume.ToString("R",I)).Append('\n');
            }
            return SHA(builder.ToString());
        }
        public static string LockText(
            NQGeneratorSettingsV23 config,NQDataLoadV16 source)
        {
            return "version="+Version+"\n"+
                "configSHA256="+ConfigurationHash(config)+"\n"+
                "rawSourceSHA256="+source.Manifest.Sha256+"\n"+
                "barSeriesSHA256="+SourceBarsHash(source)+"\n"+
                "sourcePartition="+source.Manifest.Partition+"\n"+
                "features=120\nconditions=1320\n"+
                "finalInstrument=NQ DEC2026\n"+
                "outOfSampleEvaluated=false\n";
        }
    }
}
