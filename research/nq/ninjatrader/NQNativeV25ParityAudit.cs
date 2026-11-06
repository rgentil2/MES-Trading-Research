// S0.86 V25 — independent audit of NinjaTrader historical
// strategy fills vs the existing V12 conservative research estimates.
// This is a DIAGNOSTIC COMPARISON, never a claim that the proprietary
// NinjaTrader fill engine is equivalent by construction.
// No reoptimizing frozen genes or peeking at external holdouts here.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
namespace NinjaTrader.NinjaScript.Strategies
{
    public sealed class NQNativeV25NativeTrade
    {
        public DateTime EntryTimeET,ExitTimeET;
        public int Side,Quantity;
        public double EntryPrice,ExitPrice;
        public double NativeProfitCurrency,NetUnderResearchFee;
    }
    public sealed class NQNativeV25TradeDifference
    {
        public int TradeNumber,EntryMinuteDelta,ExitMinuteDelta;
        public double EntryTicksDelta,ExitTicksDelta,NetUSDDelta;
        public bool SideMatch,QuantityMatch,Passed;
        public string Reason;
    }
    public sealed class NQNativeV25ParityResult
    {
        public bool Complete,ProvisionalPass;
        public string Status;
        public int ExpectedCount,NativeCount,Matched;
        public double ResearchNetUSD,NativeModelNetUSD;
        public double ResearchClosedDDUSD,NativeModelClosedDDUSD;
        public double MaximumEntryTickDelta,MaximumExitTickDelta;
        public double MaximumNetUSDDelta;
        public readonly List<NQNativeV25TradeDifference> Trades=
            new List<NQNativeV25TradeDifference>();
    }
    public sealed class NQNativeV25ParityTolerance
    {
        public int MaxTimeDifferenceMinutes=1;
        public double MaxEntryTickDifference=2.0;
        public double MaxExitTickDifference=2.0;
        public double MaxNetUSDPerTradeDifference=20.0;
        public double MaxTotalNetDifferenceUSD=200.0;
        public double MaxClosedDDDifferenceUSD=200.0;
        public void Validate()
        {
            if(MaxTimeDifferenceMinutes<0||
               MaxTimeDifferenceMinutes>2||
               MaxEntryTickDifference<0||
               MaxEntryTickDifference>4||
               MaxExitTickDifference<0||
               MaxExitTickDifference>4||
               MaxNetUSDPerTradeDifference<0||
               MaxNetUSDPerTradeDifference>100||
               MaxTotalNetDifferenceUSD<0||
               MaxTotalNetDifferenceUSD>2000||
               MaxClosedDDDifferenceUSD<0||
               MaxClosedDDDifferenceUSD>2000)
                throw new ArgumentException("INVALID_V25_PARITY_TOLERANCE");
        }
    }
    public static class NQNativeV25ParityAudit
    {
        static readonly CultureInfo I=CultureInfo.InvariantCulture;
        static string Number(double v)
        {return v.ToString("R",I);}
        static double DD(IList<double> net)
        {
            double equity=0,peak=0,dd=0;
            foreach(double x in net)
            {
                equity+=x;
                peak=Math.Max(peak,equity);
                dd=Math.Max(dd,peak-equity);
            }
            return dd;
        }
        static bool Finite(double x)
        {return !Double.IsNaN(x)&&!Double.IsInfinity(x);}
        public static IList<NQNativeV25NativeTrade> LoadNativeTsv(
            string path,string canonical,string freezeHash)
        {
            if(String.IsNullOrWhiteSpace(canonical)||
               String.IsNullOrWhiteSpace(freezeHash)||freezeHash.Length!=64)
                throw new ArgumentException("V25_FREEZE_IDENTITY_REQUIRED");
            var lines=File.ReadAllLines(path);
            if(lines.Length<2||lines[0]!=
               "V25LockSHA256\t"+freezeHash)
                throw new InvalidDataException("V25_NATIVE_LOCK_MISMATCH");
            if(lines[1]!="canonicalBase64\tentryET\texitET\tside"+
                "\tcontracts\tentryPrice\texitPrice"+
                "\tnativeProfitCurrency\tnetUsingV12Fee")
                throw new InvalidDataException("V25_NATIVE_TRADE_COLUMNS_MISMATCH");
            var outList=new List<NQNativeV25NativeTrade>();
            foreach(string line in lines.Skip(2))
            {
                var c=line.Split('\t');
                if(c.Length!=9)
                    throw new InvalidDataException("V25_BAD_NATIVE_TRADE_COLUMNS");
                string key;
                try{key=Encoding.UTF8.GetString(Convert.FromBase64String(c[0]));}
                catch(FormatException ex)
                {throw new InvalidDataException("V25_BAD_NATIVE_CANONICAL",ex);}
                if(key!=canonical)
                    throw new InvalidDataException("V25_NATIVE_CANONICAL_MISMATCH");
                int side,qty;double ep,xp,pnl,net;
                if(!Int32.TryParse(c[3],NumberStyles.Integer,I,out side)||
                   Math.Abs(side)!=1||
                   !Int32.TryParse(c[4],NumberStyles.Integer,I,out qty)||
                   qty!=1||
                   !Double.TryParse(c[5],NumberStyles.Float,I,out ep)||
                   !Double.TryParse(c[6],NumberStyles.Float,I,out xp)||
                   !Double.TryParse(c[7],NumberStyles.Float,I,out pnl)||
                   !Double.TryParse(c[8],NumberStyles.Float,I,out net)||
                   !Finite(ep)||!Finite(xp)||!Finite(pnl)||!Finite(net))
                    throw new InvalidDataException("V25_INVALID_NATIVE_TRADE_VALUES");
                DateTime entry,exit;
                if(!DateTime.TryParseExact(c[1],"yyyy-MM-ddTHH:mm:ss",
                    I,DateTimeStyles.None,out entry)||
                   !DateTime.TryParseExact(c[2],"yyyy-MM-ddTHH:mm:ss",
                    I,DateTimeStyles.None,out exit)||
                   exit<entry)
                    throw new InvalidDataException("V25_NATIVE_TRADE_TIMES_INVALID");
                double recomputed=(xp-ep)*side*20.0-
                    NQNativeV25FrozenSignalCore.ResearchFeeRoundTripUSD;
                if(Math.Abs(net-recomputed)>0.03)
                    throw new InvalidDataException(
                        "V25_NATIVE_NET_PRICE_FEE_RECONCILIATION_FAILED");
                if(outList.Count>0&&entry<outList[outList.Count-1].EntryTimeET)
                    throw new InvalidDataException("V25_NATIVE_TRADES_OUT_OF_ORDER");
                outList.Add(new NQNativeV25NativeTrade{
                    EntryTimeET=entry,ExitTimeET=exit,
                    Side=side,Quantity=qty,EntryPrice=ep,ExitPrice=xp,
                    NativeProfitCurrency=pnl,NetUnderResearchFee=net
                });
            }
            return outList;
        }

