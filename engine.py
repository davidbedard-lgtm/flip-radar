import re
import json as _json

import math as _m
def build_map(st):
    items=[i for i in st["items"] if "lat" in i]
    H=st["home"]; R=st.get("route",{}); legs=R.get("legs",[])
    onroute={l["id"]:n+1 for n,l in enumerate(legs)}
    latmin,latmax,lonmin,lonmax=37.195,37.795,-77.73,-77.27
    K=1050; CY=_m.cos(_m.radians(37.5)); PAD=26
    W=int((lonmax-lonmin)*CY*K)+2*PAD; Hh=int((latmax-latmin)*K)+2*PAD
    def P(lat,lon): return (round((lon-lonmin)*CY*K)+PAD, round((latmax-lat)*K)+PAD)
    hx,hy=P(H["lat"],H["lon"])
    s=[f'<svg viewBox="0 0 {W} {Hh}" style="width:100%;height:auto;max-height:640px" role="img" aria-label="Map of finds around Richmond">']
    for mi in (5,10,15,20,25):
        r=round(mi/69*K)
        s.append(f'<circle cx="{hx}" cy="{hy}" r="{r}" fill="none" stroke="var(--grid)" stroke-width="1"/>')
        s.append(f'<text x="{hx+4}" y="{hy-r-4}" font-size="10" fill="var(--mut)">{mi} mi</text>')
    if legs:
        pts=[(hx,hy)]+[P(l["lat"],l["lon"]) for l in legs]+[(hx,hy)]
        s.append('<polyline points="'+" ".join(f"{x},{y}" for x,y in pts)+'" fill="none" stroke="var(--seq)" stroke-width="2" stroke-linejoin="round" opacity="0.9"/>')
    for i in items:
        if i["id"] in onroute: continue
        x,y=P(i["lat"],i["lon"]); d=i["posted_days"]
        col="var(--good)" if d<=3 else ("#ec835a" if d<=21 else "var(--mut)")
        r=round(4+min(1,max(0,i["net_list"])/300)*5)
        s.append(f'<a href="https://www.google.com/maps/search/?api=1&amp;query={i["lat"]},{i["lon"]}" target="_blank"><circle cx="{x}" cy="{y}" r="{r}" fill="{col}" stroke="var(--s1)" stroke-width="1.5" opacity="0.9"><title>{i["title"][:70]} — ${i["net_list"]} net, {i["area"]}</title></circle></a>')
    for o in st.get("map_outlets",[]):
        x,y=P(o["lat"],o["lon"])
        s.append(f'<rect x="{x-4}" y="{y-4}" width="8" height="8" fill="none" stroke="var(--mut)" stroke-width="1.5"><title>{o["name"]}</title></rect>')
    for n,l in enumerate(legs,1):
        x,y=P(l["lat"],l["lon"])
        s.append(f'<a href="https://www.google.com/maps/search/?api=1&amp;query={l["lat"]},{l["lon"]}" target="_blank"><g><circle cx="{x}" cy="{y}" r="10" fill="var(--seq)" stroke="var(--s1)" stroke-width="2"/><text x="{x}" y="{y+3.5}" font-size="11" font-weight="700" fill="#fff" text-anchor="middle">{n}</text><title>Stop {n}: {l["title"][:60]} (+${l["net"]})</title></g></a>')
    s.append(f'<g transform="translate({hx},{hy})"><rect x="-6" y="-6" width="12" height="12" transform="rotate(45)" fill="var(--t1)" stroke="var(--s1)" stroke-width="1.5"><title>{H["label"]}</title></rect></g>')
    s.append(f'<text x="{hx}" y="{hy+22}" font-size="10.5" font-weight="600" fill="var(--t2)" text-anchor="middle">BASE</text>')
    s.append('</svg>')
    svg="".join(s)
    lg=('<div class="mlg"><span><i class="dot" style="background:var(--good)"></i> fresh (&le;3d)</span>'
        '<span><i class="dot" style="background:#ec835a"></i> confirm first</span>'
        '<span><i class="dot" style="background:var(--mut)"></i> long shot</span>'
        '<span><i class="dot" style="background:var(--seq)"></i> numbered = suggested run</span>'
        '<span><i class="sq"></i> cash-out outlet</span><span>dot size = est. net</span></div>')
    rows=""
    cum=0
    for n,l in enumerate(legs,1):
        cum+=l["net"]
        rows+=(f'<div class="prow"><b>{n}. {l["title"][:52]}</b><span><span id="leg-{n}">+{l["mi"]} mi · {l["drive_min"]} min drive</span> · {l["load_min"]} min load · nets ${l["net"]} (running ${cum})</span></div>')
    man=(f'<div class="panel"><h2>Suggested run — {len(legs)} stops</h2><div class="ps">{R.get("label","")}. Locations are town-approximate; get exact addresses from sellers before rolling.</div>{rows}'
         f'<div class="prow"><b>Loop totals</b><span><span id="looptot">{R.get("total_mi")} mi · ~{R.get("drive_min")} min driving (straight-line est.)</span> + {R.get("load_min")} min loading · gross ${R.get("total_net")} · with a {R.get("crew")}-person paid crew (${18}/hr): <b>${R.get("net_after_crew")}</b> net</span></div>'
         f'<div class="prow"><a href="{R.get("gmaps","#")}" target="_blank" rel="noopener"><b>Open full route in Google Maps →</b></a><span>turn-by-turn with all stops, ready to send to a driver</span></div></div>') if legs else ""
    D = dict(
        home=st["home"],
        rings=[5,10,15,20,25],
        route=dict(pts=([[H["lat"],H["lon"]]]+[[l["lat"],l["lon"]] for l in legs]+[[H["lat"],H["lon"]]]) if legs else []),
        items=[dict(lat=i["lat"], lon=i["lon"], d=i["posted_days"],
                    r=round(5+min(1,max(0,i["net_list"])/300)*5),
                    stop=onroute.get(i["id"],0),
                    pop="<b>%s</b><br>$%s est. net · %s<br><a href=\'%s\' target=\'_blank\'>open listing</a> · <a href=\'https://www.google.com/maps/search/?api=1&query=%s,%s\' target=\'_blank\'>directions</a>" % (i["title"][:70], i["net_list"], i["area"], i["url"], i["lat"], i["lon"]))
               for i in items],
        outlets=st.get("map_outlets",[]))
    js = """
<script>(function(){
 var D=__DATA__, ok=false;
 function fb(){var e=document.getElementById('lmap');if(e)e.style.display='none';var r=document.getElementById('radarwrap');if(r)r.style.display='block';var n=document.getElementById('mnote');if(n)n.textContent='Street tiles unavailable in this view — showing radar map. Open the downloaded file in your browser for full streets.';}
 if(!window.L){fb();return;}
 try{
  var map=L.map('lmap',{scrollWheelZoom:false}).setView([D.home.lat,D.home.lon],10);
  var t=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'&copy; OpenStreetMap contributors'});
  t.on('tileload',function(){ok=true;}); t.addTo(map);
  setTimeout(function(){if(!ok)fb();},5000);
  D.rings.forEach(function(mi){L.circle([D.home.lat,D.home.lon],{radius:mi*1609.34,fill:false,color:'#98968f',weight:1,opacity:.45,interactive:false}).addTo(map);});
  var straight=null;
  if(D.route.pts.length){
   straight=L.polyline(D.route.pts,{color:'#2a78d6',weight:3,opacity:.85}).addTo(map);
   var q=D.route.pts.map(function(p){return p[1]+','+p[0];}).join(';');
   fetch('https://router.project-osrm.org/route/v1/driving/'+q+'?overview=full&geometries=geojson&steps=false')
    .then(function(r){return r.json();})
    .then(function(j){
      if(j.code!=='Ok'||!j.routes||!j.routes[0])throw 0;
      var rt=j.routes[0];
      map.removeLayer(straight);
      L.geoJSON({type:'Feature',geometry:rt.geometry},{style:{color:'#2a78d6',weight:3.5,opacity:.9}}).addTo(map);
      var tot=document.getElementById('looptot');
      if(tot)tot.textContent=(rt.distance/1609.34).toFixed(0)+' mi · ~'+Math.round(rt.duration/60)+' min driving (road-measured)';
      (rt.legs||[]).forEach(function(lg,ix){var el=document.getElementById('leg-'+(ix+1));if(el)el.textContent='+'+(lg.distance/1609.34).toFixed(1)+' mi · '+Math.round(lg.duration/60)+' min drive';});
    })
    .catch(function(){if(straight)straight.setStyle({dashArray:'7 7'});});
  }
  D.items.forEach(function(i){
   if(i.stop){L.marker([i.lat,i.lon],{icon:L.divIcon({className:'stopic',html:i.stop,iconSize:[22,22]})}).addTo(map).bindPopup(i.pop);}
   else{var c=i.d<=3?'#0ca30c':(i.d<=21?'#ec835a':'#898781');L.circleMarker([i.lat,i.lon],{radius:i.r,color:'#ffffff',weight:1.5,fillColor:c,fillOpacity:.9}).addTo(map).bindPopup(i.pop);}
  });
  D.outlets.forEach(function(o){L.circleMarker([o.lat,o.lon],{radius:4,color:'#898781',weight:2,fill:false}).addTo(map).bindPopup(o.name);});
  L.marker([D.home.lat,D.home.lon],{icon:L.divIcon({className:'baseic',html:'&#9670;',iconSize:[20,20]})}).addTo(map).bindPopup(D.home.label);
 }catch(e){fb();}
})();</script>"""
    js = js.replace("__DATA__", _json.dumps(D))
    return ('<h2>Live map — finds &amp; suggested route</h2><div class="mapgrid"><div class="panel mappanel">'
            + '<div id="lmap"></div><div id="radarwrap" style="display:none">' + svg + lg + '</div>'
            + '<div class="mnote" id="mnote">Street tiles &copy; OpenStreetMap contributors · pins are town-approximate · click a pin for the listing + directions · if tiles are blocked in this view a radar map renders instead. Blue route follows real roads (OSRM); a dashed line means routing was unreachable (straight-line preview).</div></div>'
            + man + '</div>' + js)
