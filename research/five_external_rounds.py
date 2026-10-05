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
    daily=daily_table(base_sessions)
    print("RTH sessions:",len(sessions),"daily rows:",len(daily))

    specs=[
        ("R1",r1_sample_ma,(sessions,news_by_date)),
        ("R1",r1_sample_price_mod,(sessions,news_by_date)),
        ("R2",r2_macd_contrarian,(sessions,news_by_date)),
        ("R2",r2_mfi_macd,(base_sessions,bars5,news_by_date)),
        ("R3",r3_vwap2,(base_sessions,news_by_date)),
        ("R3",r3_bollinger,(sessions,news_by_date)),
        ("R4",simulate_daily_connors,(daily,deadlines,lookup,news_by_date,"rsi2")),
        ("R4",simulate_daily_connors,(daily,deadlines,lookup,news_by_date,"double7")),
        ("R5",r5_gap_open,(base_sessions,news_by_date)),
        ("R5",r5_gap_5m,(base_sessions,news_by_date)),
    ]

    allrows=[]; meta=[]
    for rid,fn,args in specs:
        rows,skips,forced=fn(*args)
        allrows.extend(rows)
        name=rows[0]["strategy"] if rows else fn.__name__ + ("_"+str(args[-1]) if fn is simulate_daily_connors else "")
        meta.append((rid,name,skips,forced))

    trades=pd.DataFrame(allrows)
    summaries=[]
    for rid,name,skips,forced in meta:
        g=trades[(trades["round"]==rid)&(trades["strategy"]==name)].copy() if len(trades) else pd.DataFrame()
        m=metrics(g)
        summaries.append(dict(round=rid,strategy=name,news_entry_skips=skips,
                              forced_news_exits=forced,**m,
                              passes_primary_gate=gate(m)))
    summary=pd.DataFrame(summaries)

    out=Path("results/five_external_rounds")
    out.mkdir(parents=True,exist_ok=True)
    trades.to_csv(out/"trades.csv",index=False)
    summary.to_csv(out/"summary.csv",index=False)

    print("\n=== FIVE EXTERNAL STRATEGY ROUNDS ===")
    cols=["round","strategy","trades","trades_per_month","net_pts_trade","pf_net","win_rate",
          "total_net","max_dd_points","positive_years","max_positive_year_share",
          "news_entry_skips","forced_news_exits","passes_primary_gate"]
    print(summary[cols].round(4).to_string(index=False))
    print("\n=== YEARLY ===")
    for _,r in summary.iterrows():
        print(r["round"],r["strategy"],"::",r.get("yearly",""))
    for rid in sorted(summary["round"].unique()):
        z=summary[summary["round"]==rid]
        print("\n",rid,"PASSED:",z.loc[z.passes_primary_gate,"strategy"].tolist())

if __name__=="__main__":
    main()
