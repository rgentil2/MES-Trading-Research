from __future__ import annotations

from pathlib import Path
from bisect import bisect_right
import math
import numpy as np
import pandas as pd

import external_strategy_replication as ext

COST_POINTS = ext.COST_POINTS
TICK = 0.25
MONTHS = 60.0
YEARS = list(range(2020, 2025))
ENTRY_START = 9*60 + 30
ENTRY_END = 11*60 + 30
NEWS_PATH = Path("data_external/forexfactory/usd_high_medium_2020_2024.csv")


# -----------------------------
# Core data / news
# -----------------------------

def load_news():
    n = pd.read_csv(NEWS_PATH)
    n["event_et"] = pd.to_datetime(n["event_et"], utc=True).dt.tz_convert("America/New_York")
    n["deadline_et"] = n["event_et"] - pd.Timedelta(minutes=5)
    n["blackout_end_et"] = n["event_et"] + pd.Timedelta(minutes=5)
    n = n.sort_values("event_et").drop_duplicates("event_et").reset_index(drop=True)
    by_date={}
    for d,g in n.groupby(n["event_et"].dt.date.astype(str),sort=True):
        by_date[d]=g.reset_index(drop=True)
    deadlines=list(n["deadline_et"])
    return n,by_date,deadlines


def blocked_entry(ts, news_day):
    if news_day is None or news_day.empty:
        return False
    return bool(((news_day["deadline_et"] <= ts) & (ts <= news_day["blackout_end_et"])).any())


def deadlines_for_day(news_day):
    if news_day is None or news_day.empty:
        return set()
    return set(news_day["deadline_et"])


def first_global_deadline_after(deadlines, start, through):
    # Robust direct scan: the list has only ~1.9k unique timestamps, so the
    # explicit comparison is trivial and avoids any timezone/order ambiguity.
    candidates=[d for d in deadlines if start < d <= through]
    return min(candidates) if candidates else None


def add_bar_start(df):
    x=df.copy()
    x["bar_start_et"]=x["timestamp_et"]-pd.Timedelta(minutes=1)
    return x


def full_price_lookup(full):
    z=full.sort_values("bar_start_et").drop_duplicates("bar_start_et",keep="last").reset_index(drop=True)
    ns=z["bar_start_et"].astype("int64").to_numpy()
    opens=z["open"].to_numpy(float)
    return z,ns,opens


def price_at_or_after(ts, lookup):
    z,ns,opens=lookup
    key=pd.Timestamp(ts).value
    i=int(np.searchsorted(ns,key,side="left"))
    if i>=len(z) or int(ns[i]) != int(key):
        return None,None
    return float(opens[i]), z.iloc[i]["bar_start_et"]


def record(round_id,strategy,date,direction,entry,exit_px,reason,entry_ts,exit_ts=None):
    gross=direction*(exit_px-entry)
    net=gross-COST_POINTS
    return dict(round=round_id,strategy=strategy,date=date,year=int(str(date)[:4]),
                direction=direction,entry_time_et=str(entry_ts),exit_time_et=str(exit_ts) if exit_ts is not None else "",
                entry=entry,exit=exit_px,exit_reason=reason,
                gross_points=gross,net_points=net,net_dollars=net*5.0)


def metrics(df):
    if df.empty:
        return {}
    pos=df.loc[df.net_points>0,"net_points"].sum()
    neg=-df.loc[df.net_points<0,"net_points"].sum()
    pf=pos/neg if neg>0 else np.inf
    yearly=df.groupby("year")["net_points"].sum().reindex(YEARS,fill_value=0.0)
    positive=yearly.clip(lower=0)
    share=float(positive.max()/positive.sum()) if positive.sum()>0 else np.nan
    eq=df.sort_values(["date","entry_time_et"]).net_points.cumsum()
    dd=float((eq-eq.cummax()).min())
    return dict(
        trades=len(df),
        trades_per_month=len(df)/MONTHS,
        net_pts_trade=float(df.net_points.mean()),
        pf_net=float(pf),
        win_rate=float((df.net_points>0).mean()),
        total_net=float(df.net_points.sum()),
        max_dd_points=dd,
        positive_years=int((yearly>0).sum()),
        max_positive_year_share=share,
        yearly="; ".join(f"{y}:{yearly.loc[y]:.2f}" for y in YEARS),
    )


def gate(m):
    if not m:
        return False
    return bool(
        m["net_pts_trade"]>0 and
        m["pf_net"]>=1.25 and
        m["trades"]>=300 and
        m["positive_years"]>=4 and
        np.isfinite(m["max_positive_year_share"]) and
        m["max_positive_year_share"]<=0.40
    )


# -----------------------------
# Indicator preparation
# -----------------------------

def enrich_1m(sessions):
    parts=[]
    for d,g in sessions.items():
        q=add_bar_start(g)
        q["_datekey"]=d
        q["_row"]=range(len(q))
        parts.append(q)
    x=pd.concat(parts,ignore_index=True).sort_values("timestamp_et").reset_index(drop=True)

    x["sma10"]=x["close"].rolling(10,min_periods=10).mean()
    x["sma25"]=x["close"].rolling(25,min_periods=25).mean()
    x["ma_cross_up"]=(x["sma10"]>x["sma25"])&(x["sma10"].shift(1)<=x["sma25"].shift(1))
    x["ma_cross_dn"]=(x["sma10"]<x["sma25"])&(x["sma10"].shift(1)>=x["sma25"].shift(1))

    x["sma5"]=x["close"].rolling(5,min_periods=5).mean()
    x["sma30"]=x["close"].rolling(30,min_periods=30).mean()
    sma530_up=(x["sma5"]>x["sma30"])&(x["sma5"].shift(1)<=x["sma30"].shift(1))
    x["sma530_cross_up_2"]=sma530_up.astype(int).rolling(2,min_periods=1).max().astype(bool)

    x["ema20"]=x["close"].ewm(span=20,adjust=False).mean()
    x["ema40"]=x["close"].ewm(span=40,adjust=False).mean()
    rsi14_raw=wilder_rsi(x["close"],14)
    x["rsi14s3"]=rsi14_raw.rolling(3,min_periods=3).mean()
    rsi60_cross=(x["rsi14s3"]>60)&(x["rsi14s3"].shift(1)<=60)
    x["rsi60_cross_10"]=rsi60_cross.astype(int).rolling(10,min_periods=1).max().astype(bool)

    x["donch20_upper_prev"]=x["high"].rolling(20,min_periods=20).max().shift(1)
    x["donch20_lower_prev"]=x["low"].rolling(20,min_periods=20).min().shift(1)
    x["donch20_cross_up"]=(x["close"]>x["donch20_upper_prev"])&(x["close"].shift(1)<=x["donch20_upper_prev"].shift(1))
    x["donch20_cross_dn"]=(x["close"]<x["donch20_lower_prev"])&(x["close"].shift(1)>=x["donch20_lower_prev"].shift(1))

    bb100_mid=x["close"].rolling(100,min_periods=100).mean()
    bb100_sd=x["close"].rolling(100,min_periods=100).std(ddof=0)
    x["bb100_upper15"]=bb100_mid+1.5*bb100_sd

    ema12=x["close"].ewm(span=12,adjust=False).mean()
    ema26=x["close"].ewm(span=26,adjust=False).mean()
    x["macd"]=ema12-ema26
    x["macd_signal"]=x["macd"].ewm(span=9,adjust=False).mean()
    x["macd_diff"]=x["macd"]-x["macd_signal"]
    x["macd_cross_up"]=(x["macd"]>x["macd_signal"])&(x["macd"].shift(1)<=x["macd_signal"].shift(1))
    x["macd_cross_dn"]=(x["macd"]<x["macd_signal"])&(x["macd"].shift(1)>=x["macd_signal"].shift(1))

    mid=x["close"].rolling(14,min_periods=14).mean()
    sd=x["close"].rolling(14,min_periods=14).std(ddof=0)
    x["bb_mid"]=mid; x["bb_upper"]=mid+2*sd; x["bb_lower"]=mid-2*sd
    x["bb_cross_above_lower"]=(x["close"]>x["bb_lower"])&(x["close"].shift(1)<=x["bb_lower"].shift(1))
    x["bb_cross_below_upper"]=(x["close"]<x["bb_upper"])&(x["close"].shift(1)>=x["bb_upper"].shift(1))

    # SamplePriceModification exact structure.
    prior_closes=pd.concat([x["close"].shift(k) for k in range(1,11)],axis=1)
    prior_opens=pd.concat([x["open"].shift(k) for k in range(1,11)],axis=1)
    x["spm_long"]=(prior_closes.lt(x["close"],axis=0).all(axis=1) &
                   prior_opens.lt(x["close"],axis=0).all(axis=1) &
                   (x["open"]<x["close"]))
    x["spm_short"]=(prior_closes.gt(x["close"],axis=0).all(axis=1) &
                    prior_opens.gt(x["close"],axis=0).all(axis=1) &
                    (x["open"]>x["close"]))

    return {d:g.reset_index(drop=True) for d,g in x.groupby("_datekey",sort=True)}


def aggregate_5m(sessions):
    rows=[]
    for d,g0 in sessions.items():
        g=add_bar_start(g0)
        for j in range(78):
            b=g.iloc[j*5:(j+1)*5]
            if len(b)<5: break
            rows.append(dict(
                date=d,block=j,start_idx=j*5,end_idx=(j+1)*5-1,
                start_et=b.iloc[0]["bar_start_et"],
                close_et=b.iloc[-1]["timestamp_et"],
                open=float(b.iloc[0]["open"]),high=float(b["high"].max()),
                low=float(b["low"].min()),close=float(b.iloc[-1]["close"]),
                volume=float(b["volume"].sum())
            ))
    x=pd.DataFrame(rows).sort_values(["date","block"]).reset_index(drop=True)
    tp=(x["high"]+x["low"]+x["close"])/3
    raw=tp*x["volume"]
    direction=np.sign(tp.diff())
    pos=raw.where(direction>0,0.0)
    neg=raw.where(direction<0,0.0)
    pmf=pos.rolling(14,min_periods=14).sum()
    nmf=neg.rolling(14,min_periods=14).sum()
    ratio=pmf/nmf.replace(0,np.nan)
    x["mfi14"]=100-100/(1+ratio)
    x.loc[(nmf==0)&(pmf>0),"mfi14"]=100.0
    ema12=x["close"].ewm(span=12,adjust=False).mean()
    ema26=x["close"].ewm(span=26,adjust=False).mean()
    macd=ema12-ema26
    sig=macd.ewm(span=9,adjust=False).mean()
    x["macd_diff"]=macd-sig
    x["diff_cross_up0"]=(x["macd_diff"]>0)&(x["macd_diff"].shift(1)<=0)
    return x



