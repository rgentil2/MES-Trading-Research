// S0.86 V25: fail-closed frozen-candidate handoff from a real
// SHA-verified V23 report package. No substitute genes, no candidate
// generation, no fake portfolio. SHA here checks accidental tampering;
// it is NOT a third-party signature against an adversarial file owner.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQNativeV25FrozenPackage
    {
        public string SourceBarsSHA256,ConfigurationSHA256;
        public string FreezeDigest,V23ArtifactManifestSHA256;
        public string V25LockSHA256,Instrument;
        public readonly List<NQFrozenCandidateV16> Candidates=
            new List<NQFrozenCandidateV16>();
    }
    public static class NQNativeV25FrozenImporter
    {
        static readonly CultureInfo I=CultureInfo.InvariantCulture;
        static Dictionary<string,string> Settings(string path)
        {
            var d=new Dictionary<string,string>(StringComparer.Ordinal);
            foreach(string line in File.ReadAllLines(path))
            {
                int x=line.IndexOf('=');
                if(x<1||!d.TryAdd(line.Substring(0,x),
                    line.Substring(x+1)))
                    throw new InvalidDataException("V25_INVALID_CAMPAIGN_LOCK_FIELD");
            }
            return d;
        }
        static string Required(Dictionary<string,string> d,string key)
        {
            string v;if(!d.TryGetValue(key,out v)||
               String.IsNullOrWhiteSpace(v))
                throw new InvalidDataException("V25_MISSING_"+key);
            return v;
        }
        public static NQNativeV25FrozenPackage Load(string directory)
        {
            if(String.IsNullOrWhiteSpace(directory))
                throw new ArgumentException("V25_V23_PACKAGE_PATH_REQUIRED");
            NQNativeCompleteGeneratorV23.Verify(directory);
            string root=Path.GetFullPath(directory);
            var cfg=Settings(Path.Combine(root,"campaign.lock"));
            if(Required(cfg,"sourcePartition")!="Development2020_2022")
                throw new InvalidDataException(
                    "V25_FREEZE_ONLY_AFTER_2020_2022_DEVELOPMENT");
            string bars=Required(cfg,"barSeriesSHA256"),
                   settings=Required(cfg,"configSHA256");
            if(bars.Length!=64||settings.Length!=64)
                throw new InvalidDataException("V25_INVALID_SHA_LENGTH");
            var summary=Settings(Path.Combine(root,"run_summary.txt"));
            if(Required(summary,"status")!=
                    "FROZEN_DEVELOPMENT_ONLY_READY_FOR_EXTERNAL"||
               Required(summary,"externalOosOpened")!="false"||
               Required(summary,"finalOosOpened")!="false"||
               Required(summary,"sourceBarsSHA256")!=bars||
               Required(summary,"configurationSHA256")!=settings)
                throw new InvalidDataException(
                    "V25_NO_REAL_DEV_APPROVED_AND_SEALED_PORTFOLIO");
            int count;
            if(!Int32.TryParse(Required(summary,"frozenForExternal"),
                NumberStyles.Integer,I,out count)||count<3||count>5)
                throw new InvalidDataException("V25_REQUIRES_3_TO_5_FROZEN");
            var portfolio=File.ReadAllLines(Path.Combine(root,
                "portfolio_decision.tsv"));
            if(portfolio.Length!=2)
                throw new InvalidDataException("V25_INVALID_PORTFOLIO_DECISION");
            var cols=portfolio[1].Split('\t');
            if(cols.Length!=11||cols[0]!=
               "FROZEN_DEVELOPMENT_ONLY_READY_FOR_EXTERNAL"||
               String.IsNullOrWhiteSpace(cols[10]))
                throw new InvalidDataException("V25_NO_AUTHORIZED_FROZEN_DIGEST");
            string digest=cols[10];
            var chosenIds=cols[1].Split(',');
            if(chosenIds.Length!=count||
               chosenIds.Distinct(StringComparer.Ordinal).Count()!=count)
                throw new InvalidDataException("V25_FREEZE_SELECTION_COUNT_MISMATCH");
            var rows=File.ReadAllLines(Path.Combine(root,
                "definitive_parameters.tsv"));
            if(rows.Length!=count*20+1||
               rows[0]!="strategyId\tcanonicalBase64\tgeneIndex\tparameter\tvalue\tdescription")
                throw new InvalidDataException(
                    "V25_FINAL_PARAMETERS_MISSING_OR_INCOMPLETE");
            var buckets=new Dictionary<string,int[]>(StringComparer.Ordinal);
            var ids=new Dictionary<string,string>(StringComparer.Ordinal);
            var touched=new Dictionary<string,HashSet<int>>(StringComparer.Ordinal);
            for(int i=1;i<rows.Length;i++)
            {
                var fields=rows[i].Split('\t');
                if(fields.Length!=6||String.IsNullOrWhiteSpace(fields[0])||
                   !chosenIds.Contains(fields[0],StringComparer.Ordinal))
                    throw new InvalidDataException(
                        "V25_PARAMETER_ROW_UNSELECTED_OR_CORRUPT");
                int index,value;
                if(!Int32.TryParse(fields[2],NumberStyles.Integer,I,
                    out index)||index<0||index>=20||
                   !Int32.TryParse(fields[4],NumberStyles.Integer,I,
                    out value))
                    throw new InvalidDataException("V25_BAD_GENE_INDEX_VALUE");
                int[] genes;HashSet<int> indices;
                if(!buckets.TryGetValue(fields[0],out genes))
                {
                    genes=new int[20];
                    buckets.Add(fields[0],genes);
                    indices=new HashSet<int>();
                    touched.Add(fields[0],indices);
                    ids.Add(fields[0],fields[1]);
                }
                else
                {
                    indices=touched[fields[0]];
                    if(ids[fields[0]]!=fields[1])
                        throw new InvalidDataException(
                            "V25_MUTATED_CANONICAL_CANDIDATE_ID");
                }
                if(!indices.Add(index))
                    throw new InvalidDataException("V25_DUPLICATE_GENE_POSITION");
                genes[index]=value;
            }
            if(buckets.Count!=count)
                throw new InvalidDataException("V25_MISSING_FROZEN_GENOMES");
            var result=new NQNativeV25FrozenPackage{
                SourceBarsSHA256=bars,ConfigurationSHA256=settings,
                FreezeDigest=digest,Instrument=Required(summary,"instrument"),
                V23ArtifactManifestSHA256=
                    NQNativeReproducibilityV23.SHAFile(
                        Path.Combine(root,"artifacts.sha256"))
            };
            var canonicalIds=new HashSet<string>(StringComparer.Ordinal);
            foreach(string candidate in chosenIds)
            {
                if(touched[candidate].Count!=20)
                    throw new InvalidDataException("V25_20_GENES_REQUIRED");
                string key;
                try{key=Encoding.UTF8.GetString(
                        Convert.FromBase64String(ids[candidate]));}
                catch(FormatException ex)
                {throw new InvalidDataException("V25_BAD_CANONICAL_BASE64",ex);}
                var frozen=new NQFrozenCandidateV16(candidate,
                    buckets[candidate],NQNativeExitCanonicalV19.Analyze);
                if(frozen.CanonicalId!=key||
                   !canonicalIds.Add(key))
                    throw new InvalidDataException(
                        "V25_CANONICAL_CHANGED_OR_DUPLICATE");
                result.Candidates.Add(frozen);
            }
            string input=NQNativeV25FrozenSignalCore.Version+"\n"+
                result.V23ArtifactManifestSHA256+"\n"+
                result.ConfigurationSHA256+"\n"+
                result.SourceBarsSHA256+"\n"+
                result.FreezeDigest+"\n"+
                String.Join("\n",result.Candidates.Select(x=>
                    x.Id+"|"+x.CanonicalId+"|"+
                    String.Join("/",x.Genes.Select(v=>v.ToString(I)))));
            result.V25LockSHA256=NQNativeReproducibilityV23.SHA(input);
            return result;
        }
        public static void WriteHandoff(NQNativeV25FrozenPackage pkg,
            string path)
        {
            if(pkg==null||pkg.Candidates.Count<3||
               pkg.Candidates.Count>5)
                throw new ArgumentException("V25_APPROVED_FROZEN_PACKAGE_REQUIRED");
            using(var w=new StreamWriter(path,false,new UTF8Encoding(false)))
            {
                w.WriteLine("V25LockSHA256\t"+pkg.V25LockSHA256);
                w.WriteLine("V23ArtifactsSHA256\t"+
                    pkg.V23ArtifactManifestSHA256);
                w.WriteLine("sourceBarsSHA256\t"+pkg.SourceBarsSHA256);
                w.WriteLine("frozenCampaignDigest\t"+pkg.FreezeDigest);
                w.WriteLine("candidateId\tcanonicalBase64\tgenes20");
                foreach(var x in pkg.Candidates)
                    w.WriteLine(x.Id+"\t"+
                        Convert.ToBase64String(Encoding.UTF8.GetBytes(
                            x.CanonicalId))+"\t"+
                        String.Join("/",x.Genes.Select(v=>v.ToString(I))));
            }
        }
    }
}