        public static NQNativeV25ParityResult Compare(
            NQHistoricalResultV12 expected,
            IList<NQNativeV25NativeTrade> native,
            NQNativeV25ParityTolerance tolerances)
        {
            if(expected==null||native==null||tolerances==null)
                throw new ArgumentNullException("V25_PARITY_REQUIRED_INPUT");
            tolerances.Validate();
            var result=new NQNativeV25ParityResult{
                ExpectedCount=expected.Executed.Count,NativeCount=native.Count,
                ResearchNetUSD=expected.Net,
                Status="V25_NOT_EVALUATED",
                Complete=false,ProvisionalPass=false
            };
            if(!expected.Valid||
               expected.Executed.Count!=expected.Trades.Count)
            {result.Status="V25_REFERENCE_M1_ECONOMIC_INVALID";return result;}
            result.NativeModelNetUSD=native.Sum(x=>x.NetUnderResearchFee);
            result.ResearchClosedDDUSD=DD(expected.Trades
                .Select(x=>x.NetProfitUSD).ToArray());
            result.NativeModelClosedDDUSD=DD(native
                .Select(x=>x.NetUnderResearchFee).ToArray());
            int common=Math.Min(expected.Executed.Count,native.Count);
            bool all=true;
            for(int i=0;i<common;i++)
            {
                var a=expected.Executed[i];var b=native[i];
                int tm1=(int)Math.Round(
                    Math.Abs((a.EntryTime-b.EntryTimeET).TotalMinutes));
                int tm2=(int)Math.Round(
                    Math.Abs((a.ExitTime-b.ExitTimeET).TotalMinutes));
                double ep=Math.Abs(a.EntryPrice-b.EntryPrice)/0.25;
                double xp=Math.Abs(a.ExitPrice-b.ExitPrice)/0.25;
                double net=Math.Abs(expected.Trades[i].NetProfitUSD-
                    b.NetUnderResearchFee);
                bool side=a.Side==b.Side,qty=a.Quantity==b.Quantity;
                bool passed=side&&qty&&
                    tm1<=tolerances.MaxTimeDifferenceMinutes&&
                    tm2<=tolerances.MaxTimeDifferenceMinutes&&
                    ep<=tolerances.MaxEntryTickDifference+1e-9&&
                    xp<=tolerances.MaxExitTickDifference+1e-9&&
                    net<=tolerances.MaxNetUSDPerTradeDifference+0.01;
                var diff=new NQNativeV25TradeDifference{
                    TradeNumber=i+1,EntryMinuteDelta=tm1,ExitMinuteDelta=tm2,
                    EntryTicksDelta=ep,ExitTicksDelta=xp,
                    NetUSDDelta=net,SideMatch=side,QuantityMatch=qty,
                    Passed=passed,Reason=passed?"WITHIN_TOLERANCE":
                       "SIDE_QUANTITY_TIME_PRICE_OR_NET_MISMATCH"
                };
                result.Trades.Add(diff);
                result.MaximumEntryTickDelta=Math.Max(
                    result.MaximumEntryTickDelta,ep);
                result.MaximumExitTickDelta=Math.Max(
                    result.MaximumExitTickDelta,xp);
                result.MaximumNetUSDDelta=Math.Max(
                    result.MaximumNetUSDDelta,net);
                if(passed)result.Matched++;else all=false;
            }
            result.Complete=true;
            result.ProvisionalPass=all &&
                result.ExpectedCount==result.NativeCount&&
                Math.Abs(result.ResearchNetUSD-
                    result.NativeModelNetUSD)<=
                    tolerances.MaxTotalNetDifferenceUSD&&
                Math.Abs(result.ResearchClosedDDUSD-
                    result.NativeModelClosedDDUSD)<=
                    tolerances.MaxClosedDDDifferenceUSD;
            result.Status=result.ProvisionalPass?
                "NATIVE_V12_TOLERANCE_PROVISIONALLY_PASSED":
                result.ExpectedCount!=result.NativeCount?
                    "TRADE_COUNT_MISMATCH":
                    "TRADE_OR_ACCOUNT_ECONOMIC_MISMATCH";
            return result;
        }