def aggregate_30m(sessions):
    rows=[]
    for d,g0 in sessions.items():
        g=add_bar_start(g0)
        for j in range(13):
            b=g.iloc[j*30:(j+1)*30]
            if len(b)<30: break
            rows.append(dict(
                date=d,block=j,start_idx=j*30,end_idx=(j+1)*30-1,
                start_et=b.iloc[0]["bar_start_et"],
                close_et=b.iloc[-1]["timestamp_et"],
                open=float(b.iloc[0]["open"]),high=float(b["high"].max()),
                low=float(b["low"].min()),close=float(b.iloc[-1]["close"]),
                volume=float(b["volume"].sum())
            ))
    x=pd.DataFrame(rows).sort_values(["date","block"]).reset_index(drop=True)
    x["sma200"]=x["close"].rolling(200,min_periods=200).mean()
    x["sma5"]=x["close"].rolling(5,min_periods=5).mean()
    x["rsi2"]=wilder_rsi(x["close"],2)
    return x


def add_session_vwap_bands(sessions):
    out={}
    for d,g0 in sessions.items():
        g=add_bar_start(g0)
        tp=(g["high"]+g["low"]+g["close"])/3.0
        v=g["volume"].astype(float)
        cv=v.cumsum().replace(0,np.nan)
        mean=(tp*v).cumsum()/cv
        second=((tp**2)*v).cumsum()/cv
        var=(second-mean**2).clip(lower=0)
        sd=np.sqrt(var)
        g["vwap"]=mean
        g["lower2"]=mean-2*sd
        g["band_dist"]=mean-g["lower2"]
        cond=g["band_dist"].between(10.0,12.0,inclusive="both")
        # 15 consecutive completed minutes incl current signal bar.
        g["band15"]=cond.astype(int).rolling(15,min_periods=15).sum().eq(15)
        out[d]=g.reset_index(drop=True)
    return out


# -----------------------------
# Common intraday simulators
# -----------------------------

def simulate_cross_reversal(sessions,news_by_date,round_id,name,up_col,dn_col,
                            long_on_up=True,stop_ticks=None,target_ticks=None):
    rows=[]; skips=0; forced=0
    for d,g0 in sessions.items():
        g=add_bar_start(g0)
        nd=news_by_date.get(d)
        dls=deadlines_for_day(nd)
        pos=0; entry=None; entry_ts=None; stop=None; target=None; pending=0
        for i in range(len(g)):
            b=g.iloc[i]; ts=b["bar_start_et"]
            # Forced news exit at exact T-5 open.
            if pos!=0 and ts in dls:
                rows.append(record(round_id,name,d,pos,entry,float(b["open"]),"NEWS",entry_ts,ts))
                pos=0; entry=None; stop=None; target=None; forced+=1
            # Execute prior close signal at this bar open.
            if pending!=0:
                desired=pending
                pending=0
                if pos!=0 and desired!=pos:
                    rows.append(record(round_id,name,d,pos,entry,float(b["open"]),"OPPOSITE",entry_ts,ts))
                    pos=0; entry=None; stop=None; target=None
                hm=ts.hour*60+ts.minute
                if pos==0 and ENTRY_START<=hm<=ENTRY_END:
                    if blocked_entry(ts,nd):
                        skips+=1
                    else:
                        pos=desired; entry=float(b["open"]); entry_ts=ts
                        if stop_ticks is not None:
                            stop=entry-pos*stop_ticks*TICK
                        if target_ticks is not None:
                            target=entry+pos*target_ticks*TICK

            # Intrabar stop/target, stop first.
            if pos!=0 and stop is not None:
                if pos==1:
                    if float(b["low"])<=stop:
                        fill=float(b["open"]) if float(b["open"])<stop else stop
                        rows.append(record(round_id,name,d,pos,entry,fill,"SL",entry_ts,ts))
                        pos=0; entry=None; stop=None; target=None
                    elif target is not None and float(b["high"])>=target:
                        fill=float(b["open"]) if float(b["open"])>target else target
                        rows.append(record(round_id,name,d,pos,entry,fill,"TP",entry_ts,ts))
                        pos=0; entry=None; stop=None; target=None
                else:
                    if float(b["high"])>=stop:
                        fill=float(b["open"]) if float(b["open"])>stop else stop
                        rows.append(record(round_id,name,d,pos,entry,fill,"SL",entry_ts,ts))
                        pos=0; entry=None; stop=None; target=None
                    elif target is not None and float(b["low"])<=target:
                        fill=float(b["open"]) if float(b["open"])<target else target
                        rows.append(record(round_id,name,d,pos,entry,fill,"TP",entry_ts,ts))
                        pos=0; entry=None; stop=None; target=None

            # Build signal on current close for next bar.
            if i < len(g)-1:
                up=bool(b.get(up_col,False)); dn=bool(b.get(dn_col,False))
                if up and not dn:
                    pending=(1 if long_on_up else -1)
                elif dn and not up:
                    pending=(-1 if long_on_up else 1)

        if pos!=0:
            last=g.iloc[-1]
            rows.append(record(round_id,name,d,pos,entry,float(last["close"]),"EOD",entry_ts,last["timestamp_et"]))
    return rows,skips,forced


# -----------------------------
# Round 1
# -----------------------------

def r1_sample_ma(sessions,news):
    return simulate_cross_reversal(
        sessions,news,"R1","R1-S1 SampleMACrossOver 10/25",
        "ma_cross_up","ma_cross_dn",True,None,None
    )


def r1_sample_price_mod(sessions,news):
    name="R1-S2 SamplePriceModification 20/100 BE50"
    rows=[]; skips=0; forced=0
    for d,g0 in sessions.items():
        g=add_bar_start(g0)
        nd=news.get(d); dls=deadlines_for_day(nd)
        pos=0; entry=None; entry_ts=None; stop=None; target=None; pending=0
        for i in range(len(g)):
            b=g.iloc[i]; ts=b["bar_start_et"]
            if pos!=0 and ts in dls:
                rows.append(record("R1",name,d,pos,entry,float(b["open"]),"NEWS",entry_ts,ts))
                pos=0; entry=None; forced+=1
            if pending!=0:
                hm=ts.hour*60+ts.minute
                if pos==0 and ENTRY_START<=hm<=ENTRY_END:
                    if blocked_entry(ts,nd):
                        skips+=1
                    else:
                        pos=pending; entry=float(b["open"]); entry_ts=ts
                        stop=entry-pos*20*TICK
                        target=entry+pos*100*TICK
                pending=0
            if pos!=0:
                if pos==1:
                    if float(b["low"])<=stop:
                        fill=float(b["open"]) if float(b["open"])<stop else stop
                        rows.append(record("R1",name,d,pos,entry,fill,"SL",entry_ts,ts)); pos=0
                    elif float(b["high"])>=target:
                        fill=float(b["open"]) if float(b["open"])>target else target
                        rows.append(record("R1",name,d,pos,entry,fill,"TP",entry_ts,ts)); pos=0
                else:
                    if float(b["high"])>=stop:
                        fill=float(b["open"]) if float(b["open"])>stop else stop
                        rows.append(record("R1",name,d,pos,entry,fill,"SL",entry_ts,ts)); pos=0
                    elif float(b["low"])<=target:
                        fill=float(b["open"]) if float(b["open"])<target else target
                        rows.append(record("R1",name,d,pos,entry,fill,"TP",entry_ts,ts)); pos=0
                if pos!=0:
                    # Source modifies stop after bar close. This affects subsequent bars only.
                    if pos==1 and float(b["close"])>entry+50*TICK:
                        stop=max(stop,entry)
                    elif pos==-1 and float(b["close"])<entry-50*TICK:
                        stop=min(stop,entry)
            if pos==0 and i<len(g)-1:
                if bool(b.get("spm_long",False)): pending=1
                elif bool(b.get("spm_short",False)): pending=-1
        if pos!=0:
            last=g.iloc[-1]
            rows.append(record("R1",name,d,pos,entry,float(last["close"]),"EOD",entry_ts,last["timestamp_et"]))
    return rows,skips,forced



def r1_sma530_pt1(sessions,news):
    name="R1-S3 SMA5/30 lookback2 PT1"
    rows=[]; skips=0; forced=0
    for d,g0 in sessions.items():
        g=add_bar_start(g0); nd=news.get(d); dls=deadlines_for_day(nd)
        pos=False; entry=None; entry_ts=None; target=None; pending=False
        for i in range(len(g)):
            b=g.iloc[i]; ts=b["bar_start_et"]
            if pos and ts in dls:
                rows.append(record("R1",name,d,1,entry,float(b["open"]),"NEWS",entry_ts,ts))
                pos=False; forced+=1
            if pending:
                pending=False
                hm=ts.hour*60+ts.minute
                if not pos and ENTRY_START<=hm<=ENTRY_END:
                    if blocked_entry(ts,nd): skips+=1
                    else:
                        pos=True; entry=float(b["open"]); entry_ts=ts; target=entry+TICK
            if pos and float(b["high"])>=target:
                fill=float(b["open"]) if float(b["open"])>target else target
                rows.append(record("R1",name,d,1,entry,fill,"TP",entry_ts,ts)); pos=False
            if (not pos) and i<len(g)-1 and bool(b.get("sma530_cross_up_2",False)):
                pending=True
        if pos:
            last=g.iloc[-1]
            rows.append(record("R1",name,d,1,entry,float(last["close"]),"EOD",entry_ts,last["timestamp_et"]))
    return rows,skips,forced


def r1_ema_rsi_dynamic(sessions,news):
    name="R1-S4 EMA20/40 + RSI14s3 PT200 dynEMA40"
    rows=[]; skips=0; forced=0
    for d,g0 in sessions.items():
        g=add_bar_start(g0); nd=news.get(d); dls=deadlines_for_day(nd)
        pos=False; entry=None; entry_ts=None; target=None; pending=False
        for i in range(len(g)):
            b=g.iloc[i]; ts=b["bar_start_et"]
            if pos and ts in dls:
                rows.append(record("R1",name,d,1,entry,float(b["open"]),"NEWS",entry_ts,ts))
                pos=False; forced+=1
            if pending:
                pending=False
                hm=ts.hour*60+ts.minute
                if not pos and ENTRY_START<=hm<=ENTRY_END:
                    if blocked_entry(ts,nd): skips+=1
                    else:
                        pos=True; entry=float(b["open"]); entry_ts=ts; target=entry+200*TICK
            if pos:
                dyn=float(g.iloc[i-1]["ema40"]) if i>0 and pd.notna(g.iloc[i-1]["ema40"]) else np.nan
                if np.isfinite(dyn):
                    if float(b["open"])<=dyn:
                        rows.append(record("R1",name,d,1,entry,float(b["open"]),"EMA40_STOP",entry_ts,ts)); pos=False
                    elif float(b["low"])<=dyn:
                        rows.append(record("R1",name,d,1,entry,dyn,"EMA40_STOP",entry_ts,ts)); pos=False
                if pos and float(b["high"])>=target:
                    fill=float(b["open"]) if float(b["open"])>target else target
                    rows.append(record("R1",name,d,1,entry,fill,"TP",entry_ts,ts)); pos=False
            if (not pos) and i<len(g)-1:
                if bool(b.get("rsi60_cross_10",False)) and pd.notna(b.get("ema20")) and pd.notna(b.get("ema40")) and float(b["ema20"])>float(b["ema40"]):
                    pending=True
        if pos:
            last=g.iloc[-1]
            rows.append(record("R1",name,d,1,entry,float(last["close"]),"EOD",entry_ts,last["timestamp_et"]))
    return rows,skips,forced