import json, html
try:
    _lcss = open("node_modules/leaflet/dist/leaflet.css").read()
    _ljs = open("node_modules/leaflet/dist/leaflet.js").read().replace("//# sourceMappingURL=leaflet.js.map","")
    leaflet_assets = "<style>"+_lcss+"</style>\n<script>"+_ljs+"</script>"
except Exception:
    leaflet_assets = '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"/><script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>'


CSS_LIT = None  # set below
FLIP_SRC = 'import json, html\nitems, filtered, tot, meta = st["items"], st["filtered"], st["totals"], st["meta"]\nwanted_data, outlets_data = st["wanted"], st["outlets"]\nev_total = sum(i.get("ev_net",0) for i in items)\nfresh_ct = sum(1 for i in items if i["posted_days"]<=3)\n\ndef fresh_chip(days):\n    if days<=3:  return ("good","●","Fresh · %dd"%days)\n    if days<=21: return ("warn","◐","Confirm · %dd"%days)    # message before driving\n    w = round(days/7)\n    return ("stale","○","Long shot · %dwk"%w)\n\ndef money(n): return "$%s"%format(int(n),",")\n\nrows=[]\nfor rank,i in enumerate(items,1):\n    cls,ico,lab = fresh_chip(i["posted_days"])\n    pct=min(100,i["score"])\n    quick = (\'<div class="qr"><span class="qcash">%s</span> guaranteed-cash: %s</div>\'\n             %(money(i["net_quick"]),html.escape(i["quick_route"]))) if i.get("net_quick") and i["net_quick"]>0 else ""\n    flags="".join(\'<span class="fl">%s</span>\'%html.escape(f) for f in i["flags"])\n    rows.append(f\'\'\'<div class="row">\n  <div class="rk">{rank}</div>\n  <div class="sc"><div class="scn">{i["score"]}</div><div class="scb"><i style="width:{pct}%"></i></div></div>\n  <div class="main">\n    <a class="tt" href="{html.escape(i["url"])}" target="_blank" rel="noopener">{html.escape(i["title"])}</a>\n    <div class="meta"><span class="chip {cls}">{ico} {lab}</span><span>{html.escape(i["cat"])}</span><span>{html.escape(i["area"])} · ≈{i["miles"]} mi</span><span>{html.escape(i["size"])}</span></div>\n    <div class="cond">{html.escape(i["cond"])}</div>\n    <div class="act">→ {html.escape(i["action"])}</div>\n    {quick}<div class="lab">&#9201; ~{i["time_min"]//60}h{i["time_min"]%60:02d}m all-in · crew of {i["crew"]} · ≈${i["crew_hr"]}/crew-hr · net with paid crew (${int(st["labor_model"]["wage"])}/hr): <b class="{\'lok\' if i[\'labor_ok\'] else \'lno\'}">${i["net_labor"]}</b>{\'\' if i[\'labor_ok\'] else \' — below $20 labor floor\'}</div><div class="fls">{flags}</div>\n  </div>\n  <div class="nums"><div class="net">{money(i["net_list"])}</div><div class="nlb">est. net (list route)</div>\n    <div class="sub">resale ≈ {money(i["lo"])}–{money(i["hi"])}</div><div class="sub">drive cost ≈ {money(i["drive_cost"])} · conf: {i["conf"]}</div></div>\n</div>\'\'\')\n\nwrows="".join(\'<div class="prow"><a href="%s" target="_blank" rel="noopener"><b>%s</b></a><span>%s</span></div>\'%(w["url"],html.escape(w["title"]),html.escape(w["note"])) for w in wanted_data)\n\norows="".join(\'<div class="prow"><b>%s</b><span>%s</span></div>\'%(html.escape(o["name"]),html.escape(o["note"])) for o in outlets_data)\nfrows="".join(\'<div class="prow"><b>%s</b><span>%s</span></div>\'%(html.escape(f["title"]),html.escape(f["reason"])) for f in filtered)\n\n\npage = f\'\'\'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">\n<title>Flip Radar — Richmond, VA</title>\\n{leaflet_assets}<style>\n.vr{{color-scheme:light;--s1:#fcfcfb;--pg:#f9f9f7;--t1:#0b0b0b;--t2:#52514e;--mut:#898781;--grid:#e1e0d9;--bord:rgba(11,11,11,.10);\n--seq:#2a78d6;--seqA:#cde2fb;--good:#0ca30c;--goodtx:#006300;--warn:#fab219;--ser:#ec835a;--net:#006300}}\n@media(prefers-color-scheme:dark){{:root:where(:not([data-theme="light"])) .vr{{color-scheme:dark;--s1:#1a1a19;--pg:#0d0d0d;--t1:#fff;--t2:#c3c2b7;--mut:#898781;--grid:#2c2c2a;--bord:rgba(255,255,255,.10);--seq:#3987e5;--seqA:#184f95;--goodtx:#0ca30c;--net:#0ca30c}}}}\n:root[data-theme="dark"] .vr{{color-scheme:dark;--s1:#1a1a19;--pg:#0d0d0d;--t1:#fff;--t2:#c3c2b7;--mut:#898781;--grid:#2c2c2a;--bord:rgba(255,255,255,.10);--seq:#3987e5;--seqA:#184f95;--goodtx:#0ca30c;--net:#0ca30c}}\n*{{box-sizing:border-box;margin:0}}body{{background:var(--pg)}}\n.vr{{font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--t1);background:var(--pg);min-height:100vh;padding:20px clamp(12px,3vw,36px) 48px}}\n.hd{{display:flex;flex-wrap:wrap;align-items:baseline;gap:10px 16px;margin-bottom:4px}}\nh1{{font-size:21px;font-weight:700}}.hd .sub{{color:var(--t2);font-size:13px}}\n.cfg{{color:var(--mut);font-size:12.5px;margin-bottom:16px}}.cfg b{{color:var(--t2);font-weight:600}}\n.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:18px}}\n.tile{{background:var(--s1);border:1px solid var(--bord);border-radius:10px;padding:12px 14px}}\n.tv{{font-size:24px;font-weight:700}}.tl{{font-size:12px;color:var(--t2);margin-top:2px}}.tile .hint{{font-size:11px;color:var(--mut);margin-top:2px}}\nh2{{font-size:14px;font-weight:700;margin:22px 0 8px}}\n.row{{display:grid;grid-template-columns:30px 64px 1fr 168px;gap:12px;background:var(--s1);border:1px solid var(--bord);border-radius:10px;padding:13px 14px;margin-bottom:8px;align-items:start}}\n.rk{{font-size:15px;font-weight:700;color:var(--mut);padding-top:2px}}\n.scn{{font-size:20px;font-weight:700;font-variant-numeric:tabular-nums}}\n.scb{{height:4px;background:var(--grid);border-radius:2px;margin-top:4px}}.scb i{{display:block;height:4px;border-radius:2px;background:var(--seq)}}\n.sc::after{{content:"score";font-size:10.5px;color:var(--mut)}}\n.tt{{font-size:15px;font-weight:650;color:var(--t1);text-decoration:none}}.tt:hover{{text-decoration:underline;color:var(--seq)}}\n.meta{{display:flex;flex-wrap:wrap;gap:6px 12px;font-size:12px;color:var(--t2);margin:4px 0 2px}}\n.chip{{font-weight:650;border-radius:99px;padding:0 8px;border:1px solid var(--bord)}}\n.chip.good{{color:var(--goodtx)}}.chip.warn{{color:var(--ser)}}.chip.stale{{color:var(--mut)}}\n.cond{{font-size:12.5px;color:var(--t2);margin-top:3px}}\n.act{{font-size:12.5px;font-weight:600;margin-top:5px}}\n.qr{{font-size:12px;color:var(--t2);margin-top:4px}}.qcash{{font-weight:700;color:var(--goodtx)}}\n.lab{{font-size:12px;color:var(--t2);margin-top:4px}}.lab b.lok{{color:var(--goodtx)}}.lab b.lno{{color:var(--mut)}}\n.fls{{margin-top:6px;display:flex;flex-wrap:wrap;gap:4px}}\n.fl{{font-size:10.5px;color:var(--mut);border:1px solid var(--grid);border-radius:4px;padding:0 5px}}\n.nums{{text-align:right}}.net{{font-size:19px;font-weight:700;color:var(--net);font-variant-numeric:tabular-nums}}\n.nlb{{font-size:10.5px;color:var(--mut)}}.sub{{font-size:11.5px;color:var(--t2);margin-top:2px;font-variant-numeric:tabular-nums}}\n#lmap{{height:560px;border-radius:8px;background:#e8e6e0}}\n.mnote{{font-size:11px;color:var(--mut);padding:6px 6px 0}}\n.stopic{{background:#2a78d6;color:#fff;border-radius:50%;text-align:center;line-height:22px;font-weight:700;border:2px solid #fff;font-size:12px}}\n.baseic{{font-size:20px;line-height:20px;color:#0b0b0b;text-shadow:0 0 3px #fff,0 0 3px #fff;text-align:center}}\n@media(prefers-color-scheme:dark){{:root:where(:not([data-theme="light"])) .vr #lmap .leaflet-tile{{filter:invert(1) hue-rotate(180deg) brightness(.95) saturate(.55)}}:root:where(:not([data-theme="light"])) .vr #lmap{{background:#151515}}}}\n:root[data-theme="dark"] .vr #lmap .leaflet-tile{{filter:invert(1) hue-rotate(180deg) brightness(.95) saturate(.55)}}:root[data-theme="dark"] .vr #lmap{{background:#151515}}\n.mapgrid{{display:grid;grid-template-columns:minmax(300px,430px) 1fr;gap:14px;align-items:start}}\n@media(max-width:760px){{.mapgrid{{grid-template-columns:1fr}}}}\n.mappanel{{padding:10px}}\n.mlg{{display:flex;flex-wrap:wrap;gap:5px 14px;font-size:11.5px;color:var(--t2);padding:8px 6px 2px}}\n.mlg .dot{{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:4px}}\n.mlg .sq{{display:inline-block;width:8px;height:8px;border:1.5px solid var(--mut);margin-right:4px}}\n.cols{{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:14px}}\n.panel{{background:var(--s1);border:1px solid var(--bord);border-radius:10px;padding:14px 16px}}\n.panel h2{{margin:0 0 4px}}.panel .ps{{font-size:12px;color:var(--t2);margin-bottom:8px}}\n.prow{{padding:7px 0;border-top:1px solid var(--grid);font-size:12.5px}}.prow b{{display:block;font-weight:650}}.prow span{{color:var(--t2)}}\n.prow a{{color:var(--t1);text-decoration:none}}.prow a:hover{{color:var(--seq)}}\n.foot{{margin-top:20px;font-size:11.5px;color:var(--mut);max-width:900px}}\n@media(max-width:640px){{.row{{grid-template-columns:24px 52px 1fr}}.nums{{grid-column:2/4;text-align:left;display:flex;gap:14px;align-items:baseline}}}}\n</style></head><body><div class="vr">\n<div class="hd"><h1>Flip Radar</h1><span class="sub">Richmond, VA · free-item arbitrage board</span>\n<span class="sub" style="margin-left:auto">Scanned <b>{meta["scan_label"]}</b> · next auto-scan <b>{meta["next_scan_label"]}</b> · runs 7:30 AM / 5:30 PM daily</span></div>\n<div class="cfg">Base: <b>South Richmond (23224)</b> · radius <b>25 mi</b> · hauling <b>pickup + trailer</b> · floor <b>$30 net</b> · sources: <b>Craigslist + trash nothing (cloud) · FB Marketplace via your Chrome when desktop is online</b> · <b>Nextdoor live (logged in)</b> · labor model: $18/hr/person, 2.3 min/mi, load time by size</div>\n<div class="tiles">\n<div class="tile"><div class="tv">{len(items)}</div><div class="tl">live finds over the $30 floor</div></div>\n<div class="tile"><div class="tv">{fresh_ct}</div><div class="tl">fresh (≤3 days) — act today</div></div>\n<div class="tile"><div class="tv">{money(tot["lo"])}–{money(tot["hi"])}</div><div class="tl">combined resale estimate</div></div>\n<div class="tile"><div class="tv">{money(ev_total)}</div><div class="tl">expected value on the board</div><div class="hint">net × odds each item is still there</div></div>\n<div class="tile"><div class="tv">{money(items[0]["net_list"])}</div><div class="tl">best single play — {html.escape(items[0]["title"][:34])}…</div></div>\n<div class="tile"><div class="tv">{sum(1 for i in items if i.get("labor_ok"))} / {len(items)}</div><div class="tl">still profitable with a paid crew</div><div class="hint">$18/hr per person, drive + load + sell time</div></div>\n</div>\n{build_map(st)}\\n<h2>Ranked opportunities — highest priority first</h2>\n{"".join(rows)}\n<div class="cols">\n<div class="panel"><h2>Active buyers near you (demand signals)</h2><div class="ps">People currently posting "wanted" ads — direct sell-to targets when matching items turn up free.</div>{wrows}</div>\n<div class="panel"><h2>Guaranteed cash-out directory</h2><div class="ps">Where an item converts to same-day cash instead of waiting on a buyer. Expect ~30–40% of resale at pawn; call ahead.</div>{orows}</div>\n<div class="panel"><h2>Seen &amp; filtered this scan</h2><div class="ps">Found but under your $30-net floor (kept for dedupe so they don\'t resurface).</div>{frows}\n<div class="prow"><b>Scoring</b><span>score = margin 45 (net × availability odds) + sell-speed 20 + freshness 20 + effort 15. Drive cost $0.70/mi round trip. Driver scenario: all-in time = round-trip drive @2.3 min/mi + load (10-60 min by size) + 15 min sell overhead; crew of 2 when heavy; net-with-crew subtracts $18/hr per person. All values are estimates from listing text — condition unverified until you see the item. Always message before driving on anything marked "confirm."</span></div></div>\n</div>\n<div class="foot">Values are conservative quick-sale estimates for the Richmond market, not appraisals. Free listings move fast — the two fresh ones at the top typically disappear within a day. This board updates automatically twice daily; claimed/gone items drop off and new finds slot in by score.</div>\n</div></body></html>\'\'\''

