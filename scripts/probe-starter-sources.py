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

for slug in ["the-heist-beta-starter-deck","embracing-power-beta-starter-deck"]:
 url=f"{base}/explore/game/cyberpunk-tcg/{slug}"
 soup=BeautifulSoup(requests.get(url,timeout=25,headers={"User-Agent":"Mozilla/5.0"}).text,"html.parser")
 print("SET",slug,"IMAGES",len([x for x in soup.find_all('img') if "/api/img/cards/cyberpunk-tcg/"+slug+"/webp/" in str(x.get('src'))]))
 for i,x in enumerate([x for x in soup.find_all('img') if "/api/img/cards/cyberpunk-tcg/"+slug+"/webp/" in str(x.get('src'))][:22]):
  print("ITEM",slug,i,x.get("alt"),x.get("src"),"PARENT",x.parent.parent.get_text(" ",strip=True)[:120])
 print("SET_TEXT",slug,soup.get_text(" ",strip=True)[150:900])

import json,concurrent.futures
data=json.loads(open("starter-catalog.json").read())
def check(item):
 code,card,deck=item
 try:
  res=requests.get(card["imageUrl"],timeout=15,headers={"User-Agent":"Mozilla/5.0"})
  return (deck,code,res.status_code,res.headers.get("content-type"),len(res.content))
 except Exception as e:return (deck,code,"ERROR",str(e),0)
items=[(code,card,deck) for deck,info in data["sets"].items() for code,card in info["cards"].items() if card.get("imageUrl")]
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
 results=list(pool.map(check,items))
bad=[x for x in results if x[2]!=200 or not str(x[3]).startswith("image/") or x[4]<3000]
print("STARTER_IMAGE_TEST",len(results),"GOOD",len(results)-len(bad),"BAD",bad,"B018_DECLARED_NO_IMAGE",data["sets"]["heist"]["cards"]["B018"].get("imageUrl") is None,flush=True)
if len(results)!=39 or data["sets"]["heist"]["cards"]["B018"].get("imageUrl") is not None:raise SystemExit("Unexpected starter image manifest")
if bad:raise SystemExit(1)