def r1_donchian20(sessions,news):
    name="R1-S5 Basic Donchian20 long"
    rows=[]; skips=0; forced=0
    for d,g0 in sessions.items():
        g=add_bar_start(g0); nd=news.get(d); dls=deadlines_for_day(nd)
        pos=False; entry=None; entry_ts=None; pending_entry=False; pending_exit=False
        for i in range(len(g)):
            b=g.iloc[i]; ts=b["bar_start_et"]
            if pos and ts in dls:
                rows.append(record("R1",name,d,1,entry,float(b["open"]),"NEWS",entry_ts,ts))
                pos=False; forced+=1
            if pending_exit:
                pending_exit=False
                if pos:
                    rows.append(record("R1",name,d,1,entry,float(b["open"]),"DONCH_EXIT",entry_ts,ts)); pos=False
            if pending_entry:
                pending_entry=False
                hm=ts.hour*60+ts.minute
                if not pos and ENTRY_START<=hm<=ENTRY_END:
                    if blocked_entry(ts,nd): skips+=1
                    else: pos=True; entry=float(b["open"]); entry_ts=ts
            if i<len(g)-1:
                if pos and bool(b.get("donch20_cross_dn",False)): pending_exit=True
                elif (not pos) and bool(b.get("donch20_cross_up",False)): pending_entry=True
        if pos:
            last=g.iloc[-1]
            rows.append(record("R1",name,d,1,entry,float(last["close"]),"EOD",entry_ts,last["timestamp_et"]))
    return rows,skips,forced


# -----------------------------
# Round 2
# -----------------------------

def r2_macd_contrarian(sessions,news):
    return simulate_cross_reversal(
        sessions,news,"R2","R2-S1 Contrarian MACD 10/10",
        "macd_cross_up","macd_cross_dn",False,10,10
    )


def r2_mfi_macd(sessions, bars5, news):
    name="R2-S2 MFI14+MACD 5m long"
    rows=[]; skips=0; forced=0
    for d,g0 in sessions.items():
        g=add_bar_start(g0)
        b5=bars5[bars5.date==d].reset_index(drop=True)
        if b5.empty: continue
        nd=news.get(d); dls=deadlines_for_day(nd)
        occupied_until=pd.Timestamp.min.tz_localize("America/New_York")
        for i in range(1,len(b5)-1):
            s=b5.iloc[i]
            if not (pd.notna(s["mfi14"]) and float(s["mfi14"])<20 and bool(s["diff_cross_up0"])):
                continue
            entry_ts=s["close_et"]
            if entry_ts<=occupied_until: continue
            hm=entry_ts.hour*60+entry_ts.minute
            if not (ENTRY_START<=hm<=ENTRY_END): continue
            if blocked_entry(entry_ts,nd):
                skips+=1; continue
            m=g.index[g["bar_start_et"]==entry_ts].tolist()
            if not m: continue
            entry_idx=int(m[0]); entry=float(g.iloc[entry_idx]["open"])
            stop=float(s["low"])

            # Source exit condition first known at 5m close; execute next 5m open.
            normal_exit_ts=g.iloc[-1]["timestamp_et"]
            reason="EOD"
            for j in range(i+1,len(b5)-1):
                q=b5.iloc[j]
                if pd.notna(q["mfi14"]) and float(q["mfi14"])>80 and float(q["macd_diff"])<float(b5.iloc[j-1]["macd_diff"]):
                    normal_exit_ts=q["close_et"]; reason="SIGNAL"; break

            scan=g[(g["bar_start_et"]>=entry_ts)&(g["bar_start_et"]<=normal_exit_ts)]
            exit_px=None; exit_ts=None; exit_reason=None
            for _,bar in scan.iterrows():
                ts=bar["bar_start_et"]
                if ts in dls:
                    exit_px=float(bar["open"]); exit_ts=ts; exit_reason="NEWS"; forced+=1; break
                if float(bar["low"])<=stop:
                    exit_px=float(bar["open"]) if float(bar["open"])<stop else stop
                    exit_ts=ts; exit_reason="SL"; break
                if ts>=normal_exit_ts and reason=="SIGNAL":
                    exit_px=float(bar["open"]); exit_ts=ts; exit_reason="SIGNAL"; break
            if exit_px is None:
                exit_px=float(g.iloc[-1]["close"]); exit_ts=g.iloc[-1]["timestamp_et"]; exit_reason="EOD"
            rows.append(record("R2",name,d,1,entry,exit_px,exit_reason,entry_ts,exit_ts))
            occupied_until=pd.Timestamp(exit_ts)
    return rows,skips,forced



def r2_inside_directional(sessions,news):
    name="R2-S3 InsideBar directional close SL10 PT25"
    rows=[]; skips=0; forced=0; ambiguous=0
    for d,g0 in sessions.items():
        g=add_bar_start(g0); nd=news.get(d); dls=deadlines_for_day(nd)
        available=1
        i=1
        while i < len(g)-1:
            if i<available:
                i+=1; continue
            b=g.iloc[i]; p=g.iloc[i-1]
            inside=float(b["high"])<float(p["high"]) and float(b["low"])>float(p["low"])
            if not inside:
                i+=1; continue
            direction=0; level=None
            if float(b["close"])==float(b["high"]):
                direction=1; level=float(b["high"])+TICK
            elif float(b["close"])==float(b["low"]):
                direction=-1; level=float(b["low"])-TICK
            else:
                i+=1; continue
            nb=g.iloc[i+1]; ts=nb["bar_start_et"]
            hm=ts.hour*60+ts.minute
            if not (ENTRY_START<=hm<=ENTRY_END):
                i+=1; continue
            hit=(float(nb["high"])>=level) if direction==1 else (float(nb["low"])<=level)
            if not hit:
                i+=1; continue
            if blocked_entry(ts,nd):
                skips+=1; i+=1; continue
            entry=max(level,float(nb["open"])) if direction==1 else min(level,float(nb["open"]))
            stop=entry-direction*10*TICK
            target=entry+direction*25*TICK
            exit_px=None; exit_idx=None; reason=None; exit_ts=None
            for k in range(i+1,len(g)):
                q=g.iloc[k]; qts=q["bar_start_et"]
                if qts in dls:
                    exit_px=float(q["open"]); exit_idx=k; reason="NEWS"; exit_ts=qts; forced+=1; break
                if direction==1:
                    if float(q["low"])<=stop:
                        exit_px=float(q["open"]) if float(q["open"])<stop else stop; exit_idx=k; reason="SL"; exit_ts=qts; break
                    if float(q["high"])>=target:
                        exit_px=float(q["open"]) if float(q["open"])>target else target; exit_idx=k; reason="TP"; exit_ts=qts; break
                else:
                    if float(q["high"])>=stop:
                        exit_px=float(q["open"]) if float(q["open"])>stop else stop; exit_idx=k; reason="SL"; exit_ts=qts; break
                    if float(q["low"])<=target:
                        exit_px=float(q["open"]) if float(q["open"])<target else target; exit_idx=k; reason="TP"; exit_ts=qts; break
            if exit_px is None:
                last=g.iloc[-1]; exit_px=float(last["close"]); exit_idx=len(g)-1; reason="EOD"; exit_ts=last["timestamp_et"]
            rows.append(record("R2",name,d,direction,entry,exit_px,reason,ts,exit_ts))
            available=exit_idx+1
            i=available
        # next session
    return rows,skips,forced


def r2_inside_structural(sessions,news):
    name="R2-S4 InsideBar structural bracket"
    rows=[]; skips=0; forced=0
    for d,g0 in sessions.items():
        g=add_bar_start(g0); nd=news.get(d); dls=deadlines_for_day(nd)
        available=1; i=1
        while i < len(g)-1:
            if i<available:
                i+=1; continue
            b=g.iloc[i]; p=g.iloc[i-1]
            if not (float(b["high"])<float(p["high"]) and float(b["low"])>float(p["low"])):
                i+=1; continue
            buy=float(b["high"])+TICK; sell=float(b["low"])-TICK
            nb=g.iloc[i+1]; ts=nb["bar_start_et"]
            hm=ts.hour*60+ts.minute
            if not (ENTRY_START<=hm<=ENTRY_END):
                i+=1; continue
            hit_l=float(nb["high"])>=buy; hit_s=float(nb["low"])<=sell
            if hit_l and hit_s:
                i+=1; continue
            if not hit_l and not hit_s:
                i+=1; continue
            if blocked_entry(ts,nd):
                skips+=1; i+=1; continue
            direction=1 if hit_l else -1
            entry=max(buy,float(nb["open"])) if direction==1 else min(sell,float(nb["open"]))
            stop=(float(b["low"])-TICK) if direction==1 else (float(b["high"])+TICK)
            exit_px=None; exit_idx=None; reason=None; exit_ts=None
            for k in range(i+1,len(g)):
                q=g.iloc[k]; qts=q["bar_start_et"]
                if qts in dls:
                    exit_px=float(q["open"]); exit_idx=k; reason="NEWS"; exit_ts=qts; forced+=1; break
                if direction==1 and float(q["low"])<=stop:
                    exit_px=float(q["open"]) if float(q["open"])<stop else stop; exit_idx=k; reason="SL"; exit_ts=qts; break
                if direction==-1 and float(q["high"])>=stop:
                    exit_px=float(q["open"]) if float(q["open"])>stop else stop; exit_idx=k; reason="SL"; exit_ts=qts; break
            if exit_px is None:
                last=g.iloc[-1]; exit_px=float(last["close"]); exit_idx=len(g)-1; reason="EOD"; exit_ts=last["timestamp_et"]
            rows.append(record("R2",name,d,direction,entry,exit_px,reason,ts,exit_ts))
            available=exit_idx+1; i=available
    return rows,skips,forced