def render_flip(st, prof=None, nav=""):
    g = {"st": st, "build_map": build_map, "leaflet_assets": leaflet_assets, "_json": _json}
    exec(FLIP_SRC, g)
    return _inject_nav(g["page"], nav)

# shared CSS literal for non-flip renderers (identical to flip's)
CSS_LIT = '\n.vr{color-scheme:light;--s1:#fcfcfb;--pg:#f9f9f7;--t1:#0b0b0b;--t2:#52514e;--mut:#898781;--grid:#e1e0d9;--bord:rgba(11,11,11,.10);\n--seq:#2a78d6;--seqA:#cde2fb;--good:#0ca30c;--goodtx:#006300;--warn:#fab219;--ser:#ec835a;--net:#006300}\n@media(prefers-color-scheme:dark){:root:where(:not([data-theme="light"])) .vr{color-scheme:dark;--s1:#1a1a19;--pg:#0d0d0d;--t1:#fff;--t2:#c3c2b7;--mut:#898781;--grid:#2c2c2a;--bord:rgba(255,255,255,.10);--seq:#3987e5;--seqA:#184f95;--goodtx:#0ca30c;--net:#0ca30c}}\n:root[data-theme="dark"] .vr{color-scheme:dark;--s1:#1a1a19;--pg:#0d0d0d;--t1:#fff;--t2:#c3c2b7;--mut:#898781;--grid:#2c2c2a;--bord:rgba(255,255,255,.10);--seq:#3987e5;--seqA:#184f95;--goodtx:#0ca30c;--net:#0ca30c}\n*{box-sizing:border-box;margin:0}body{background:var(--pg)}\n.vr{font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--t1);background:var(--pg);min-height:100vh;padding:20px clamp(12px,3vw,36px) 48px}\n.hd{display:flex;flex-wrap:wrap;align-items:baseline;gap:10px 16px;margin-bottom:4px}\nh1{font-size:21px;font-weight:700}.hd .sub{color:var(--t2);font-size:13px}\n.cfg{color:var(--mut);font-size:12.5px;margin-bottom:16px}.cfg b{color:var(--t2);font-weight:600}\n.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:18px}\n.tile{background:var(--s1);border:1px solid var(--bord);border-radius:10px;padding:12px 14px}\n.tv{font-size:24px;font-weight:700}.tl{font-size:12px;color:var(--t2);margin-top:2px}.tile .hint{font-size:11px;color:var(--mut);margin-top:2px}\nh2{font-size:14px;font-weight:700;margin:22px 0 8px}\n.row{display:grid;grid-template-columns:30px 64px 1fr 168px;gap:12px;background:var(--s1);border:1px solid var(--bord);border-radius:10px;padding:13px 14px;margin-bottom:8px;align-items:start}\n.rk{font-size:15px;font-weight:700;color:var(--mut);padding-top:2px}\n.scn{font-size:20px;font-weight:700;font-variant-numeric:tabular-nums}\n.scb{height:4px;background:var(--grid);border-radius:2px;margin-top:4px}.scb i{display:block;height:4px;border-radius:2px;background:var(--seq)}\n.sc::after{content:"score";font-size:10.5px;color:var(--mut)}\n.tt{font-size:15px;font-weight:650;color:var(--t1);text-decoration:none}.tt:hover{text-decoration:underline;color:var(--seq)}\n.meta{display:flex;flex-wrap:wrap;gap:6px 12px;font-size:12px;color:var(--t2);margin:4px 0 2px}\n.chip{font-weight:650;border-radius:99px;padding:0 8px;border:1px solid var(--bord)}\n.chip.good{color:var(--goodtx)}.chip.warn{color:var(--ser)}.chip.stale{color:var(--mut)}\n.cond{font-size:12.5px;color:var(--t2);margin-top:3px}\n.act{font-size:12.5px;font-weight:600;margin-top:5px}\n.qr{font-size:12px;color:var(--t2);margin-top:4px}.qcash{font-weight:700;color:var(--goodtx)}\n.lab{font-size:12px;color:var(--t2);margin-top:4px}.lab b.lok{color:var(--goodtx)}.lab b.lno{color:var(--mut)}\n.fls{margin-top:6px;display:flex;flex-wrap:wrap;gap:4px}\n.fl{font-size:10.5px;color:var(--mut);border:1px solid var(--grid);border-radius:4px;padding:0 5px}\n.nums{text-align:right}.net{font-size:19px;font-weight:700;color:var(--net);font-variant-numeric:tabular-nums}\n.nlb{font-size:10.5px;color:var(--mut)}.sub{font-size:11.5px;color:var(--t2);margin-top:2px;font-variant-numeric:tabular-nums}\n#lmap{height:560px;border-radius:8px;background:#e8e6e0}\n.mnote{font-size:11px;color:var(--mut);padding:6px 6px 0}\n.stopic{background:#2a78d6;color:#fff;border-radius:50%;text-align:center;line-height:22px;font-weight:700;border:2px solid #fff;font-size:12px}\n.baseic{font-size:20px;line-height:20px;color:#0b0b0b;text-shadow:0 0 3px #fff,0 0 3px #fff;text-align:center}\n@media(prefers-color-scheme:dark){:root:where(:not([data-theme="light"])) .vr #lmap .leaflet-tile{filter:invert(1) hue-rotate(180deg) brightness(.95) saturate(.55)}:root:where(:not([data-theme="light"])) .vr #lmap{background:#151515}}\n:root[data-theme="dark"] .vr #lmap .leaflet-tile{filter:invert(1) hue-rotate(180deg) brightness(.95) saturate(.55)}:root[data-theme="dark"] .vr #lmap{background:#151515}\n.mapgrid{display:grid;grid-template-columns:minmax(300px,430px) 1fr;gap:14px;align-items:start}\n@media(max-width:760px){.mapgrid{grid-template-columns:1fr}}\n.mappanel{padding:10px}\n.mlg{display:flex;flex-wrap:wrap;gap:5px 14px;font-size:11.5px;color:var(--t2);padding:8px 6px 2px}\n.mlg .dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:4px}\n.mlg .sq{display:inline-block;width:8px;height:8px;border:1.5px solid var(--mut);margin-right:4px}\n.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:14px}\n.panel{background:var(--s1);border:1px solid var(--bord);border-radius:10px;padding:14px 16px}\n.panel h2{margin:0 0 4px}.panel .ps{font-size:12px;color:var(--t2);margin-bottom:8px}\n.prow{padding:7px 0;border-top:1px solid var(--grid);font-size:12.5px}.prow b{display:block;font-weight:650}.prow span{color:var(--t2)}\n.prow a{color:var(--t1);text-decoration:none}.prow a:hover{color:var(--seq)}\n.foot{margin-top:20px;font-size:11.5px;color:var(--mut);max-width:900px}\n@media(max-width:640px){.row{grid-template-columns:24px 52px 1fr}.nums{grid-column:2/4;text-align:left;display:flex;gap:14px;align-items:baseline}}\n'