        public static void WriteReport(string path,
            NQNativeV25ParityResult r,string candidateId)
        {
            using(var w=new StreamWriter(path,false,new UTF8Encoding(false)))
            {
                w.WriteLine("candidateId\tstatus\tmatched\treferenceCount"+
                    "\tnativeCount\trefNetUSD\tnativeModelNetUSD"+
                    "\trefDDUSD\tnativeDDUSD\tmaxEntryTickDelta"+
                    "\tmaxExitTickDelta\tmaxTradeNetDeltaUSD");
                w.WriteLine(String.Join("\t",new[]{
                    candidateId,r.Status,r.Matched.ToString(I),
                    r.ExpectedCount.ToString(I),r.NativeCount.ToString(I),
                    Number(r.ResearchNetUSD),Number(r.NativeModelNetUSD),
                    Number(r.ResearchClosedDDUSD),Number(r.NativeModelClosedDDUSD),
                    Number(r.MaximumEntryTickDelta),
                    Number(r.MaximumExitTickDelta),
                    Number(r.MaximumNetUSDDelta)
                }));
                w.WriteLine("trade\tentryMinuteDelta\texitMinuteDelta"+
                    "\tentryTickDelta\texitTickDelta\ttradeNetDeltaUSD"+
                    "\tsideMatch\tquantityMatch\tstatus");
                foreach(var trade in r.Trades)
                    w.WriteLine(String.Join("\t",new[]{
                        trade.TradeNumber.ToString(I),
                        trade.EntryMinuteDelta.ToString(I),
                        trade.ExitMinuteDelta.ToString(I),
                        Number(trade.EntryTicksDelta),
                        Number(trade.ExitTicksDelta),
                        Number(trade.NetUSDDelta),
                        trade.SideMatch?"1":"0",
                        trade.QuantityMatch?"1":"0",
                        trade.Reason
                    }));
            }
        }
    }
}