def r2_boll100_fade(sessions,news):
    name="R2-S5 Bollinger100 1.5dev short $2500/$5000"
    rows=[]; skips=0; forced=0
    for d,g0 in sessions.items():
        g=add_bar_start(g0); nd=news.get(d); dls=deadlines_for_day(nd)
        pos=False; entry=None; entry_ts=None; stop=None; target=None; pending=False
        for i in range(len(g)):
            b=g.iloc[i]; ts=b["bar_start_et"]
            if pos and ts in dls:
                rows.append(record("R2",name,d,-1,entry,float(b["open"]),"NEWS",entry_ts,ts)); pos=False; forced+=1
            if pending:
                pending=False
                hm=ts.hour*60+ts.minute
                if not pos and ENTRY_START<=hm<=ENTRY_END:
                    if blocked_entry(ts,nd): skips+=1
                    else:
                        pos=True; entry=float(b["open"]); entry_ts=ts
                        target=entry-500.0; stop=entry+1000.0
            if pos:
                if float(b["high"])>=stop:
                    fill=float(b["open"]) if float(b["open"])>stop else stop
                    rows.append(record("R2",name,d,-1,entry,fill,"SL",entry_ts,ts)); pos=False
                elif float(b["low"])<=target:
                    fill=float(b["open"]) if float(b["open"])<target else target
                    rows.append(record("R2",name,d,-1,entry,fill,"TP",entry_ts,ts)); pos=False
            if (not pos) and i<len(g)-1 and pd.notna(b.get("bb100_upper15")) and float(b["close"])>float(b["bb100_upper15"]):
                pending=True
        if pos:
            last=g.iloc[-1]; rows.append(record("R2",name,d,-1,entry,float(last["close"]),"EOD",entry_ts,last["timestamp_et"]))
    return rows,skips,forced


# -----------------------------
# Round 3
# -----------------------------

def r3_vwap2(sessions,news):
    name="R3-S1 VWAP lower2 10-12pt mean reversion"
    rows=[]; skips=0; forced=0
    vs=add_session_vwap_bands(sessions)
    for d,g in vs.items():
        nd=news.get(d); dls=deadlines_for_day(nd)
        pos=False; entry=None; entry_ts=None; stop=None; pending=False
        for i in range(len(g)):
            b=g.iloc[i]; ts=b["bar_start_et"]
            if pos and ts in dls:
                rows.append(record("R3",name,d,1,entry,float(b["open"]),"NEWS",entry_ts,ts))
                pos=False; forced+=1
            if pending:
                pending=False
                hm=ts.hour*60+ts.minute
                if not pos and ENTRY_START<=hm<=ENTRY_END:
                    if blocked_entry(ts,nd):
                        skips+=1
                    else:
                        pos=True; entry=float(b["open"]); entry_ts=ts; stop=entry-5.0
            if pos:
                # stop first; dynamic VWAP target known causally from prior completed minute
                target=float(g.iloc[i-1]["vwap"]) if i>0 and pd.notna(g.iloc[i-1]["vwap"]) else np.nan
                if float(b["low"])<=stop:
                    fill=float(b["open"]) if float(b["open"])<stop else stop
                    rows.append(record("R3",name,d,1,entry,fill,"SL",entry_ts,ts)); pos=False
                elif np.isfinite(target) and float(b["high"])>=target:
                    fill=float(b["open"]) if float(b["open"])>target else target
                    rows.append(record("R3",name,d,1,entry,fill,"VWAP",entry_ts,ts)); pos=False
            if (not pos) and i<len(g)-1:
                if bool(b["band15"]) and pd.notna(b["lower2"]) and float(b["low"])<=float(b["lower2"]):
                    pending=True
        if pos:
            last=g.iloc[-1]
            rows.append(record("R3",name,d,1,entry,float(last["close"]),"EOD",entry_ts,last["timestamp_et"]))
    return rows,skips,forced


def r3_bollinger(sessions,news):
    name="R3-S2 Bollinger(2,14) lower-to-upper long"
    rows=[]; skips=0; forced=0
    for d,g0 in sessions.items():
        g=add_bar_start(g0)
        nd=news.get(d); dls=deadlines_for_day(nd)
        pos=False; entry=None; entry_ts=None; pending_entry=False; pending_exit=False
        for i in range(len(g)):
            b=g.iloc[i]; ts=b["bar_start_et"]
            if pos and ts in dls:
                rows.append(record("R3",name,d,1,entry,float(b["open"]),"NEWS",entry_ts,ts))
                pos=False; forced+=1
            if pending_exit:
                pending_exit=False
                if pos:
                    rows.append(record("R3",name,d,1,entry,float(b["open"]),"BOLL_UPPER",entry_ts,ts))
                    pos=False
            if pending_entry:
                pending_entry=False
                hm=ts.hour*60+ts.minute
                if not pos and ENTRY_START<=hm<=ENTRY_END:
                    if blocked_entry(ts,nd): skips+=1
                    else:
                        pos=True; entry=float(b["open"]); entry_ts=ts
            if i<len(g)-1:
                if pos and bool(b.get("bb_cross_below_upper",False)):
                    pending_exit=True
                elif (not pos) and bool(b.get("bb_cross_above_lower",False)):
                    pending_entry=True
        if pos:
            last=g.iloc[-1]
            rows.append(record("R3",name,d,1,entry,float(last["close"]),"EOD",entry_ts,last["timestamp_et"]))
    return rows,skips,forced



def _prior_rth_levels(sessions):
    dates=sorted(sessions)
    out={}
    for j in range(1,len(dates)):
        prev=dates[j-1]; d=dates[j]
        g=sessions[prev]
        out[d]={
            "high":float(g["high"].max()),
            "low":float(g["low"].min()),
            "close":float(g.iloc[-1]["close"]),
        }
    return out


def r3_prior_close_pt25(sessions,news):
    name="R3-S3 PriorClose cross PT25"
    rows=[]; skips=0; forced=0
    levels=_prior_rth_levels(sessions)
    for d,g0 in sessions.items():
        if d not in levels: continue
        g=add_bar_start(g0); nd=news.get(d); dls=deadlines_for_day(nd)
        lvl=levels[d]["close"]
        pos=0; entry=None; entry_ts=None; target=None; pending=0
        for i in range(len(g)):
            b=g.iloc[i]; ts=b["bar_start_et"]
            if pos!=0 and ts in dls:
                rows.append(record("R3",name,d,pos,entry,float(b["open"]),"NEWS",entry_ts,ts))
                pos=0; forced+=1
            if pending!=0:
                direction=pending; pending=0
                hm=ts.hour*60+ts.minute
                if pos==0 and ENTRY_START<=hm<=ENTRY_END:
                    if blocked_entry(ts,nd): skips+=1
                    else:
                        pos=direction; entry=float(b["open"]); entry_ts=ts
                        target=entry+direction*25*TICK
            if pos!=0:
                if pos==1 and float(b["high"])>=target:
                    fill=float(b["open"]) if float(b["open"])>target else target
                    rows.append(record("R3",name,d,pos,entry,fill,"TP",entry_ts,ts)); pos=0
                elif pos==-1 and float(b["low"])<=target:
                    fill=float(b["open"]) if float(b["open"])<target else target
                    rows.append(record("R3",name,d,pos,entry,fill,"TP",entry_ts,ts)); pos=0
            if pos==0 and i>0 and i<len(g)-1:
                prev=g.iloc[i-1]
                long_sig=float(b["low"])>lvl and float(prev["low"])<=lvl
                short_sig=float(b["high"])<lvl and float(prev["high"])>=lvl
                if long_sig and not short_sig: pending=1
                elif short_sig and not long_sig: pending=-1
        if pos!=0:
            last=g.iloc[-1]
            rows.append(record("R3",name,d,pos,entry,float(last["close"]),"EOD",entry_ts,last["timestamp_et"]))
    return rows,skips,forced


def r3_prior_hilo_breakout(sessions,news):
    name="R3-S4 PriorHighLow breakout signalbar stop"
    rows=[]; skips=0; forced=0
    levels=_prior_rth_levels(sessions)
    for d,g0 in sessions.items():
        if d not in levels: continue
        g=add_bar_start(g0); nd=news.get(d); dls=deadlines_for_day(nd)
        ph=levels[d]["high"]; pl=levels[d]["low"]; session_open=float(g.iloc[0]["open"])
        pos=0; entry=None; entry_ts=None; stop=None; pending=None
        for i in range(len(g)):
            b=g.iloc[i]; ts=b["bar_start_et"]
            if pos!=0 and ts in dls:
                rows.append(record("R3",name,d,pos,entry,float(b["open"]),"NEWS",entry_ts,ts)); pos=0; forced+=1
            if pending is not None:
                direction,st=pending; pending=None
                hm=ts.hour*60+ts.minute
                if pos==0 and ENTRY_START<=hm<=ENTRY_END:
                    if blocked_entry(ts,nd): skips+=1
                    else:
                        pos=direction; entry=float(b["open"]); entry_ts=ts; stop=st
            if pos!=0:
                if pos==1 and float(b["low"])<=stop:
                    fill=float(b["open"]) if float(b["open"])<stop else stop
                    rows.append(record("R3",name,d,pos,entry,fill,"SL",entry_ts,ts)); pos=0
                elif pos==-1 and float(b["high"])>=stop:
                    fill=float(b["open"]) if float(b["open"])>stop else stop
                    rows.append(record("R3",name,d,pos,entry,fill,"SL",entry_ts,ts)); pos=0
            if pos==0 and i>0 and i<len(g)-1:
                p=g.iloc[i-1]
                long_sig=float(b["close"])>ph and float(p["close"])<=ph and float(b["close"])>session_open
                short_sig=float(b["close"])<pl and float(p["close"])>=pl and float(b["close"])<session_open
                if long_sig and not short_sig:
                    pending=(1,float(b["low"])-TICK)
                elif short_sig and not long_sig:
                    pending=(-1,float(b["high"])+TICK)
        if pos!=0:
            last=g.iloc[-1]
            rows.append(record("R3",name,d,pos,entry,float(last["close"]),"EOD",entry_ts,last["timestamp_et"]))
    return rows,skips,forced


def r3_prior_close_short_100_200(sessions,news):
    name="R3-S5 PriorClose cross short SL100 PT200"
    rows=[]; skips=0; forced=0
    levels=_prior_rth_levels(sessions)
    for d,g0 in sessions.items():
        if d not in levels: continue
        g=add_bar_start(g0); nd=news.get(d); dls=deadlines_for_day(nd)
        lvl=levels[d]["close"]
        pos=False; entry=None; entry_ts=None; stop=None; target=None; pending=False
        for i in range(len(g)):
            b=g.iloc[i]; ts=b["bar_start_et"]
            if pos and ts in dls:
                rows.append(record("R3",name,d,-1,entry,float(b["open"]),"NEWS",entry_ts,ts)); pos=False; forced+=1
            if pending:
                pending=False
                hm=ts.hour*60+ts.minute
                if not pos and ENTRY_START<=hm<=ENTRY_END:
                    if blocked_entry(ts,nd): skips+=1
                    else:
                        pos=True; entry=float(b["open"]); entry_ts=ts
                        stop=entry+100*TICK; target=entry-200*TICK
            if pos:
                if float(b["high"])>=stop:
                    fill=float(b["open"]) if float(b["open"])>stop else stop
                    rows.append(record("R3",name,d,-1,entry,fill,"SL",entry_ts,ts)); pos=False
                elif float(b["low"])<=target:
                    fill=float(b["open"]) if float(b["open"])<target else target
                    rows.append(record("R3",name,d,-1,entry,fill,"TP",entry_ts,ts)); pos=False
            if (not pos) and i>0 and i<len(g)-1:
                p=g.iloc[i-1]
                if float(b["close"])<lvl and float(p["close"])>=lvl:
                    pending=True
        if pos:
            last=g.iloc[-1]
            rows.append(record("R3",name,d,-1,entry,float(last["close"]),"EOD",entry_ts,last["timestamp_et"]))
    return rows,skips,forced


