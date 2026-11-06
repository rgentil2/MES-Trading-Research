// V11 - C# pure canonical signature including only EFFECTIVE exit settings.
// The V11 Boolean identity is preserved; V11 exit mode changes its runtime ID.
using System;
using System.Security.Cryptography;
using System.Text;
namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQExitIdentityV11
    {
        public string RuntimeKey { get; internal set; }
        public string Fingerprint { get; internal set; }
        public string BooleanKey { get; internal set; }
        public bool IsRedundant { get; internal set; }
        public int EffectiveLeaves { get; internal set; }
        public int WarmupBars { get; internal set; }
    }
    public static class NQNativeExitCanonicalV11
    {
        public static NQExitIdentityV11 Analyze(int[] genes)
        {
            if (genes == null || genes.Length != 20)
                throw new ArgumentException("Exactly 20 V11 genes required");
            int mode=genes[16];
            if (mode<0 || mode>3 || genes[17]<7 || genes[17]>28 ||
                genes[18]<10 || genes[18]>30 || genes[19]<10 || genes[19]>50)
                throw new ArgumentException("Invalid ATR exit genes");
            if (mode==1 && genes[14]<1)
                throw new ArgumentException("ATR stop/fixed target requires TP>0");
            var v3=NQNativeBooleanCanonicalV11.Analyze(genes[0],
                new[]{genes[1],genes[3],genes[5],genes[7]},
                new[]{genes[2],genes[4],genes[6],genes[8]},
                new[]{genes[9],genes[10],genes[11]},
                genes[12],genes[13],genes[14],genes[15]);
            int warmup=mode==0 ? v3.WarmupBars : Math.Max(v3.WarmupBars,genes[17]+4);
            string exit=mode==0 ? "staticSL="+genes[13]+";staticTP="+genes[14] :
                mode==1 ? "atrSL="+genes[17]+"x"+genes[18]+";staticTP="+genes[14] :
                mode==2 ? "atrSL="+genes[17]+"x"+genes[18]+";atrTPx"+genes[19] :
                          "atrSL="+genes[17]+"x"+genes[18]+";noTP";
            string key="EXCANv11:"+v3.BooleanKey+";warmup="+warmup+
                ";reverse="+genes[12]+";mode="+mode+";"+exit+";daily="+genes[15];
            string hash;
            using(var sha=SHA256.Create())
                hash=BitConverter.ToString(sha.ComputeHash(Encoding.UTF8.GetBytes(key)),0,12).Replace("-","");
            return new NQExitIdentityV11{RuntimeKey=key,BooleanKey=v3.BooleanKey,
                Fingerprint="NQEX11_"+hash,IsRedundant=v3.IsRedundant,
                EffectiveLeaves=v3.EffectiveLeaves,WarmupBars=warmup};
        }
    }
}
