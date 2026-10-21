#!/usr/bin/env python3
"""Import dated, publicly displayed market reference observations (not sales)."""
import json, re, time, datetime
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

START="2026-09-10"
prices=json.loads(Path("prices.json").read_text())["prices"]
history_path=Path("price-history.json")
history=json.loads(history_path.read_text())
history.setdefault("cards",{})
session=requests.Session()
session.headers["User-Agent"]="Mozilla/5.0 (CYBERSCAN personal collection price-history import)"
month_map={m:i for i,m in enumerate(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],1)}
date_pattern=re.compile(r"^\s*(\d{1,2})\s+([A-Za-z]{3,9})\s+(20\d\d)\s*$")
money_pattern=re.compile(r"^\s*\$?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)\s*$")
failures=[]
imported=0
for n,(code,item) in enumerate(sorted(prices.items()),1):
    if not code.startswith("B"):continue
    url=item.get("sourceUrl","")
    parsed=urlparse(url)
    if parsed.scheme!="https" or parsed.netloc!="valuemycard.com" or not parsed.path.startswith("/card/"):
        failures.append((code,"invalid-source-url"));continue
    try:
        response=session.get(url,timeout=20)
        response.raise_for_status()
        soup=BeautifulSoup(response.text,"html.parser")
        table=None
        for candidate in soup.select("table"):
            headings=[th.get_text(" ",strip=True).lower() for th in candidate.select("th")]
            if any("date" in h for h in headings) and any("market price" in h for h in headings):
                table=candidate;break
        if table is None:
            failures.append((code,"history-table-missing"));continue
        fresh=[]
        for row in table.select("tr"):
            columns=[td.get_text(" ",strip=True) for td in row.select("td")]
            if len(columns)<2:continue
            dm=date_pattern.fullmatch(columns[0])
            pm=money_pattern.fullmatch(columns[1])
            if not dm or not pm:continue
            day,month,year=dm.groups()
            month_no=month_map.get(month[:3].title())
            if not month_no:continue
            iso=datetime.date(int(year),month_no,int(day)).isoformat()
            value=float(pm.group(1).replace(",",""))
            if iso>=START and value>0:
                fresh.append({"date":iso,"usd":value})
        if not fresh:
            failures.append((code,"no-valid-history"));continue
        existing={p["date"]:p for p in history["cards"].get(code,[]) if p["date"]>=START}
        for point in fresh:
            existing[point["date"]]=point
        history["cards"][code]=[existing[k] for k in sorted(existing)]
        imported+=1
        print(f"{n}/172 {code}: {len(fresh)} source observations",flush=True)
    except (requests.RequestException, ValueError, KeyError) as exc:
        failures.append((code,str(exc)[:160]))
    time.sleep(0.35)
history["startDate"]=START
history["kind"]="observed market price history (not individual sales)"
history["notes"]="Only dates and prices published by the card's market-reference page; no interpolated data. Before 2026-09-10 excluded."
if imported:
    history_path.write_text(json.dumps(history,ensure_ascii=False,indent=2)+"\n")
print("Imported",imported,"of",len([x for x in prices if x.startswith("B")]),"cards. Unavailable:",json.dumps(failures,ensure_ascii=False),flush=True)
if imported<150:
    raise SystemExit("Insufficient coverage: refusing to publish bulk backfill")