# -----------------------------
# Daily helpers / Round 4
# -----------------------------

def wilder_rsi(series,period):
    d=series.diff()
    gain=d.clip(lower=0)
    loss=(-d).clip(lower=0)
    avg_g=gain.ewm(alpha=1/period,adjust=False,min_periods=period).mean()
    avg_l=loss.ewm(alpha=1/period,adjust=False,min_periods=period).mean()
    rs=avg_g/avg_l.replace(0,np.nan)
    out=100-100/(1+rs)
    out[(avg_l==0)&(avg_g>0)]=100
    return out


def daily_table(sessions):
    rows=[]
    for d,g0 in sessions.items():
        g=add_bar_start(g0)
        rows.append(dict(date=d,
                         open=float(g.iloc[0]["open"]),
                         high=float(g["high"].max()),
                         low=float(g["low"].min()),
                         close=float(g.iloc[-1]["close"]),
                         open_ts=g.iloc[0]["bar_start_et"],
                         close_ts=g.iloc[-1]["timestamp_et"]))
    x=pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    x["sma200"]=x["close"].rolling(200,min_periods=200).mean()
    x["sma5"]=x["close"].rolling(5,min_periods=5).mean()
    x["rsi2"]=wilder_rsi(x["close"],2)
    x["low7close"]=x["close"].rolling(7,min_periods=7).min()
    x["high7close"]=x["close"].rolling(7,min_periods=7).max()
    pc=x["close"].shift(1)
    tr=pd.concat([
        x["high"]-x["low"],
        (x["high"]-pc).abs(),
        (x["low"]-pc).abs()
    ],axis=1).max(axis=1)
    x["atr20"]=tr.ewm(alpha=1/20,adjust=False,min_periods=20).mean()
    x["atr20_prev"]=x["atr20"].shift(1)
    for n in (10,20,55):
        x[f"high{n}_prev"]=x["high"].rolling(n,min_periods=n).max().shift(1)
        x[f"low{n}_prev"]=x["low"].rolling(n,min_periods=n).min().shift(1)
    return x


def simulate_daily_connors(daily,deadlines,lookup,news_by_date,kind):
    if kind=="rsi2":
        name="R4-S1 Connors RSI2<5 / SMA200"
    else:
        name="R4-S2 Connors Double7"
    rows=[]; skips=0; forced=0
    i=0
    while i < len(daily)-1:
        s=daily.iloc[i]
        if kind=="rsi2":
            sig=(pd.notna(s["sma200"]) and pd.notna(s["rsi2"]) and
                 float(s["close"])>float(s["sma200"]) and float(s["rsi2"])<5)
        else:
            sig=(pd.notna(s["sma200"]) and pd.notna(s["low7close"]) and
                 float(s["close"])>float(s["sma200"]) and float(s["close"])<=float(s["low7close"]))
        if not sig:
            i+=1; continue
        eidx=i+1
        e=daily.iloc[eidx]
        entry_ts=e["open_ts"]
        nd=news_by_date.get(e["date"])
        if blocked_entry(entry_ts,nd):
            skips+=1; i+=1; continue
        entry=float(e["open"])

        # find normal daily exit
        xidx=None
        for j in range(eidx,len(daily)):
            q=daily.iloc[j]
            if kind=="rsi2":
                cond=pd.notna(q["sma5"]) and float(q["close"])>float(q["sma5"])
            else:
                cond=pd.notna(q["high7close"]) and float(q["close"])>=float(q["high7close"])
            if cond:
                xidx=j; break
        if xidx is None: xidx=len(daily)-1
        normal_ts=daily.iloc[xidx]["close_ts"]
        normal_px=float(daily.iloc[xidx]["close"])

        dl=first_global_deadline_after(deadlines,entry_ts,normal_ts)
        if dl is not None:
            px,actual=price_at_or_after(dl,lookup)
            if px is not None:
                rows.append(record("R4",name,e["date"],1,entry,px,"NEWS",entry_ts,actual))
                forced+=1
                # permit a new daily signal at/after the forced exit date close
                forced_date=pd.Timestamp(actual).date().isoformat()
                matches=daily.index[daily["date"]>=forced_date].tolist()
                i=(matches[0] if matches else xidx)
                continue
            # If T-5 falls while the futures market is closed, there is no
            # causal executable price at the deadline; that event cannot force
            # a fill and the position remains unchanged.
        rows.append(record("R4",name,e["date"],1,entry,normal_px,"DAILY_EXIT",entry_ts,normal_ts))
        i=xidx+1
    return rows,skips,forced



def r4_oops_fpo(sessions,full,news_by_date,deadlines):
    name="R4-S3 Larry Williams Oops FPO"
    rows=[]; skips=0; forced=0
    dates=sorted(sessions)
    fullx=full.sort_values("bar_start_et").reset_index(drop=True)
    deadline_set=set(deadlines)
    j=1
    while j < len(dates):
        d,prev=dates[j],dates[j-1]
        g=add_bar_start(sessions[d]); pg=sessions[prev]
        prior_low=float(pg["low"].min()); prior_high=float(pg["high"].max())
        op=float(g.iloc[0]["open"])
        direction=0; level=None
        if op<prior_low:
            direction=1; level=prior_low
        elif op>prior_high:
            direction=-1; level=prior_high
        if direction==0:
            j+=1; continue
        nd=news_by_date.get(d)
        entry_idx=None; entry=None; entry_ts=None
        for i in range(len(g)):
            b=g.iloc[i]; ts=b["bar_start_et"]
            hm=ts.hour*60+ts.minute
            if hm>ENTRY_END: break
            hit=float(b["high"])>=level if direction==1 else float(b["low"])<=level
            if not hit: continue
            if blocked_entry(ts,nd):
                skips+=1; continue
            entry_idx=i; entry_ts=ts
            entry=max(level,float(b["open"])) if direction==1 else min(level,float(b["open"]))
            break
        if entry_idx is None:
            j+=1; continue
        stop=(float(g.iloc[:entry_idx+1]["low"].min()) if direction==1
              else float(g.iloc[:entry_idx+1]["high"].max()))

        # First subsequent RTH open that is profitable.
        fpo_idx=None; normal_ts=None; normal_px=None
        for k in range(j+1,len(dates)):
            q=add_bar_start(sessions[dates[k]])
            qop=float(q.iloc[0]["open"])
            if (direction==1 and qop>entry) or (direction==-1 and qop<entry):
                fpo_idx=k; normal_ts=q.iloc[0]["bar_start_et"]; normal_px=qop; break
        if normal_ts is None:
            q=add_bar_start(sessions[dates[-1]])
            normal_ts=q.iloc[-1]["timestamp_et"]; normal_px=float(q.iloc[-1]["close"]); fpo_idx=len(dates)-1

        scan=fullx[(fullx["bar_start_et"]>=entry_ts)&(fullx["bar_start_et"]<=normal_ts)]
        exit_px=None; exit_ts=None; reason=None
        for _,bar in scan.iterrows():
            ts=bar["bar_start_et"]
            if ts in deadline_set and ts>entry_ts:
                exit_px=float(bar["open"]); exit_ts=ts; reason="NEWS"; forced+=1; break
            if direction==1 and float(bar["low"])<=stop:
                exit_px=float(bar["open"]) if float(bar["open"])<stop else stop
                exit_ts=ts; reason="SL"; break
            if direction==-1 and float(bar["high"])>=stop:
                exit_px=float(bar["open"]) if float(bar["open"])>stop else stop
                exit_ts=ts; reason="SL"; break
        if exit_px is None:
            exit_px=normal_px; exit_ts=normal_ts; reason="FPO"
        rows.append(record("R4",name,d,direction,entry,exit_px,reason,entry_ts,exit_ts))
        # continue discovery from day of exit or next setup day
        exit_date=pd.Timestamp(exit_ts).tz_convert("America/New_York").date().isoformat() if pd.Timestamp(exit_ts).tzinfo else pd.Timestamp(exit_ts).date().isoformat()
        nxt=[idx for idx,dd in enumerate(dates) if dd>=exit_date and idx>j]
        j=(nxt[0] if nxt else len(dates))
    return rows,skips,forced


def r4_connors_30m(sessions,bars30,news):
    name="R4-S4 Connors RSI2 symmetric 30m 0.15% stop"
    rows=[]; skips=0; forced=0
    for d,g0 in sessions.items():
        g=add_bar_start(g0)
        b30=bars30[bars30.date==d].reset_index(drop=True)
        if b30.empty: continue
        nd=news.get(d); dls=deadlines_for_day(nd)
        available_ts=g.iloc[0]["bar_start_et"]
        for i in range(len(b30)-1):
            s=b30.iloc[i]
            if s["close_et"]<available_ts: continue
            direction=0
            if pd.notna(s["rsi2"]) and pd.notna(s["sma200"]):
                if float(s["rsi2"])<5 and float(s["close"])>float(s["sma200"]): direction=1
                elif float(s["rsi2"])>95 and float(s["close"])<float(s["sma200"]): direction=-1
            if direction==0: continue
            entry_ts=b30.iloc[i+1]["start_et"]
            hm=entry_ts.hour*60+entry_ts.minute
            if hm<ENTRY_START or hm>ENTRY_END: continue
            if blocked_entry(entry_ts,nd):
                skips+=1; continue
            entry=float(b30.iloc[i+1]["open"])
            stop=entry*(1-0.0015) if direction==1 else entry*(1+0.0015)

            normal_exit_ts=g.iloc[-1]["timestamp_et"]; reason="EOD"
            for j in range(i+1,len(b30)-1):
                q=b30.iloc[j]
                if pd.isna(q["sma5"]) or pd.isna(q["sma200"]): continue
                if direction==1:
                    cond=float(q["close"])>float(q["sma5"]) or float(q["close"])<float(q["sma200"])
                else:
                    cond=float(q["close"])<float(q["sma5"]) or float(q["close"])>float(q["sma200"])
                if cond:
                    normal_exit_ts=b30.iloc[j+1]["start_et"]; reason="SIGNAL"; break

            scan=g[(g["bar_start_et"]>=entry_ts)&(g["bar_start_et"]<=normal_exit_ts)]
            exit_px=None; exit_ts=None; exit_reason=None
            for _,bar in scan.iterrows():
                ts=bar["bar_start_et"]
                if ts in dls:
                    exit_px=float(bar["open"]); exit_ts=ts; exit_reason="NEWS"; forced+=1; break
                if direction==1 and float(bar["low"])<=stop:
                    exit_px=float(bar["open"]) if float(bar["open"])<stop else stop
                    exit_ts=ts; exit_reason="SL"; break
                if direction==-1 and float(bar["high"])>=stop:
                    exit_px=float(bar["open"]) if float(bar["open"])>stop else stop
                    exit_ts=ts; exit_reason="SL"; break
                if reason=="SIGNAL" and ts>=normal_exit_ts:
                    exit_px=float(bar["open"]); exit_ts=ts; exit_reason="SIGNAL"; break
            if exit_px is None:
                exit_px=float(g.iloc[-1]["close"]); exit_ts=g.iloc[-1]["timestamp_et"]; exit_reason="EOD"
            rows.append(record("R4",name,d,direction,entry,exit_px,exit_reason,entry_ts,exit_ts))
            available_ts=pd.Timestamp(exit_ts)
    return rows,skips,forced