def nav_html(active):
    base = "https://davidbedard-lgtm.github.io/flip-radar/"
    tabs = [("hub","Hub",""),("flip","Flip",""+"flip/"),("haul","Haul","haul/")]
    links = "".join(
        '<a href="%s%s" style="text-decoration:none;font-weight:%s;color:%s;padding:2px 10px;border-radius:99px;%s">%s</a>'
        % (base, path, "700" if key==active else "600",
           "var(--t1)" if key==active else "var(--t2)",
           "background:var(--grid);" if key==active else "", label)
        for key,label,path in tabs)
    return ('<div class="nav" style="display:flex;gap:4px;align-items:center;margin:-6px 0 12px;font-size:13px">'
            '<span style="color:var(--mut);margin-right:6px">Boards:</span>'+links+'</div>')

def _inject_nav(page, nav):
    return page.replace('<div class="vr">', '<div class="vr">'+nav, 1) if nav else page

def render_haul(st, prof, nav=""):
    import html
    items, filtered, tot, meta = st["items"], st["filtered"], st["totals"], st["meta"]
    dm = st.get("disposal_note","")
    def money(n): return "$%s"%format(int(n),",")
    def fresh_chip(h):
        if h<=24: return ("good","●","Fresh · %dh"%h)
        if h<=72: return ("warn","◐","%dd old — call fast"%round(h/24))
        return ("stale","○","%dd old — long shot"%round(h/24))
    rows=[]
    for rank,i in enumerate(items,1):
        cls,ico,lab = fresh_chip(i.get("age_hours",72))
        pct=min(100,i["score"])
        flags="".join('<span class="fl">%s</span>'%html.escape(f) for f in i["flags"])
        der = '<span class="chip" style="color:var(--seq)">derived lead</span>' if i.get("derived") else ""
        freon = '<div class="qr" style="color:var(--ser)">⚠ freon appliance in load — needs certified recovery, not priced</div>' if i.get("freon") else ""
        rows.append(f'''<div class="row">
  <div class="rk">{rank}</div>
  <div class="sc"><div class="scn">{i["score"]}</div><div class="scb"><i style="width:{pct}%"></i></div></div>
  <div class="main">
    <a class="tt" href="{html.escape(i["url"])}" target="_blank" rel="noopener">{html.escape(i["title"])}</a>
    <div class="meta"><span class="chip {cls}">{ico} {lab}</span>{der}<span>{html.escape(i["cat"])}</span><span>{html.escape(i["area"])} · ≈{i["miles"]} mi</span><span>crew of {i["crew"]}</span></div>
    <div class="cond">{html.escape(i["cond"])}</div>
    <div class="act">→ {html.escape(i["action"])}</div>
    <div class="qr">quote ≈ <b>{money(i["quote_lo"])}–{money(i["quote_hi"])}</b> · disposal ≈ {money(i["disposal_cost"])} · drive ≈ {money(i["drive_cost"])} · labor ≈ {money(i["labor_cost"])} · recovery offset ≈ <span class="qcash">+{money(i["recovery_est"])}</span></div>
    {freon}<div class="lab">&#9201; ~{i["time_min"]//60}h{i["time_min"]%60:02d}m all-in · CASH <b class="{'lok' if i['cash_crew_hr']>=40 else 'lno'}">≈${i["cash_crew_hr"]}/crew-hr</b> (fee only) · upside with recovery ≈ ${i["crew_hr"]}/crew-hr · EV {money(i["ev"])} ({int(i["p_win"]*100)}% win{(" × %d%% item still there"%round(i.get("p_avail_src",1)*100)) if i.get("derived") else ""})</div>
    <div class="fls">{flags}</div>
  </div>
  <div class="nums"><div class="net">{money(i["cash_net"])}</div><div class="nlb">CASH net (fee − costs)</div>
    <div class="sub">+{money(i["recovery_est"])} recovery upside → {money(i["net"])} total</div><div class="sub">conf: {i["conf"]}</div></div>
</div>''')
    frows="".join('<div class="prow"><b>%s</b><span>%s</span></div>'%(html.escape(f["title"]),html.escape(f["reason"])) for f in filtered)
    vrows="".join('<div class="prow"><b>%s</b><span>%s</span></div>'%(html.escape(a),html.escape(b)) for a,b in [
      ("Commercial auto coverage","Open question: does current auto policy cover paid hauling work? Personal policies usually exclude it."),
      ("Business license","Open question: Richmond/Chesterfield business license status for junk-removal work."),
      ("Landfill commercial account","Open question: cash rates vs. account rates at Shoosmith / transfer stations — an account usually cuts the tip fee."),
    ])
    fresh_ct=sum(1 for i in items if i.get("age_hours",99)<=24)
    ev_total=sum(i["ev"] for i in items)
    best=max(items,key=lambda x:x["cash_crew_hr"]) if items else None
    rec_ct=sum(1 for i in items if "recurring potential" in " ".join(i["flags"]))
    title="Haul Radar"; page = f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>Haul Radar — Richmond, VA</title>
{leaflet_assets}<style>{CSS_LIT}</style></head><body><div class="vr">
<div class="hd"><h1>Haul Radar</h1><span class="sub">Richmond, VA · paid removal &amp; cleanout leads</span>
<span class="sub" style="margin-left:auto">Scanned <b>{meta["scan_label"]}</b> · HAUL scans run <b>mornings only</b> (7:30 AM)</span></div>
<div class="cfg">Base: <b>South Richmond (23224)</b> · the truck earns instead of costs: quote − disposal − drive − labor <b>+ resale recovery</b> · floor <b>$40/crew-hr</b> · {dm}</div>
<div class="tiles">
<div class="tile"><div class="tv">{len(items)}</div><div class="tl">open leads over the floor</div></div>
<div class="tile"><div class="tv">{fresh_ct}</div><div class="tl">fresh (≤24h) — call today</div></div>
<div class="tile"><div class="tv">{money(ev_total)}</div><div class="tl">total EV on the board</div><div class="hint">net × odds each job is still open</div></div>
<div class="tile"><div class="tv">${best["cash_crew_hr"] if best else 0}/hr</div><div class="tl">best CASH $/crew-hr — {html.escape(best["title"][:28]) if best else "—"}…</div></div>
<div class="tile"><div class="tv">{rec_ct}</div><div class="tl">leads with recurring potential</div><div class="hint">property managers, estates, landlords</div></div>
</div>
{build_map(st)}
<h2>Ranked leads — best CASH $/crew-hour first (recovery shown as upside, never mixed in)</h2>
{"".join(rows)}
<div class="cols">
<div class="panel"><h2>Relationships / recurring — applications, not leads</h2><div class="ps">Standing recruitment posts (win-odds &lt;15%) — these resolve by applying and building a relationship, not in the lead flow. They clear the cash floor; they just are not one-off jobs.</div>{"".join('<div class="prow"><a href="%s" target="_blank" rel="noopener"><b>%s</b></a><span>cash ≈ $%s/crew-hr if landed · %s</span></div>'%(r["url"],html.escape(r["title"][:70]),r["cash_crew_hr"],html.escape(r["action"])) for r in st.get("relationships",[]))}</div>
<div class="panel"><h2>Verify before quoting</h2><div class="ps">Standing open questions — not legal or insurance advice, just the three things to nail down before taking paid jobs.</div>{vrows}</div>
<div class="panel"><h2>Seen &amp; filtered this scan</h2><div class="ps">Leads under the $40/crew-hr floor, expired gigs, and out-of-area asks.</div>{frows}
<div class="prow"><b>Scoring</b><span>net = quote − disposal − drive ($0.70/mi RT) − labor ($18/hr/person) + resale recovery. Score weights: $/crew-hr 45 (cap $150), EV 25 (cap $400), freshness 20, proximity 10. Gig win-odds decay fast: ≤6h 70% · ≤24h 45% · ≤3d 20% · older 8%. All quotes and volumes are estimates from post text.</span></div></div>
</div>
<div class="foot">Quotes, volumes, and disposal costs are estimates until you see the job — confirm tipping rates by phone before bidding. Leads only: you make contact and set terms; the scanner never messages anyone. Derived leads are stuck free-items reframed as removal quotes — the poster has NOT asked for paid help. Linked-plan rows share one object with the FLIP board: pitch paid removal first, fall back to the free grab if declined — never run both asks. Hub totals count derived leads at CASH value only; the resale upside counts once, on FLIP.</div>
</div></body></html>'''
    return _inject_nav(page, nav)

def render_hub(states, boards, nav=""):
    import html
    def money(n): return "$%s"%format(int(n),",")
    cards=[]
    for b in boards:
        if not b.get("enabled"): continue
        st=states.get(b["name"]);
        if not st: continue
        items=st["items"]; fresh=sum(1 for i in items if i.get("posted_days",9)<=3 or i.get("age_hours",99)<=24)
        ev=sum(i.get("ev_hub", i.get("ev_net", i.get("ev",0))) for i in items)
        top=items[0] if items else None
        cards.append(f'''<a class="tile" style="text-decoration:none" href="{b["name"]}/">
