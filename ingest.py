#!/usr/bin/env python3
"""Radar outcomes ingest — Run Log + Sale Log (Google Sheet CSV/paste) -> outcomes.json.
Match: item ID first, title words second. IDs are immutable; unknown IDs warn, never renumber.
PRIVACY: writes LOCAL outcomes.json only (project-synced by the session); never touches git.
Usage: python3 ingest.py <csv-file> [--log run|sale|auto] [--outcomes outcomes.json] [--state state_flip.json]"""
import csv, json, sys, statistics, datetime, io, re

def norm(h): return re.sub(r"[^a-z0-9]","",h.lower())
RUN_MAP = {"timestamp":"timestamp","driver":"driver","itemid":"id","item":"id","outcome":"outcome",
 "arrived":"arrived","loadedandleft":"departed","left":"departed","departed":"departed",
 "amountpaid":"ask_paid","paid":"ask_paid","conditionvslisting":"condition_vs_listing",
 "helperneeded":"helper_needed","photos":"photos","notes":"notes"}
SALE_MAP = {"itemid":"id","item":"id","listedprice":"listed_price","soldprice":"sold_price",
 "solddate":"sold_date","listeddate":"listed_date","channel":"channel","minutestolist":"minutes_to_list",
 "relists":"relists","notes":"sale_notes","title":"title"}