def r4_donchian20_10(daily,deadlines,lookup,news_by_date):
    name="R4-S5 Donchian20/10 long-only"
    rows=[]; skips=0; forced=0
    i=0
    while i < len(daily)-1:
        s=daily.iloc[i]
        sig=(pd.notna(s["high20_prev"]) and float(s["close"])>float(s["high20_prev"]))
        if not sig:
            i+=1; continue
        eidx=i+1; e=daily.iloc[eidx]; entry_ts=e["open_ts"]
        if blocked_entry(entry_ts,news_by_date.get(e["date"])):
            skips+=1; i+=1; continue
        entry=float(e["open"])
        xidx=None
        for j in range(eidx,len(daily)-1):
            q=daily.iloc[j]
            if pd.notna(q["low10_prev"]) and float(q["close"])<float(q["low10_prev"]):
                xidx=j+1; break
        if xidx is None: xidx=len(daily)-1
        normal_ts=daily.iloc[xidx]["open_ts"] if xidx<len(daily)-1 else daily.iloc[xidx]["close_ts"]
        normal_px=float(daily.iloc[xidx]["open"] if xidx<len(daily)-1 else daily.iloc[xidx]["close"])
        dl=first_global_deadline_after(deadlines,entry_ts,normal_ts)
        if dl is not None:
            px,actual=price_at_or_after(dl,lookup)
            if px is not None:
                rows.append(record("R4",name,e["date"],1,entry,px,"NEWS",entry_ts,actual)); forced+=1
                exit_date=pd.Timestamp(actual).tz_convert("America/New_York").date().isoformat() if pd.Timestamp(actual).tzinfo else pd.Timestamp(actual).date().isoformat()
                m=daily.index[daily["date"]>=exit_date].tolist()
                i=(m[0] if m else xidx); continue
        rows.append(record("R4",name,e["date"],1,entry,normal_px,"DONCH_EXIT",entry_ts,normal_ts))
        i=xidx+1
    return rows,skips,forced


# -----------------------------
# Round 5 gaps
# -----------------------------

def static_path(g,start_idx,direction,entry,stop,target,nd,eod_idx=389):
    dls=deadlines_for_day(nd)
    for i in range(start_idx,min(eod_idx,len(g)-1)+1):
        b=g.iloc[i]; ts=b["bar_start_et"]
        if ts in dls:
            return float(b["open"]),i,"NEWS",ts
        if direction==1:
            if float(b["low"])<=stop:
                return (float(b["open"]) if float(b["open"])<stop else stop),i,"SL",ts
            if float(b["high"])>=target:
                return (float(b["open"]) if float(b["open"])>target else target),i,"TP",ts
        else:
            if float(b["high"])>=stop:
                return (float(b["open"]) if float(b["open"])>stop else stop),i,"SL",ts
            if float(b["low"])<=target:
                return (float(b["open"]) if float(b["open"])<target else target),i,"TP",ts
    b=g.iloc[min(eod_idx,len(g)-1)]
    return float(b["close"]),min(eod_idx,len(g)-1),"EOD",b["timestamp_et"]


def r5_gap_open(sessions,news):
    name="R5-S1 Gap fade open -> prior close"
    rows=[]; skips=0; forced=0
    dates=sorted(sessions)
    for j in range(1,len(dates)):
        d,prev=dates[j],dates[j-1]
        g=add_bar_start(sessions[d]); pg=add_bar_start(sessions[prev])
        prior_close=float(pg.iloc[-1]["close"])
        entry=float(g.iloc[0]["open"]); ts=g.iloc[0]["bar_start_et"]
        gap=entry-prior_close
        if abs(gap/prior_close)<0.001: continue
        nd=news.get(d)
        if blocked_entry(ts,nd): skips+=1; continue
        direction=-1 if gap>0 else 1
        target=prior_close
        stop=entry+gap if direction==-1 else entry+gap  # one gap-length further in gap direction
        # For gap down long, gap<0 => stop below entry. For gap up short, gap>0 => stop above.
        exit_px,_,reason,exit_ts=static_path(g,0,direction,entry,stop,target,nd,389)
        if reason=="NEWS": forced+=1
        rows.append(record("R5",name,d,direction,entry,exit_px,reason,ts,exit_ts))
    return rows,skips,forced


def r5_gap_5m(sessions,news):
    name="R5-S2 5m gap fill 0.05-0.20% SL12"
    rows=[]; skips=0; forced=0
    dates=sorted(sessions)
    for j in range(1,len(dates)):
        d,prev=dates[j],dates[j-1]
        g=add_bar_start(sessions[d]); pg=add_bar_start(sessions[prev])
        prior_close=float(pg.iloc[-1]["close"])
        op=float(g.iloc[0]["open"])
        gap=op-prior_close
        pct=abs(gap/prior_close)
        if pct<0.0005 or pct>0.0020: continue
        first5=g.iloc[:5]
        # If target filled in opening 5m, no trade.
        if float(first5["low"].min())<=prior_close<=float(first5["high"].max()):
            continue
        entry_idx=5
        if entry_idx>=len(g): continue
        ts=g.iloc[entry_idx]["bar_start_et"]
        nd=news.get(d)
        if blocked_entry(ts,nd): skips+=1; continue
        entry=float(g.iloc[entry_idx]["open"])
        direction=-1 if gap>0 else 1
        target=prior_close
        stop=entry-direction*12.0
        # Ensure target remains favorable from actual entry.
        if direction==1 and target<=entry: continue
        if direction==-1 and target>=entry: continue
        exit_px,_,reason,exit_ts=static_path(g,entry_idx,direction,entry,stop,target,nd,389)
        if reason=="NEWS": forced+=1
        rows.append(record("R5",name,d,direction,entry,exit_px,reason,ts,exit_ts))
    return rows,skips,forced



def _r5_channel_system(daily,sessions,deadlines,lookup,news_by_date,entry_n,exit_n,name,use_2n):
    rows=[]; skips=0; forced=0
    dates=sorted(set(daily["date"]).intersection(sessions.keys()))
    dmap={r["date"]:r for _,r in daily.iterrows()}
    pos=0; entry=None; entry_ts=None; stop=None
    last_checked=None
    for di,d in enumerate(dates):
        row=dmap[d]
        g=add_bar_start(sessions[d])
        nd=news_by_date.get(d); dls=deadlines_for_day(nd)

        # If holding overnight, a scheduled news deadline can flatten before RTH open.
        if pos!=0 and last_checked is not None:
            open_ts=g.iloc[0]["bar_start_et"]
            dl=first_global_deadline_after(deadlines,last_checked,open_ts)
            if dl is not None:
                px,actual=price_at_or_after(dl,lookup)
                if px is not None and pd.Timestamp(actual)<=open_ts:
                    rows.append(record("R5",name,d,pos,entry,px,"NEWS",entry_ts,actual))
                    pos=0; entry=None; stop=None; forced+=1

        upper=row.get(f"high{entry_n}_prev",np.nan)
        lower=row.get(f"low{entry_n}_prev",np.nan)
        exit_low=row.get(f"low{exit_n}_prev",np.nan)
        exit_high=row.get(f"high{exit_n}_prev",np.nan)
        nval=row.get("atr20_prev",np.nan)

        for i in range(len(g)):
            b=g.iloc[i]; ts=b["bar_start_et"]
            exited_this_bar=False

            if pos!=0 and ts in dls:
                rows.append(record("R5",name,d,pos,entry,float(b["open"]),"NEWS",entry_ts,ts))
                pos=0; entry=None; stop=None; forced+=1; exited_this_bar=True

            if pos!=0:
                if pos==1:
                    candidates=[]
                    if use_2n and stop is not None: candidates.append(float(stop))
                    if pd.notna(exit_low): candidates.append(float(exit_low))
                    if candidates:
                        eff=max(candidates)
                        if float(b["low"])<=eff:
                            fill=float(b["open"]) if float(b["open"])<eff else eff
                            rows.append(record("R5",name,d,1,entry,fill,"CHANNEL/SL",entry_ts,ts))
                            pos=0; entry=None; stop=None; exited_this_bar=True
                else:
                    candidates=[]
                    if use_2n and stop is not None: candidates.append(float(stop))
                    if pd.notna(exit_high): candidates.append(float(exit_high))
                    if candidates:
                        eff=min(candidates)
                        if float(b["high"])>=eff:
                            fill=float(b["open"]) if float(b["open"])>eff else eff
                            rows.append(record("R5",name,d,-1,entry,fill,"CHANNEL/SL",entry_ts,ts))
                            pos=0; entry=None; stop=None; exited_this_bar=True

            if pos==0 and not exited_this_bar and pd.notna(upper) and pd.notna(lower):
                hm=ts.hour*60+ts.minute
                if ENTRY_START<=hm<=ENTRY_END:
                    hit_l=float(b["high"])>=float(upper)
                    hit_s=float(b["low"])<=float(lower)
                    if hit_l and hit_s:
                        continue
                    if hit_l or hit_s:
                        if blocked_entry(ts,nd):
                            skips+=1; continue
                        direction=1 if hit_l else -1
                        level=float(upper) if direction==1 else float(lower)
                        fill=max(level,float(b["open"])) if direction==1 else min(level,float(b["open"]))
                        pos=direction; entry=fill; entry_ts=ts
                        if use_2n:
                            if pd.isna(nval) or float(nval)<=0:
                                pos=0; entry=None; entry_ts=None; continue
                            stop=entry-direction*2.0*float(nval)
                        else:
                            stop=None

        last_checked=g.iloc[-1]["timestamp_et"]

    if pos!=0:
        d=dates[-1]; g=add_bar_start(sessions[d]); last=g.iloc[-1]
        rows.append(record("R5",name,d,pos,entry,float(last["close"]),"DATA_END",entry_ts,last["timestamp_et"]))
    return rows,skips,forced


