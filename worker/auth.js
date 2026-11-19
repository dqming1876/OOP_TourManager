const enc=new TextEncoder();
const json=(data,status=200,headers={})=>new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json','Cache-Control':'no-store',...headers}});
async function hmac(value,secret){const key=await crypto.subtle.importKey('raw',enc.encode(secret),{name:'HMAC',hash:'SHA-256'},false,['sign']);return Array.from(new Uint8Array(await crypto.subtle.sign('HMAC',key,enc.encode(value))),x=>x.toString(16).padStart(2,'0')).join('')}
function equal(a,b){if(typeof a!=='string'||typeof b!=='string')return false;let n=a.length^b.length;for(let i=0;i<Math.max(a.length,b.length);i++)n|=(a.charCodeAt(i)||0)^(b.charCodeAt(i)||0);return n===0}
export async function authenticated(request,env){try{if(!env.ADMIN_SESSION_SECRET)return false;let c=request.headers.get('Cookie')||'',token=c.match(/(?:^|;\s*)dv_admin=([^;]+)/)?.[1];if(!token)return false;let [expiry,signature]=token.split('.');if(!/^\d+$/.test(expiry)||+expiry<Date.now()||+expiry>Date.now()+9*3600000)return false;return equal(signature,await hmac(expiry,env.ADMIN_SESSION_SECRET))}catch{return false}}
const attempts=new Map();
export async function authRoute(request,env){const url=new URL(request.url),path=url.pathname;
 if(path==='/api/admin/session')return json({authenticated:await authenticated(request,env)});
 if(!['/api/admin/login','/api/admin/logout'].includes(path))return json({error:'Not found'},404);
 if(request.method!=='POST')return json({error:'Method not allowed'},405);
 if(request.headers.get('Origin')!==url.origin)return json({error:'Forbidden'},403);
 if(path.endsWith('/logout'))return json({ok:true},200,{'Set-Cookie':'dv_admin=; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=0'});
 if(!env.ADMIN_USERNAME||!env.ADMIN_PASSWORD||!env.ADMIN_SESSION_SECRET)return json({error:'Not configured'},503);
 const ip=request.headers.get('CF-Connecting-IP')||'unknown',now=Date.now();let a=attempts.get(ip);if(!a||a.until<now){a={count:0,until:now+300000};attempts.set(ip,a)}if(a.count>=8)return json({error:'Too many attempts'},429);
 let body;try{if(+(request.headers.get('Content-Length')||0)>2048)return json({error:'Too large'},413);body=await request.json()}catch{return json({error:'Invalid request'},400)}
 a.count++;if(!equal(body.username,env.ADMIN_USERNAME)||!equal(body.password,env.ADMIN_PASSWORD))return json({error:'Invalid credentials'},401);
 attempts.delete(ip);let exp=String(now+8*3600000),token=exp+'.'+await hmac(exp,env.ADMIN_SESSION_SECRET);return json({ok:true},200,{'Set-Cookie':'dv_admin='+token+'; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=28800'});
}