def to_min(a,b):
    try:
        fmt="%H:%M"; t1=datetime.datetime.strptime(a.strip(),fmt); t2=datetime.datetime.strptime(b.strip(),fmt)
        return int((t2-t1).total_seconds()//60)
    except Exception: return None

def money(v):
    try: return float(re.sub(r"[^0-9.\-]","",str(v))) if str(v).strip() not in ("","-") else None
    except Exception: return None

def ingest(path, log="auto", outcomes_path="outcomes.json", state_path="state_flip.json"):
    rows=list(csv.DictReader(io.StringIO(open(path).read())))
    try: outcomes=json.load(open(outcomes_path))
    except Exception: outcomes=[]
    try: st=json.load(open(state_path)); items={i["id"]:i for i in st["items"]}
    except Exception: items={}
    by_id={o["id"]:o for o in outcomes}
    n_new=n_upd=0; warns=[]
    for raw in rows:
        r={}; is_sale = log=="sale"
        for k,v in raw.items():
            nk=norm(k or "")
            if log=="auto" and nk in ("soldprice","listedprice"): is_sale=True
            m=(SALE_MAP if (log=="sale") else RUN_MAP).get(nk)
            if log=="auto":
                m = RUN_MAP.get(nk) or SALE_MAP.get(nk)
            if m and str(v).strip()!="": r[m]=str(v).strip()
        iid=r.get("id","").strip()
        if iid and iid not in items and iid not in by_id:
            # title-word fallback
            tw=set(re.findall(r"[a-z0-9]+", (r.get("title") or iid).lower()))
            best=None
            for i in items.values():
                sc=len(tw & set(re.findall(r"[a-z0-9]+", i["title"].lower())))
                if sc>=2 and (best is None or sc>best[0]): best=(sc,i["id"])
            if best: warns.append(f"'{iid}' matched by title -> {best[1]}"); iid=best[1]
            else: warns.append(f"UNKNOWN id '{iid}' — kept verbatim (never renumbered)")
        if not iid: warns.append("row skipped: no item id"); continue
        src=items.get(iid,{})
        o=by_id.get(iid)
        if not o:
            o=dict(id=iid, board="flip", title=src.get("title", r.get("title", iid)), category=src.get("cat"),
                   source=src.get("source"), acquired_date=None, ask_paid=None, drive_miles=src.get("miles"),
                   crew_size=src.get("run",{}).get("crew", src.get("crew")), repair_cost=None, listed_price=None,
                   sold_price=None, sold_date=None, days_to_sell=None, channel=None, notes=None,
                   driver=None, outcome=None, arrived=None, departed=None, onsite_min=None,
                   condition_vs_listing=None, helper_needed=None, minutes_to_list=None, relists=None, no_shows=0,
                   est_resale_mid=src.get("resale_mid"))
            outcomes.append(o); by_id[iid]=o; n_new+=1
        else: n_upd+=1
        for k in ("driver","outcome","arrived","departed","condition_vs_listing","notes","channel","sold_date","title"):
            if r.get(k): o[k if k!="title" else "title"]=r[k]
        if r.get("timestamp") and not o.get("acquired_date"): o["acquired_date"]=r["timestamp"].split(" ")[0]
        if r.get("ask_paid") is not None and money(r.get("ask_paid")) is not None: o["ask_paid"]=money(r["ask_paid"])
        for k in ("listed_price","sold_price"):
            if r.get(k): o[k]=money(r[k])
        for k in ("minutes_to_list","relists"):
            if r.get(k):
                try: o[k]=int(float(r[k]))
                except Exception: pass
        if r.get("helper_needed"): o["helper_needed"]=r["helper_needed"].lower() in ("yes","true","1","y")
        if r.get("sale_notes"): o["notes"]=((o.get("notes") or "")+" | sale: "+r["sale_notes"]).strip(" |")
        if o.get("arrived") and o.get("departed"): o["onsite_min"]=to_min(o["arrived"],o["departed"])
        if (o.get("outcome") or "").upper().replace(" ","") in ("ITEMGONE","GONE","NOSHOW"): o["no_shows"]=(o.get("no_shows") or 0)+0 if o.get("outcome_counted") else (o.get("no_shows") or 0)+1; o["outcome_counted"]=True
        if o.get("sold_date") and o.get("acquired_date"):
            try:
                d1=datetime.date.fromisoformat(o["acquired_date"][:10]); d2=datetime.date.fromisoformat(o["sold_date"][:10])
                o["days_to_sell"]=(d2-d1).days
            except Exception: pass
    json.dump(outcomes, open(outcomes_path,"w"), indent=1)

    # ---- measurement: replace guesses once 5 stops have times ----
    timed=[o for o in outcomes if o.get("onsite_min") is not None]
    stops=[o for o in outcomes if o.get("outcome")]
    gone=[o for o in stops if (o.get("outcome") or "").upper().replace(" ","") in ("ITEMGONE","GONE","NOSHOW")]
    cal={}
    if len(timed)>=5:
        by_crew={}
        for o in timed: by_crew.setdefault(o.get("crew_size") or 1,[]).append(o["onsite_min"])
        cal["measured_onsite_min"]={str(k):round(statistics.median(v)) for k,v in by_crew.items()}
        cal["n_timed"]=len(timed); cal["provisional_load_min_table"]="10 car / 15 base / 25 truck / 40 two-person / 60 extreme"
    if stops:
        cal["stale_rate"]=round(len(gone)/len(stops),2); cal["n_stops"]=len(stops); cal["n_gone"]=len(gone)
    if cal:
        try:
            c=json.load(open("config.json")); c.setdefault("time_calibration",{}).update(cal)
            json.dump(c,open("config.json","w"),indent=1)
        except Exception: pass
    msg=f"Ingested {len(rows)} rows -> {n_new} new, {n_upd} updated records ({len(outcomes)} total in ledger)"
    if warns: msg+=" | "+"; ".join(warns[:3])
    if len(timed)>=5: msg+=f" | MEASURED onsite medians now active: {cal['measured_onsite_min']} (n={len(timed)})"
    if stops: msg+=f" | stale-at-door rate: {cal['stale_rate']:.0%} of {len(stops)} confirmed stops"
    print(msg)
    return outcomes

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument("csv"); ap.add_argument("--log",default="auto")
    ap.add_argument("--outcomes",default="outcomes.json"); ap.add_argument("--state",default="state_flip.json")
    a=ap.parse_args(); ingest(a.csv, a.log, a.outcomes, a.state)