def r5_turtle_s1(daily,sessions,deadlines,lookup,news):
    return _r5_channel_system(
        daily,sessions,deadlines,lookup,news,
        20,10,"R5-S3 Turtle S1 20/10 + 2N",True)


def r5_turtle_s2(daily,sessions,deadlines,lookup,news):
    return _r5_channel_system(
        daily,sessions,deadlines,lookup,news,
        55,20,"R5-S4 Turtle S2 55/20 + 2N",True)


def r5_donchian20_20(daily,sessions,deadlines,lookup,news):
    return _r5_channel_system(
        daily,sessions,deadlines,lookup,news,
        20,20,"R5-S5 Donchian four-week 20/20",False)



# -----------------------------
# TradingView open-source strategies
# -----------------------------

def _continuous_rth(sessions):
    parts=[]
    for d,g0 in sessions.items():
        g=add_bar_start(g0)
        g["_datekey"]=d
        g["_row"]=range(len(g))
        parts.append(g)
    return pd.concat(parts,ignore_index=True).sort_values("timestamp_et").reset_index(drop=True)


def tv_bb_ema9(sessions,news):
    """TradingView D499 Bollinger Bands + EMA9, exposed long-only source."""
    name="R4-S4 TV-Bollinger20x2 + EMA9 long"
    x=_continuous_rth(sessions)
    x["ema9"]=x["close"].ewm(span=9,adjust=False).mean()
    mid=x["close"].rolling(20,min_periods=20).mean()
    sd=x["close"].rolling(20,min_periods=20).std(ddof=0)
    x["lower20"]=mid-2.0*sd
    # Exact exposed Pine condition: Long = close[1] < lower (current lower).
    x["long_signal"]=x["close"].shift(1) < x["lower20"]
    x["exit_signal"]=x["close"] >= x["ema9"]

    rows=[]; skips=0; forced=0
    for d,g0 in x.groupby("_datekey",sort=True):
        g=g0.reset_index(drop=True)
        nd=news.get(d); dls=deadlines_for_day(nd)
        pos=False; entry=None; entry_ts=None
        pending_entry=False; pending_exit=False
        for i in range(len(g)):
            b=g.iloc[i]; ts=b["bar_start_et"]
            if pos and ts in dls:
                rows.append(record("R4",name,d,1,entry,float(b["open"]),"NEWS",entry_ts,ts))
                pos=False; forced+=1
            if pending_exit:
                pending_exit=False
                if pos:
                    rows.append(record("R4",name,d,1,entry,float(b["open"]),"EMA9",entry_ts,ts))
                    pos=False
            if pending_entry:
                pending_entry=False
                hm=ts.hour*60+ts.minute
                if not pos and ENTRY_START<=hm<=ENTRY_END:
                    if blocked_entry(ts,nd):
                        skips+=1
                    else:
                        pos=True; entry=float(b["open"]); entry_ts=ts
            if i<len(g)-1:
                if pos and bool(b["exit_signal"]):
                    pending_exit=True
                elif (not pos) and bool(b["long_signal"]):
                    pending_entry=True
        if pos:
            last=g.iloc[-1]
            rows.append(record("R4",name,d,1,entry,float(last["close"]),"EOD",entry_ts,last["timestamp_et"]))
    return rows,skips,forced


def _supertrend_series(g,period=10,factor=3.0):
    high=g["high"].to_numpy(float)
    low=g["low"].to_numpy(float)
    close=g["close"].to_numpy(float)
    n=len(g)
    tr=np.full(n,np.nan)
    for i in range(n):
        if i==0:
            tr[i]=high[i]-low[i]
        else:
            tr[i]=max(high[i]-low[i],abs(high[i]-close[i-1]),abs(low[i]-close[i-1]))
    atr=pd.Series(tr).ewm(alpha=1/period,adjust=False,min_periods=period).mean().to_numpy()
    hl2=(high+low)/2.0
    bu=hl2+factor*atr
    bl=hl2-factor*atr
    fu=np.full(n,np.nan); fl=np.full(n,np.nan); st=np.full(n,np.nan); bull=np.full(n,False)
    for i in range(n):
        if not np.isfinite(atr[i]):
            continue
        if i==0 or not np.isfinite(fu[i-1]):
            fu[i]=bu[i]; fl[i]=bl[i]
            st[i]=fu[i]
            bull[i]=close[i]>st[i]
            continue
        fu[i]=bu[i] if (bu[i]<fu[i-1] or close[i-1]>fu[i-1]) else fu[i-1]
        fl[i]=bl[i] if (bl[i]>fl[i-1] or close[i-1]<fl[i-1]) else fl[i-1]
        if np.isclose(st[i-1],fu[i-1],equal_nan=False):
            st[i]=fu[i] if close[i]<=fu[i] else fl[i]
        else:
            st[i]=fl[i] if close[i]>=fl[i] else fu[i]
        bull[i]=close[i]>st[i]
    return st,bull


def tv_supertrend(sessions,news):
    """TradingView open-source SuperTrend L/S, defaults ATR10 factor3."""
    name="R4-S5 TV-SuperTrend10x3 L/S"
    rows=[]; skips=0; forced=0
    for d,g0 in sessions.items():
        g=add_bar_start(g0)
        st,bull=_supertrend_series(g,10,3.0)
        g=g.copy()
        g["st"]=st; g["bull"]=bull
        nd=news.get(d); dls=deadlines_for_day(nd)
        pos=0; entry=None; entry_ts=None; pending=0
        for i in range(len(g)):
            b=g.iloc[i]; ts=b["bar_start_et"]
            # Dynamic stop known from previous completed bar.
            if pos!=0 and ts in dls:
                rows.append(record("R4",name,d,pos,entry,float(b["open"]),"NEWS",entry_ts,ts))
                pos=0; forced+=1
            if pos!=0 and i>0 and np.isfinite(g.iloc[i-1]["st"]):
                stop=float(g.iloc[i-1]["st"])
                if pos==1 and stop< float(b["open"]) and float(b["low"])<=stop:
                    fill=float(b["open"]) if float(b["open"])<stop else stop
                    rows.append(record("R4",name,d,1,entry,fill,"SUPERSTOP",entry_ts,ts))
                    pos=0
                elif pos==-1 and stop>float(b["open"]) and float(b["high"])>=stop:
                    fill=float(b["open"]) if float(b["open"])>stop else stop
                    rows.append(record("R4",name,d,-1,entry,fill,"SUPERSTOP",entry_ts,ts))
                    pos=0
            if pending!=0:
                desired=pending; pending=0
                if pos!=0 and pos!=desired:
                    rows.append(record("R4",name,d,pos,entry,float(b["open"]),"FLIP",entry_ts,ts))
                    pos=0
                hm=ts.hour*60+ts.minute
                if pos==0 and ENTRY_START<=hm<=ENTRY_END:
                    if blocked_entry(ts,nd):
                        skips+=1
                    else:
                        pos=desired; entry=float(b["open"]); entry_ts=ts
            if i<len(g)-1 and i>0 and np.isfinite(g.iloc[i]["st"]) and np.isfinite(g.iloc[i-1]["st"]):
                now=bool(g.iloc[i]["bull"]); prev=bool(g.iloc[i-1]["bull"])
                if now and not prev: pending=1
                elif prev and not now: pending=-1
        if pos!=0:
            last=g.iloc[-1]
            rows.append(record("R4",name,d,pos,entry,float(last["close"]),"EOD",entry_ts,last["timestamp_et"]))
    return rows,skips,forced


def tv_rsi14_4060(sessions,news):
    """TradingView Free990 RSI14 40/60, TP5%, SL2%, frozen Both directions."""
    name="R5-S3 TV-RSI14 40/60 TP5 SL2"
    x=_continuous_rth(sessions)
    x["rsi14_tv"]=wilder_rsi(x["close"],14)
    x["cross_below40"]=(x["rsi14_tv"]<40)&(x["rsi14_tv"].shift(1)>=40)
    x["cross_above60"]=(x["rsi14_tv"]>60)&(x["rsi14_tv"].shift(1)<=60)
    rows=[]; skips=0; forced=0
    for d,g0 in x.groupby("_datekey",sort=True):
        g=g0.reset_index(drop=True)
        nd=news.get(d); dls=deadlines_for_day(nd)
        pos=0; entry=None; entry_ts=None; stop=None; target=None; pending=0
        for i in range(len(g)):
            b=g.iloc[i]; ts=b["bar_start_et"]
            if pos!=0 and ts in dls:
                rows.append(record("R5",name,d,pos,entry,float(b["open"]),"NEWS",entry_ts,ts))
                pos=0; forced+=1
            if pending!=0:
                desired=pending; pending=0
                if pos!=0 and pos!=desired:
                    rows.append(record("R5",name,d,pos,entry,float(b["open"]),"RSI_REVERSE",entry_ts,ts))
                    pos=0
                hm=ts.hour*60+ts.minute
                if pos==0 and ENTRY_START<=hm<=ENTRY_END:
                    if blocked_entry(ts,nd): skips+=1
                    else:
                        pos=desired; entry=float(b["open"]); entry_ts=ts
                        stop=entry*(1-0.02*pos)
                        target=entry*(1+0.05*pos)
            if pos!=0:
                if pos==1:
                    if float(b["low"])<=stop:
                        fill=float(b["open"]) if float(b["open"])<stop else stop
                        rows.append(record("R5",name,d,pos,entry,fill,"SL",entry_ts,ts)); pos=0
                    elif float(b["high"])>=target:
                        fill=float(b["open"]) if float(b["open"])>target else target
                        rows.append(record("R5",name,d,pos,entry,fill,"TP",entry_ts,ts)); pos=0
                else:
                    if float(b["high"])>=stop:
                        fill=float(b["open"]) if float(b["open"])>stop else stop
                        rows.append(record("R5",name,d,pos,entry,fill,"SL",entry_ts,ts)); pos=0
                    elif float(b["low"])<=target:
                        fill=float(b["open"]) if float(b["open"])<target else target
                        rows.append(record("R5",name,d,pos,entry,fill,"TP",entry_ts,ts)); pos=0
            if i<len(g)-1:
                if bool(b["cross_below40"]): pending=1
                elif bool(b["cross_above60"]): pending=-1
        if pos!=0:
            last=g.iloc[-1]
            rows.append(record("R5",name,d,pos,entry,float(last["close"]),"EOD",entry_ts,last["timestamp_et"]))
    return rows,skips,forced


