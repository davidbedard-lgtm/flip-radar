"""Flip Radar board scorers — formulas moved verbatim from playbook prose (v10)."""

def score_flip(items, mile_rate=0.70, wage=18.0):
    """FLIP v2: EV-weighted margin + liquidity + freshness + effort, plus labor fields."""
    def load_min(it):
        h=it["haul"]; s=it["size"].lower()
        return 60 if h>=8 else 40 if (h>=5 or "helper" in s or "2-person" in s) else 25 if h>=3 else 10 if "car" in s else 15
    for it in items:
        mid=(it["lo"]+it["hi"])/2; drive=round(2*it["miles"]*mile_rate,2); nl=round(mid*0.95-drive); d=it["posted_days"]
        p=0.85 if d<=1 else 0.70 if d<=3 else 0.50 if d<=7 else 0.30 if d<=21 else 0.12 if d<=45 else 0.08
        ev=max(0,nl)*p
        crew=2 if (it["haul"]>=5 or "helper" in it["size"].lower() or "2-person" in it["size"].lower() or "2 people" in it["cond"].lower()) else 1
        tmin=round(it["miles"]*2*2.3+load_min(it)+15); lcost=round(tmin/60*wage*crew)
        it.update(resale_mid=round(mid),drive_cost=round(drive),net_list=nl,
            net_quick=(round(it["quick"]-drive) if it.get("quick") else None),p_avail=p,ev_net=round(ev),
            score=round(min(45,ev/150*45)+it["liq"]+(20 if d<=1 else 16 if d<=3 else 12 if d<=7 else 6 if d<=21 else 2)+max(0,15-it["miles"]*0.15-it["haul"])),
            time_min=tmin,crew=crew,labor_cost=lcost,net_labor=nl-lcost,
            crew_hr=round(nl/(tmin/60*crew)) if tmin>0 else 0,labor_ok=(nl-lcost)>=20)
    items.sort(key=lambda x:-x["score"])
    return items

def score_haul(leads, disposal, mile_rate=0.70, wage=18.0, floor_cash_crew_hr=40, flip_items=None):
    """HAUL v1.1 (2026-07-28 corrections):
    cash_net = quote - disposal - drive - labor            (money in hand)
    cash_crew_hr = cash_net / crew-hours                   <- PRIMARY SORT + $40 floor
    total_net = cash_net + recovery ; total_crew_hr = upside column
    Derived leads: ev = total_net x p_win(0.35) x p_avail(source flip item) — compounded odds.
    Floor fail + recovery>0  => KEPT, flagged 'recovery-carried' (honest label), not filtered.
    p_win < 0.15 recruitment posts => 'relationships' bucket (applications, not leads).
    ev_hub excludes derived recovery so hub totals never double-count a FLIP object."""
    flip_by_url = {i["url"]: i for i in (flip_items or [])}
    kept, filtered, relationships = [], [], []
    for L in leads:
        vol = L.get("loads", 1.0)
        if "quote_lo" not in L:
            base = {0.25:(100,140),0.5:(200,250),1.0:(300,380),1.5:(420,520),2.0:(520,650)}
            lo,hi = base.get(vol,(300,380))
            if L.get("single_item"): lo,hi = 75,125
            L["quote_lo"],L["quote_hi"]=lo,hi
        q=(L["quote_lo"]+L["quote_hi"])/2
        tons=L.get("tons", vol*0.6)
        disp=round(tons*disposal["msw_per_ton"] + sum(disposal["surcharges"].get(x,0) for x in L.get("surcharge_items",[]) if isinstance(disposal["surcharges"].get(x,0),(int,float))))
        L["disposal_cost"]=disp - round(L.get("recovery_diverts_disposal",0)*disp)
        drive=round(2*L["miles"]*mile_rate + L.get("dump_extra_mi",8)*2*mile_rate)
        crew=L.get("crew", 2 if vol>=0.5 else 1)
        onsite=L.get("onsite_min", round(45+60*max(0,vol-0.5)))
        tmin=round(L["miles"]*2*2.3 + L.get("dump_extra_mi",8)*2*2.3 + onsite + 30 + 15)
        lab=round(tmin/60*wage*crew)
        rec=L.get("recovery_est",0)
        crew_hours = tmin/60*crew
        cash_net = round(q - L["disposal_cost"] - drive - lab)
        total_net = cash_net + rec
        cash_chr = round(cash_net/crew_hours) if crew_hours>0 else 0
        total_chr = round(total_net/crew_hours) if crew_hours>0 else 0
        h=L.get("age_hours",72)
        p_win = 0.70 if h<=6 else 0.45 if h<=24 else 0.20 if h<=72 else 0.08
        p_avail = 1.0
        if L.get("derived"):
            p_win = 0.35
            src = flip_by_url.get(L["url"])
            p_avail = src["p_avail"] if src else 0.30
        ev = round(max(0,total_net) * p_win * p_avail)
        ev_hub = round(max(0,cash_net) * p_win * p_avail) if L.get("derived") else ev
        fresh = 20 if h<=6 else 14 if h<=24 else 8 if h<=72 else 3
        rec_bonus = 8 if any(k in (L.get("cond","")+L.get("title","")).lower() for k in ("property","realtor","estate","landlord","rental","tenant","recurring","monthly")) else 0
        score=round(min(45,max(0,cash_chr)/150*45)+min(25,ev/400*25)+fresh+max(0,10-L["miles"]*0.25)+rec_bonus)
        L.update(quote_mid=round(q),drive_cost=drive,labor_cost=lab,recovery_est=rec,
                 cash_net=cash_net,net=total_net,crew=crew,time_min=tmin,
                 cash_crew_hr=cash_chr,crew_hr=total_chr,p_win=p_win,p_avail_src=p_avail,
                 ev=ev,ev_hub=ev_hub,score=min(100,score))
        if rec_bonus and "recurring potential" not in L.get("flags",[]): L["flags"]=L.get("flags",[])+["recurring potential"]
        if p_win < 0.15 and not L.get("derived") and ("recruitment" in " ".join(L.get("flags",[])) or "recurring" in " ".join(L.get("flags",[]))):
            relationships.append(L); continue
        if cash_chr >= floor_cash_crew_hr:
            kept.append(L)
        elif rec > 0:
            L["flags"]=L.get("flags",[])+["recovery-carried — fee does not clear $40/crew-hr floor"]
            kept.append(L)
        else:
            filtered.append(L)
    kept.sort(key=lambda x:-x["cash_crew_hr"])
    return kept, filtered, relationships
