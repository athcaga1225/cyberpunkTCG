import requests
from bs4 import BeautifulSoup
base="https://holohoard.app"
for slug in ["the-heist-beta-starter-deck","embracing-power-beta-starter-deck","the-heist-beta","embracing-power-beta"]:
 url=f"{base}/explore/game/cyberpunk-tcg/{slug}"
 try:
  r=requests.get(url,timeout=20,headers={"User-Agent":"Mozilla/5.0"})
  soup=BeautifulSoup(r.text,"html.parser")
  imgs=[(x.get("alt"),x.get("src")) for x in soup.find_all("img") if "cards/cyberpunk" in str(x.get("src"))]
  cardlinks=[(x.get_text(" ",strip=True)[:55],x.get("href")) for x in soup.find_all("a",href=True) if "/card-" in x.get("href")]
  print("PAGE",slug,r.status_code,len(r.content),"TITLE",str(soup.title.get_text() if soup.title else "")[:100],"IMGS",imgs[:4],"LINKS",cardlinks[:5],flush=True)
 except Exception as e:print("ERROR",slug,str(e))
