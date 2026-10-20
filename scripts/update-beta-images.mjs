const collectionUrl='https://spellboundgames.co.uk/collections/cyberpunk-singles/products.json?limit=250';
const base='https://spellboundgames.co.uk';
const res=await fetch(collectionUrl,{signal:AbortSignal.timeout(20000),headers:{'User-Agent':'Mozilla/5.0 (CYBERSCAN Beta image index)' }});
if(!res.ok)throw Error('Shopify collection HTTP '+res.status);
const data=await res.json();
if(!Array.isArray(data.products))throw Error('Missing Shopify products array');
const images={};
const duplicates=[];
for(const p of data.products){
  const label=[p.title,p.handle].join(' ');
  const match=label.match(/\bB(\d{3}[AB]?)\b/i);
  if(!match)continue;
  const code='B'+match[1].toUpperCase();
  const number=Number(match[1].slice(0,3));
  if(number<1||number>171)continue;
  const url=p.images?.[0]?.src||p.image?.src;
  if(!url||!url.startsWith('https://cdn.shopify.com/'))continue;
  if(images[code]){duplicates.push(code);continue}
  images[code]={url,title:p.title,sourceUrl:base+'/products/'+p.handle};
}
if(!images.B135||Object.keys(images).length<140)throw Error('Incomplete or missing B135: '+Object.keys(images).length);
const results=await Promise.all(Object.entries(images).map(async ([code,item])=>{
  try{const resp=await fetch(item.url,{method:'HEAD',signal:AbortSignal.timeout(10000)});return [code,resp.ok&&String(resp.headers.get('content-type')).startsWith('image/')]}
  catch{return [code,false]}
}));
for(const [code,good]of results)if(!good)delete images[code];
if(!images.B135||Object.keys(images).length<140)throw Error('Images failed verification: '+Object.keys(images).length);
const fs=await import('node:fs');
const payload={version:1,source:'Spellbound Games public Beta Singles Shopify product images',sourceUrl:'https://spellboundgames.co.uk/collections/cyberpunk-singles',notes:'Externally hosted product photos, not an official card image license. Images belong to their respective owners. No copies are stored in this repository.',images:Object.fromEntries(Object.entries(images).sort(([a],[b])=>a.localeCompare(b,undefined,{numeric:true})))};
fs.writeFileSync('card-images.json',JSON.stringify(payload,null,2)+'\n');
console.log('TOTAL PRODUCTS',data.products.length,'IMAGE MATCHES',Object.keys(images).length,'DUPLICATES',duplicates.length,'B135',JSON.stringify(images.B135));
