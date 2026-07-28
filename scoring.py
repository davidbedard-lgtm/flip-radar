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

def score_haul(leads, disposal, mile_rate=0.70, wage=18.0, floor_crew_hr=40):
    """HAUL v1: net = quote - disposal - drive - labor + recovery; $/crew-hr is king.
    Weights: crew_hr 45 (cap $150) | ev 25 (cap $400) | freshness 20 | proximity 10 | +8 recurring bonus."""
    kept, filtered = [], []
    for L in leads:
        vol = L.get("loads", 1.0)
        if "quote_lo" not in L:
            base = {0.25:(100,140),0.5:(200,250),1.0:(300,380),1.5:(420,520),2.0:(520,650)}
            lo,hi = base.get(vol,(300,380))
            if L.get("single_item"): lo,hi = 75,125
            L["quote_lo"],L["quote_hi"]=lo,hi
        q=(L["quote_lo"]+L["quote_hi"])/2
        tons=L.get("tons", vol*0.6)
        disp=round(tons*disposal["msw_per_ton"] + sum(disposal["surcharges"].get(s,0) for s in L.get("surcharge_items",[]) if isinstance(disposal["surcharges"].get(s,0),(int,float))))
        L["disposal_cost"]=disp - round(L.get("recovery_diverts_disposal",0)*disp)  # resellable/donatable share skips the tip fee
        drive=round(2*L["miles"]*mile_rate + L.get("dump_extra_mi",8)*2*mile_rate)  # job RT + dump leg
        crew=L.get("crew", 2 if vol>=0.5 else 1)
        onsite=L.get("onsite_min", round(45+60*max(0,vol-0.5)))
        tmin=round(L["miles"]*2*2.3 + L.get("dump_extra_mi",8)*2*2.3 + onsite + 30 + 15)  # drive + dump + load + tip + admin
        lab=round(tmin/60*wage*crew)
        rec=L.get("recovery_est",0)
        net=round(q - L["disposal_cost"] - drive - lab + rec)
        chr_=round(net/(tmin/60*crew)) if tmin>0 else 0
        h=L.get("age_hours",72)
        p = 0.70 if h<=6 else 0.45 if h<=24 else 0.20 if h<=72 else 0.08
        if L.get("derived"): p = 0.35  # cold-pitch odds — poster didn't ask for paid help
        ev=round(max(0,net)*p)
        fresh = 20 if h<=6 else 14 if h<=24 else 8 if h<=72 else 3
        rec_bonus = 8 if any(k in (L.get("cond","")+L.get("title","")).lower() for k in ("property","realtor","estate","landlord","rental","tenant","recurring","monthly")) else 0
        score=round(min(45,max(0,chr_)/150*45)+min(25,ev/400*25)+fresh+max(0,10-L["miles"]*0.25)+rec_bonus)
        L.update(quote_mid=round(q),drive_cost=drive,labor_cost=lab,recovery_est=rec,net=net,crew=crew,
                 time_min=tmin,crew_hr=chr_,p_win=p,ev=ev,score=min(100,score))
        if rec_bonus: L["flags"]=L.get("flags",[])+["recurring potential"]
        (kept if chr_>=floor_crew_hr else filtered).append(L)
    kept.sort(key=lambda x:-x["score"])
    return kept, filtered
