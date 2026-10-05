from __future__ import annotations

from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import csv, re, time, json
import requests
from bs4 import BeautifulSoup

START_YEAR=2020
END_YEAR=2024
MONTHS=["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]
HEADERS={
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language":"en-US,en;q=0.9",
}
COOKIES={"fftimezone":"Etc/GMT","fftimeformat":"1"}
IMPACT_COLOR_MAP={"red":"High","ora":"Medium","yel":"Low","gry":"Holiday"}
IMPACT_LEVEL_MAP={"high":"High","medium":"Medium","low":"Low","none":"Holiday"}

def clean(x):
    return " ".join(x.split()) if x else ""

def parse_impact(tr):
    cell=tr.select_one("td.calendar__impact")
    if not cell: return ""
    icon=cell.select_one("[title]")
    if icon and icon.get("title"):
        t=icon["title"].replace("Impact Expected","").strip()
        if t.startswith("Med "): return "Medium"
        if t.startswith("High"): return "High"
        if t.startswith("Low"): return "Low"
        if t: return t
    classes=set(cell.get("class",[]))
    for el in cell.select("[class]"):
        classes.update(el.get("class",[]))
    s=" ".join(classes).lower()
    for k,v in IMPACT_COLOR_MAP.items():
        if f"impact-{k}" in s: return v
    for k,v in IMPACT_LEVEL_MAP.items():
        if f"--{k}" in s: return v
    return ""

def fetch_month(year, mon):
    url=f"https://www.forexfactory.com/calendar?month={mon}.{year}"
    r=requests.get(url,headers=HEADERS,cookies=COOKIES,timeout=45)
    r.raise_for_status()
    return url,r.text

def parse_month(html, nominal_year, nominal_month_idx):
    soup=BeautifulSoup(html,"html.parser")
    table=soup.select_one("table.calendar__table")
    if not table:
        raise RuntimeError("Calendar table not found")
    current_date=""
    current_time=""
    current_year=nominal_year
    out=[]
    for tr in table.select("tr.calendar__row"):
        event_cell=tr.select_one("td.calendar__event")
        if not event_cell: continue
        date_cell=tr.select_one("td.calendar__date")
        if date_cell:
            d=clean(date_cell.get_text(" "))
            if d:
                m=re.search(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b",d,re.I)
                if m:
                    idx=MONTHS.index(m.group(1).lower())+1
                    # Monthly views can show adjacent-month days.
                    # Infer year relative to the requested month, not row order.
                    if nominal_month_idx == 1 and idx == 12:
                        row_year = nominal_year - 1
                    elif nominal_month_idx == 12 and idx == 1:
                        row_year = nominal_year + 1
                    else:
                        row_year = nominal_year
                else:
                    row_year = nominal_year
                current_date=f"{d} {row_year}"
        time_cell=tr.select_one("td.calendar__time")
        if time_cell:
            t=clean(time_cell.get_text(" "))
            if t: current_time=t
        def cell(sel):
            el=tr.select_one(sel)
            return clean(el.get_text(" ")) if el else ""
        out.append({
            "date_raw":current_date,
            "time_raw":current_time,
            "currency":cell("td.calendar__currency"),
            "impact":parse_impact(tr),
            "event":clean(event_cell.get_text(" ")),
        })
    return out

def parse_dt(date_raw,time_raw):
    # Examples: Thu Jan 2 2024 / 13:30. Skip All Day/Tentative/blank.
    if not date_raw or not time_raw: return None
    t=time_raw.strip().lower()
    if "all day" in t or "tentative" in t or "day " in t: return None
    t=t.replace("am"," AM").replace("pm"," PM")
    for fmt in ("%a %b %d %Y %H:%M","%a %b %d %Y %I:%M %p"):
        try:
            dt=datetime.strptime(date_raw+" "+t,fmt)
            return dt.replace(tzinfo=ZoneInfo("UTC"))
        except ValueError:
            pass
    return None

def main():
    raw=[]
    for y in range(START_YEAR,END_YEAR+1):
        for mon in MONTHS:
            url,html=fetch_month(y,mon)
            rows=parse_month(html,y,MONTHS.index(mon)+1)
            print(y,mon,"rows",len(rows))
            for r in rows:
                r["source_url"]=url
                raw.append(r)
            time.sleep(2.1)

    keep=[]
    skipped=[]
    for r in raw:
        if r["currency"]!="USD" or r["impact"] not in {"High","Medium"}:
            continue
        dt_utc=parse_dt(r["date_raw"],r["time_raw"])
        if dt_utc is None:
            skipped.append(r)
            continue
        dt_et=dt_utc.astimezone(ZoneInfo("America/New_York"))
        if not (START_YEAR <= dt_et.year <= END_YEAR): continue
        keep.append({
            "event_utc":dt_utc.isoformat(),
            "event_et":dt_et.isoformat(),
            "date_et":dt_et.date().isoformat(),
            "time_et":dt_et.strftime("%H:%M:%S"),
            "currency":r["currency"],
            "impact":r["impact"],
            "event":r["event"],
            "blackout_start_et":(dt_et-pd.Timedelta(minutes=5)).isoformat(),
            "blackout_end_et":(dt_et+pd.Timedelta(minutes=5)).isoformat(),
            "source_url":r["source_url"],
        })

    # de-duplicate monthly overlaps and repeated rows
    uniq={}
    for r in keep:
        key=(r["event_utc"],r["currency"],r["impact"],r["event"])
        uniq[key]=r
    keep=sorted(uniq.values(),key=lambda r:(r["event_utc"],r["event"]))
    out=Path("data_external/forexfactory")
    out.mkdir(parents=True,exist_ok=True)
    fields=list(keep[0]) if keep else ["event_utc"]
    with (out/"usd_high_medium_2020_2024.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(keep)
    with (out/"unscheduled_usd_high_medium_2020_2024.json").open("w",encoding="utf-8") as f:
        json.dump(skipped,f,ensure_ascii=False,indent=2)

    from collections import Counter
    by_year=Counter(r["date_et"][:4] for r in keep)
    by_impact=Counter(r["impact"] for r in keep)
    audit={
        "source":"Forex Factory",
        "timezone_scraped":"UTC/GMT via fftimezone cookie",
        "timezone_output":"America/New_York",
        "rule":"USD High/Medium; flat at T-5; no new entries T-5 through T+5",
        "scheduled_events":len(keep),
        "unscheduled_skipped":len(skipped),
        "by_year":dict(sorted(by_year.items())),
        "by_impact":dict(by_impact),
    }
    (out/"AUDIT.json").write_text(json.dumps(audit,indent=2),encoding="utf-8")
    print(json.dumps(audit,indent=2))
    print("FIRST 10")
    for r in keep[:10]: print(r["event_et"],r["impact"],r["event"])

if __name__=="__main__":
    import pandas as pd
    main()
