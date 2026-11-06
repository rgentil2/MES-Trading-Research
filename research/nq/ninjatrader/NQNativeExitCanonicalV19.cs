// S0.80 V19 1320-condition canonicalizer with 20 genes. Preserves prior V11/V18 files unchanged.
// V19 structural identity for 396 directional conditions, including
// all 132 unchanged V11 IDs. Does not change ANY V11 canonical format.
// Boolean semantics are the same left-associated AND/OR as V11.
// All active 20-gene exits retained with original economic semantics.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography;
using System.Text;

namespace NinjaTrader.NinjaScript.Strategies
{
    public static class NQNativeExitCanonicalV19
    {
        private static bool BooleanValue(int[] indexes,int[] ops,
            int count,int mask)
        {
            bool value=(mask & (1<<indexes[0]))!=0;
            for(int j=1;j<count;j++)
            {
                bool right=(mask & (1<<indexes[j]))!=0;
                value=ops[j-1]==0?(value&&right):(value||right);
            }
            return value;
        }
        public static NQExitIdentityV11 Analyze(int[] g)
        {
            if(g==null||g.Length!=20||g[0]<1||g[0]>4||
               g[12]<0||g[12]>1||g[13]<1||g[14]<0||
               g[15]<1||g[15]>2||g[16]<0||g[16]>3||
               g[17]<7||g[17]>28||g[18]<10||g[18]>30||
               g[19]<10||g[19]>50||g[16]==1&&g[14]<1)
                throw new ArgumentException("Invalid V19 20-gene exit/condition bounds");

            int count=g[0],warmup=0;
            var keys=new string[count];
            for(int k=0;k<count;k++)
            {
                int type=g[1+2*k],period=g[2+2*k];
                if(type<0||type>=NQNativeConditionCatalogV19.Count||
                   period<NQNativeConditionCatalogV19.MinPeriod||
                   period>NQNativeConditionCatalogV19.MaxPeriod)
                    throw new ArgumentException("Invalid V19 signal type/period");
                keys[k]=type.ToString("D3")+":"+period.ToString("D3");
                warmup=Math.Max(warmup,
                    NQNativeConditionCatalogV19.RequiredBars(period));
                if(k>0&&g[8+k]!=0&&g[8+k]!=1)
                    throw new ArgumentException("Invalid Boolean op");
            }
            var unique=keys.Distinct().OrderBy(x=>x,
                StringComparer.Ordinal).ToArray();
            int[] indexes=keys.Select(x=>Array.IndexOf(unique,x)).ToArray();
            int states=1<<unique.Length;
            var table=new bool[states];
            int[] ops={g[9],g[10],g[11]};
            for(int mask=0;mask<states;mask++)
                table[mask]=BooleanValue(indexes,ops,count,mask);
            var active=new List<int>();
            for(int j=0;j<unique.Length;j++)
            {
                bool essential=false;
                for(int m=0;m<states;m++)
                    if(table[m]!=table[m^(1<<j)])
                    {essential=true;break;}
                if(essential)active.Add(j);
            }
            var truth=new StringBuilder();
            for(int m=0;m<(1<<active.Count);m++)
            {
                int original=0;
                for(int j=0;j<active.Count;j++)
                    if((m&(1<<j))!=0)
                        original|=1<<active[j];
                truth.Append(table[original]?'1':'0');
            }
            string boolean="BCANv19:"+
                String.Join(",",active.Select(j=>unique[j]))+
                ";tt="+truth;
            int runtimeWarmup=g[16]==0?warmup:
                Math.Max(warmup,g[17]+4);
            string exit=g[16]==0?
                "staticSL="+g[13]+";staticTP="+g[14]:
                g[16]==1?
                "atrSL="+g[17]+"x"+g[18]+";staticTP="+g[14]:
                g[16]==2?
                "atrSL="+g[17]+"x"+g[18]+";atrTPx"+g[19]:
                "atrSL="+g[17]+"x"+g[18]+";noTP";
            string key="EXCANv19:"+boolean+";warmup="+runtimeWarmup+
                ";reverse="+g[12]+";mode="+g[16]+";"+exit+
                ";daily="+g[15];
            string hash;
            using(var sha=SHA256.Create())
                hash=BitConverter.ToString(sha.ComputeHash(
                    Encoding.UTF8.GetBytes(key)),0,12).Replace("-","");
            return new NQExitIdentityV11{
                RuntimeKey=key,BooleanKey=boolean,
                Fingerprint="NQEX19_"+hash,
                IsRedundant=active.Count<count,
                EffectiveLeaves=active.Count,WarmupBars=runtimeWarmup
            };
        }
        public static NQGeneRangeV11[] DefaultDomains(
            int[] baseline,bool exploreExits)
        {
            var d=NQEvolutionEngineV12.DefaultDomains(baseline,
                exploreExits);
            foreach(int i in new[]{1,3,5,7})
                d[i]=new NQGeneRangeV11(0,
                    NQNativeConditionCatalogV19.Count-1,1);
            return d;
        }
    }
}
