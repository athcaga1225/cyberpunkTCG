#!/usr/bin/env python3
"""Refresh verified Welcome to Night City Beta card prices from public price-guide pages."""
import json,re,unicodedata,datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
from datetime import date as calendar_date, timedelta

BASE="https://valuemycard.com"
GUIDE=BASE+"/expansions/cyberpunk-tcg/24845-welcome-to-night-city-beta"
RARITY_CODES={"Common":"C","Uncommon":"UC","Rare":"R","Epic":"E","Secret":"S","Iconic Legend":"IL","Iconic Other":"IO","Iconic Secret":"IS"}
catalog=json.loads(Path("card-catalog.json").read_text())["cards"]
data=json.loads(Path("prices.json").read_text())
session=requests.Session()
session.headers.update({"User-Agent":"Mozilla/5.0 (CYBERSCAN personal Beta collector reference)"})
results={}
failures=[]
MONTHS={m:i for i,m in enumerate(("Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"),1)}
today=calendar_date.today()
def observed_date(day,month):
    month_no=MONTHS[month.title()]
    stamp=calendar_date(today.year,month_no,int(day))
    if stamp>today+timedelta(days=1):
        stamp=calendar_date(today.year-1,month_no,int(day))
    return stamp.isoformat()
for page in range(1,4):
    url=GUIDE+("?page="+str(page) if page>1 else "")
    response=session.get(url,timeout=25)
    response.raise_for_status()
    soup=BeautifulSoup(response.text,"html.parser")
    anchors=soup.find_all("a",href=re.compile(r"^/card/\d+"))
    print("PAGE",page,"CARD ROWS",len(anchors),flush=True)
    for link in anchors:
        title=link.get_text(" ",strip=True)
        match=re.search(r"#\s*(B\d{3}[ab]?)\s+(.+?)\s+(IL|IS|IO|UC|C|R|E|S)\s+\$(\d+(?:\.\d+)?)\s+(Foil|Normal)\s+Updated\s+(\d+)\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)",title,re.I)
        if not match:
            failures.append(("unparsed",title))
            continue
        code,source_name,rarity_code,usd,printing,day,month=match.groups()
        code=code.upper()
        card=catalog.get(code)
        if not card:
            failures.append(("unrecognized-card",code,source_name))
            continue
        expected=RARITY_CODES.get(card.get("rarity"))
        if rarity_code.upper()!=expected:
            failures.append(("rarity-conflict",code,rarity_code,expected))
            continue
        def norm(s):
            s=re.sub(r"\((?:ISecret|ILegend|IO|Rare|Secret|Epic|Uncommon|Common|a|b)\)","",s,flags=re.I)
            s=unicodedata.normalize("NFKD",s)
            return "".join(c for c in s.lower() if c.isascii() and c.isalnum())
        similarity=SequenceMatcher(None,norm(source_name),norm(card["name"])).ratio()
        if similarity<0.86:
            failures.append(("name-conflict",code,source_name,card["name"],round(similarity,3)))
            continue
        if code in results:
            failures.append(("duplicate",code))
            continue
        date=observed_date(day,month)
        href=link.get("href","")
        results[code]={"usd":float(usd),"name":card["name"],"source":"ValueMyCard — TCGplayer US market reference","sourceUrl":BASE+href,"observedDate":date,"printing":"Welcome to Night City Beta "+code+" "+card["rarity"]+" "+printing,"condition":"Ungraded market reference"}
expected_codes={code for code in catalog if code.startswith("B")}
missing=sorted(expected_codes-set(results))
if failures or missing or len(results)!=172:
    print("FAILURES",json.dumps(failures[:30],ensure_ascii=False),flush=True)
    print("MISSING",missing,flush=True)
    print("RESULTS",len(results),"EXPECTED",len(expected_codes),flush=True)
    raise SystemExit("Refusing incomplete or inconsistent price update")
data["observedDate"]=max(item["observedDate"] for item in results.values())
data["source"]="ValueMyCard — TCGplayer US market references for Welcome to Night City Beta"
data["sourceUrl"]=GUIDE
data["notes"]="172 Welcome to Night City Beta main-set prices, captured from displayed printings. Foil and normal are preserved per card. Historical market references, not live offers. Box Toppers are excluded."
data["prices"]={**{code:p for code,p in data["prices"].items() if not code.startswith("B")},**dict(sorted(results.items()))}
# Preserve dated observations, never invent a point for a day with no new source value.
history_path=Path("price-history.json")
history=json.loads(history_path.read_text()) if history_path.exists() else {
    "startDate":"2026-09-10","kind":"observed market price history (not individual transactions)","cards":{}
}
history.setdefault("cards",{})
for code,record in results.items():
    day=record["observedDate"]
    if day<history.get("startDate","2026-09-10"):
        continue
    series=history["cards"].setdefault(code,[])
    point={"date":day,"usd":record["usd"]}
    previous=next((p for p in series if p["date"]==day),None)
    if previous is None:
        series.append(point)
    elif previous["usd"]!=point["usd"]:
        previous["usd"]=point["usd"]
    series.sort(key=lambda p:p["date"])
history_path.write_text(json.dumps(history,ensure_ascii=False,indent=2)+"\n")
Path("prices.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
print("SUCCESS priced",len(results),"main-series cards; Box Toppers unchanged; range",min(v["usd"] for v in results.values()),max(v["usd"] for v in results.values()),flush=True)