<div class="tv">{b["title"]}</div>
<div class="tl">{len(items)} live · {fresh} fresh · EV {money(ev)}</div>
<div class="hint">top: {html.escape(top["title"][:60]) if top else "—"}</div>
<div class="hint" style="color:var(--seq);font-weight:600">open board →</div></a>''')
    scan = states.get("flip",{}).get("meta",{}).get("scan_label","")
    try: outcomes = json.load(open("outcomes.json"))
    except Exception: outcomes = []
    if outcomes:
        realized = sum((o.get("sold_price") or 0)-(o.get("ask_paid") or 0)-(o.get("repair_cost") or 0)-round((o.get("drive_miles") or 0)*0.70) for o in outcomes if o.get("sold_price") is not None)
        sold = [o for o in outcomes if o.get("sold_price") is not None]
        cats = {}
        for o in sold: cats.setdefault(o.get("category","other"),[]).append(o)
        acc = " · ".join("%s: %d logged"%(k,len(v)) for k,v in sorted(cats.items()))
        results_panel = ('<div class="panel" style="margin-top:14px"><h2>Results — actuals, not estimates</h2>'
          '<div class="prow"><b>%d flips logged · %d sold · realized net %s</b><span>%s. Calibration factors activate at 5 sales per category.</span></div></div>'
          % (len(outcomes), len(sold), "$%s"%format(int(realized),","), acc or "—"))
    else:
        results_panel = ('<div class="panel" style="margin-top:14px"><h2>Results — actuals, not estimates</h2>'
          '<div class="prow"><b>0 outcomes logged yet</b><span>Report any result in chat in one sentence — "got the drill for $10, sold it for $55 in three days" — and it lands here. Ten logged outcomes unlock per-category calibration; until then every board number is an uncalibrated estimate.</span></div></div>')
    page = f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>Radar — Boards</title>
<style>{CSS_LIT}</style></head><body><div class="vr">
<div class="hd"><h1>Radar</h1><span class="sub">Richmond, VA · David's automated boards</span>
<span class="sub" style="margin-left:auto">Last scan <b>{scan}</b> · auto-updates 7:30 AM / 5:30 PM</span></div>
<div class="tiles" style="grid-template-columns:repeat(auto-fit,minmax(260px,1fr))">{"".join(cards)}</div>
{results_panel}
<div class="foot">Flip = free items worth grabbing and reselling. Haul = paid removal/cleanout leads where the load's resale value subsidizes the quote (HAUL scans mornings only). Dedupe rule: a derived HAUL lead and its FLIP source are one object — hub totals count the resale value once, on FLIP; derived leads enter at cash value. Every number is an estimate until the outcomes ledger calibrates it.</div>
</div></body></html>'''
    return _inject_nav(page, nav)