def tv_ny_orb15_rr(sessions,news):
    """TradingView shui2967 NY ORB: close-confirmed breakout, stop other OR edge, TP 1.5x OR range."""
    name="R5-S1 TV-NY ORB15 fixed1.5xRange"
    rows=[]; skips=0; forced=0
    for d,g0 in sessions.items():
        g=add_bar_start(g0)
        if len(g)<20: continue
        orh=float(g.iloc[:15]["high"].max()); orl=float(g.iloc[:15]["low"].min())
        rr_range=orh-orl
        if rr_range<=0: continue
        nd=news.get(d); dls=deadlines_for_day(nd)
        long_used=False; short_used=False
        pos=0; entry=None; entry_ts=None; stop=None; target=None; pending=0
        for i in range(15,len(g)):
            b=g.iloc[i]; ts=b["bar_start_et"]
            if pos!=0 and ts in dls:
                rows.append(record("R5",name,d,pos,entry,float(b["open"]),"NEWS",entry_ts,ts))
                pos=0; forced+=1
            if pending!=0:
                desired=pending; pending=0
                hm=ts.hour*60+ts.minute
                used=(long_used if desired==1 else short_used)
                if pos==0 and not used and ENTRY_START<=hm<=ENTRY_END:
                    if blocked_entry(ts,nd): skips+=1
                    else:
                        pos=desired; entry=float(b["open"]); entry_ts=ts
                        stop=orl if pos==1 else orh
                        target=entry+pos*1.5*rr_range
                        if pos==1: long_used=True
                        else: short_used=True
            if pos!=0:
                if pos==1:
                    if float(b["low"])<=stop:
                        fill=float(b["open"]) if float(b["open"])<stop else stop
                        rows.append(record("R5",name,d,pos,entry,fill,"SL",entry_ts,ts)); pos=0
                    elif float(b["high"])>=target:
                        fill=float(b["open"]) if float(b["open"])>target else target
                        rows.append(record("R5",name,d,pos,entry,fill,"TP",entry_ts,ts)); pos=0
                else:
                    if float(b["high"])>=stop:
                        fill=float(b["open"]) if float(b["open"])>stop else stop
                        rows.append(record("R5",name,d,pos,entry,fill,"SL",entry_ts,ts)); pos=0
                    elif float(b["low"])<=target:
                        fill=float(b["open"]) if float(b["open"])<target else target
                        rows.append(record("R5",name,d,pos,entry,fill,"TP",entry_ts,ts)); pos=0
            if i<len(g)-1 and pos==0:
                if (not long_used) and float(b["close"])>orh:
                    pending=1
                elif (not short_used) and float(b["close"])<orl:
                    pending=-1
        if pos!=0:
            last=g.iloc[-1]
            rows.append(record("R5",name,d,pos,entry,float(last["close"]),"EOD",entry_ts,last["timestamp_et"]))
    return rows,skips,forced


def tv_orb15_2r(sessions,news):
    """TradingView Hardest_Easy_Money ORB15; source pip translated to one MES tick."""
    name="R5-S2 TV-ORB15 stop-order 2R"
    rows=[]; skips=0; forced=0
    for d,g0 in sessions.items():
        g=add_bar_start(g0)
        if len(g)<20: continue
        orh=float(g.iloc[:15]["high"].max()); orl=float(g.iloc[:15]["low"].min())
        long_level=orh+1*TICK
        short_level=orl-1*TICK
        long_stop=orl-2*TICK
        short_stop=orh+2*TICK
        nd=news.get(d)
        # Orders active for one hour after 09:45 => through 10:45 bar start.
        entry=None
        for i in range(15,len(g)):
            b=g.iloc[i]; ts=b["bar_start_et"]
            if ts.hour*60+ts.minute>10*60+45: break
            hit_l=float(b["high"])>=long_level
            hit_s=float(b["low"])<=short_level
            if hit_l and hit_s:
                entry=None
                break
            if not hit_l and not hit_s:
                continue
            direction=1 if hit_l else -1
            if blocked_entry(ts,nd):
                skips+=1
                continue
            level=long_level if direction==1 else short_level
            fill=max(level,float(b["open"])) if direction==1 else min(level,float(b["open"]))
            entry=(i,direction,fill,ts)
            break
        if entry is None: continue
        idx,direction,fill,ts=entry
        stop=long_stop if direction==1 else short_stop
        risk=abs(fill-stop)
        if risk<=0: continue
        target=fill+direction*2.0*risk
        exit_px,_,reason,exit_ts=static_path(g,idx,direction,fill,stop,target,nd,389)
        if reason=="NEWS": forced+=1
        rows.append(record("R5",name,d,direction,fill,exit_px,reason,ts,exit_ts))
    return rows,skips,forced



# -----------------------------
# Main
# -----------------------------

def main():
    if not NEWS_PATH.exists():
        raise RuntimeError("Missing Forex Factory calendar")
    _,news_by_date,deadlines=load_news()
    full=ext.stitch_mes()
    full=add_bar_start(full)
    lookup=full_price_lookup(full)
    base_sessions=ext.rth_sessions(full.drop(columns=["bar_start_et"]))
    sessions=enrich_1m(base_sessions)
    bars5=aggregate_5m(base_sessions)
    bars30=aggregate_30m(base_sessions)
    daily=daily_table(base_sessions)
    print("RTH sessions:",len(sessions),"daily rows:",len(daily),"30m bars:",len(bars30))

    specs=[
        # 15 NinjaTrader / NinjaTrader Forum strategies
        ("R1","R1-S1 SampleMACrossOver 10/25",r1_sample_ma,(sessions,news_by_date)),
        ("R1","R1-S2 SamplePriceModification 20/100 BE50",r1_sample_price_mod,(sessions,news_by_date)),
        ("R1","R1-S3 SMA5/30 lookback2 PT1",r1_sma530_pt1,(sessions,news_by_date)),
        ("R1","R1-S4 EMA20/40 + RSI14s3 PT200 dynEMA40",r1_ema_rsi_dynamic,(sessions,news_by_date)),
        ("R1","R1-S5 Basic Donchian20 long",r1_donchian20,(sessions,news_by_date)),

        ("R2","R2-S1 Contrarian MACD 10/10",r2_macd_contrarian,(sessions,news_by_date)),
        ("R2","R2-S2 MFI14+MACD 5m long",r2_mfi_macd,(base_sessions,bars5,news_by_date)),
        ("R2","R2-S3 InsideBar directional close SL10 PT25",r2_inside_directional,(sessions,news_by_date)),
        ("R2","R2-S4 InsideBar structural bracket",r2_inside_structural,(sessions,news_by_date)),
        ("R2","R2-S5 Bollinger100 1.5dev short $2500/$5000",r2_boll100_fade,(sessions,news_by_date)),

        ("R3","R3-S1 VWAP lower2 10-12pt mean reversion",r3_vwap2,(base_sessions,news_by_date)),
        ("R3","R3-S2 Bollinger(2,14) lower-to-upper long",r3_bollinger,(sessions,news_by_date)),
        ("R3","R3-S3 PriorClose cross PT25",r3_prior_close_pt25,(base_sessions,news_by_date)),
        ("R3","R3-S4 PriorHighLow breakout signalbar stop",r3_prior_hilo_breakout,(base_sessions,news_by_date)),
        ("R3","R3-S5 PriorClose cross short SL100 PT200",r3_prior_close_short_100_200,(base_sessions,news_by_date)),

        # 5 TradingView open-source strategies + 5 other published systems
        ("R4","R4-S1 Connors RSI2<5 / SMA200",simulate_daily_connors,(daily,deadlines,lookup,news_by_date,"rsi2")),
        ("R4","R4-S2 Connors Double7",simulate_daily_connors,(daily,deadlines,lookup,news_by_date,"double7")),
        ("R4","R4-S3 Larry Williams Oops FPO",r4_oops_fpo,(base_sessions,full,news_by_date,deadlines)),
        ("R4","R4-S4 TV-Bollinger20x2 + EMA9 long",tv_bb_ema9,(base_sessions,news_by_date)),
        ("R4","R4-S5 TV-SuperTrend10x3 L/S",tv_supertrend,(base_sessions,news_by_date)),

        ("R5","R5-S1 TV-NY ORB15 fixed1.5xRange",tv_ny_orb15_rr,(base_sessions,news_by_date)),
        ("R5","R5-S2 TV-ORB15 stop-order 2R",tv_orb15_2r,(base_sessions,news_by_date)),
        ("R5","R5-S3 TV-RSI14 40/60 TP5 SL2",tv_rsi14_4060,(base_sessions,news_by_date)),
        ("R5","R5-S4 Gap fade open -> prior close",r5_gap_open,(base_sessions,news_by_date)),
        ("R5","R5-S5 Turtle S1 20/10 + 2N",r5_turtle_s1,(daily,base_sessions,deadlines,lookup,news_by_date)),
    ]

    assert len(specs)==25
    allrows=[]; meta=[]
    for rid,name,fn,args in specs:
        print("RUN",rid,name)
        rows,skips,forced=fn(*args)
        allrows.extend(rows)
        family=("NinjaTrader" if rid in {"R1","R2","R3"} else ("TradingView" if "TV-" in name else "External"))
        meta.append((rid,name,family,skips,forced))

    trades=pd.DataFrame(allrows)
    summaries=[]
    for rid,name,family,skips,forced in meta:
        if len(trades):
            g=trades[(trades["round"]==rid)&(trades["strategy"]==name)].copy()
        else:
            g=pd.DataFrame()
        m=metrics(g)
        summaries.append(dict(round=rid,source_family=family,strategy=name,news_entry_skips=skips,
                              forced_news_exits=forced,**m,
                              passes_primary_gate=gate(m)))
    summary=pd.DataFrame(summaries)

    out=Path("results/five_external_rounds")
    out.mkdir(parents=True,exist_ok=True)
    trades.to_csv(out/"trades.csv",index=False)
    summary.to_csv(out/"summary.csv",index=False)

    print("\n=== FIVE ROUNDS x FIVE EXTERNAL STRATEGIES ===")
    cols=["round","source_family","strategy","trades","trades_per_month","net_pts_trade","pf_net","win_rate",
          "total_net","max_dd_points","positive_years","max_positive_year_share",
          "news_entry_skips","forced_news_exits","passes_primary_gate"]
    for col in cols:
        if col not in summary.columns: summary[col]=np.nan
    print(summary[cols].round(4).to_string(index=False))
    print("\n=== YEARLY ===")
    for _,r in summary.iterrows():
        print(r["round"],r["strategy"],"::",r.get("yearly",""))
    for rid in ["R1","R2","R3","R4","R5"]:
        z=summary[summary["round"]==rid]
        print("\n",rid,"PASSED:",z.loc[z.passes_primary_gate==True,"strategy"].tolist())

if __name__=="__main__":
    main()

# PR trigger only; 25-strategy preregistered logic unchanged