BANNED_ON_RUNSHEET = ("resale","resell","ev ","score","$/crew","flip for","worth $","net_list","margin")
def _sanitize_verify(it):
    run = it.get("run",{})
    if run.get("verify"): return run["verify"]
    keep=[]
    for s in re.split(r"(?<=[.;]) ", it.get("cond","")):
        low=s.lower()
        if any(b in low for b in ("resell","resale","$","sell","flip","worth","market","do \u0024")): continue
        keep.append(s)
    return " ".join(keep) or "Match item and condition against the listing photos before paying anything."

def render_runsheet(st, driver=None):
    import html, re as _re, datetime
    stops=[i for i in st["items"] if i.get("run",{}).get("status")=="confirmed" and (driver is None or i["run"].get("driver")==driver)]
    by={}
    for i in stops: by.setdefault(i["run"].get("driver","Driver"),[]).append(i)
    pages=[]
    for drv, its in by.items():
        cards=[]
        for n,i in enumerate(its,1):
            r=i["run"]
            cards.append(f'''<div class="stopcard">
<div class="sc-head"><span class="sc-n">STOP {n}</span><span class="sc-id">{html.escape(i["id"])}</span><span class="sc-crew">crew of {r.get("crew",1)}</span></div>
<div class="sc-title">{html.escape(i["title"])}</div>
<div class="sc-line"><b>Address:</b> {html.escape(r["address"])}</div>
<div class="sc-line"><b>Window (seller-confirmed):</b> {html.escape(r["window"])}</div>
<div class="sc-pay">MAX AUTHORIZED TO PAY: <b>${r.get("max_pay",0)}</b> — one dollar more, call David first</div>
<div class="sc-line"><b>Verify on sight:</b> {html.escape(_sanitize_verify(i))}</div>
<div class="sc-line"><b>Photos (all four):</b> ☐ item front &nbsp; ☐ label / model number &nbsp; ☐ any damage &nbsp; ☐ loaded &amp; secured</div>
<div class="sc-line paper"><b>Paper fallback:</b> arrived ______ : ______ &nbsp;&nbsp; left ______ : ______ &nbsp;&nbsp; paid $ ________</div>
<div class="sc-line"><b>Outcome (circle):</b> PICKED UP &nbsp;·&nbsp; ITEM GONE &nbsp;·&nbsp; DECLINED / MISMATCH &nbsp;·&nbsp; RESCHEDULE</div>
<div class="sc-notes">Notes: ______________________________________________________________________</div>
</div>''')
        pages.append(f'''<div class="rs-page">
<div class="rs-head"><h1>RUN SHEET — {html.escape(drv)}</h1><div class="rs-sub">Flip Radar dispatch · date ____________ · truck ____________</div></div>
<div class="rs-line"><b>Storage drop-off:</b> ______________________________________ &nbsp; <b>David:</b> call/text before paying over max, on any mismatch, or if anyone asks questions</div>
{"".join(cards)}
<div class="rs-foot">Rules: never contact the seller — David has already confirmed every stop. Pay cash only up to the printed max. If the item does not match the sheet, photograph it, mark DECLINED, and move on. Log every stop in the Run Form before leaving the curb (paper fields above are the backup).</div>
</div>''')
    page = ("<!DOCTYPE html><html><head><meta charset=\"utf-8\"><title>Run Sheet</title><style>"
      "body{font:13px/1.45 system-ui,-apple-system,'Segoe UI',sans-serif;color:#0b0b0b;background:#fff;margin:0}"
      ".rs-page{max-width:7.6in;margin:0 auto;padding:24px 28px;page-break-after:always}"
      "h1{font-size:20px;margin:0}.rs-sub{color:#52514e;font-size:12px;margin-top:2px}"
      ".rs-head{border-bottom:2px solid #0b0b0b;padding-bottom:8px;margin-bottom:8px}"
      ".rs-line{font-size:12.5px;margin:6px 0 12px}"
      ".stopcard{border:1.5px solid #0b0b0b;border-radius:8px;padding:10px 12px;margin-bottom:12px;page-break-inside:avoid}"
      ".sc-head{display:flex;gap:10px;align-items:baseline}.sc-n{font-weight:800}.sc-id{font-family:ui-monospace,monospace;background:#f0efec;padding:0 6px;border-radius:4px}.sc-crew{margin-left:auto;font-weight:700}"
      ".sc-title{font-size:15px;font-weight:700;margin:4px 0}"
      ".sc-line{font-size:12.5px;margin:5px 0}.paper{background:#f9f9f7;padding:4px 6px;border-radius:4px}"
      ".sc-pay{font-size:14px;font-weight:700;border:2px solid #0b0b0b;display:inline-block;padding:3px 10px;border-radius:6px;margin:4px 0}"
      ".sc-notes{margin-top:6px;font-size:12.5px}.rs-foot{font-size:11.5px;color:#52514e;border-top:1px solid #c3c2b7;padding-top:8px;margin-top:4px}"
      "@media print{.rs-page{padding:0.35in 0.4in}}"
      "</style></head><body>"+ "".join(pages) +"</body></html>")
    import re as _re2
    content = _re2.sub(r"<style>.*?</style>", "", page, flags=_re2.S).lower()   # strip CSS before scanning
    for b in BANNED_ON_RUNSHEET:
        assert b not in content, "PRIVACY/SCOPE VIOLATION: banned term on driver-facing sheet: "+b
    return page

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", default="flip")
    ap.add_argument("--out", default=None)
    ap.add_argument("--no-nav", action="store_true")
    ap.add_argument("--runsheet", action="store_true")
    ap.add_argument("--driver", default=None)
    args = ap.parse_args()
    if args.runsheet:
        import os
        st = json.load(open("state_%s.json" % args.board))
        page = render_runsheet(st, args.driver)
        out = args.out or "private_runsheets/runsheet.html"
        ap_out = os.path.abspath(out)
        assert "/tmp/pub" not in ap_out and "flip-radar/flip" not in ap_out and not ap_out.endswith("index.html"), \
            "PRIVACY: run sheets are local-only and must never be written into the publish tree"
        os.makedirs(os.path.dirname(ap_out) or ".", exist_ok=True)
        open(out,"w").write(page); print("runsheet wrote", out, len(page), "chars (LOCAL ONLY — never published)"); raise SystemExit
    if args.board == "hub":
        boards = [json.load(open("boards/%s.json"%n)) for n in ("flip","haul","auction")]
        states = {}
        for b in boards:
            try: states[b["name"]] = json.load(open("state_%s.json"%b["name"]))
            except Exception: pass
        page = render_hub(states, boards, "" if args.no_nav else nav_html("hub"))
    else:
        prof = json.load(open("boards/%s.json" % args.board))
        st = json.load(open("state_%s.json" % args.board))
        nav = "" if args.no_nav else nav_html(args.board)
        page = {"flip": render_flip, "haul": render_haul}[prof["renderer"]](st, prof, nav)
    out = args.out or (args.board if args.board=="index" else args.board) 
    out = args.out or ("hub.html" if args.board=="hub" else "%s.html" % args.board)
    open(out,"w").write(page)
    print("engine wrote", out, len(page), "chars")
