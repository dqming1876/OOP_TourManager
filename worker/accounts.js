function cookieValue(req,name){return (req.headers.get('Cookie')||'').match(new RegExp('(?:^|;\\s*)'+name+'=([^;]+)'))?.[1]}
async function passwordHash(password,salt){let key=await crypto.subtle.importKey('raw',enc.encode(password),'PBKDF2',false,['deriveBits']);let bytes=await crypto.subtle.deriveBits({name:'PBKDF2',salt:enc.encode(salt),iterations:100000,hash:'SHA-256'},key,256);return Array.from(new Uint8Array(bytes),x=>x.toString(16).padStart(2,'0')).join('')}
function publicAccount(a){return {id:a.id,name:a.name,username:a.username,role:'customer',email:a.email||'',phone:a.phone||'',address:a.address||'',birthday:a.birthday||''}}
async function currentAccount(req,env){if(await authenticated(req,env))return {id:'admin',name:'Quản trị viên',username:env.ADMIN_USERNAME,role:'admin'};let tok=cookieValue(req,'dv_user');if(!tok||!env.DB)return null;let [id,exp,sig]=tok.split('.');if(!id||!/^\d+$/.test(exp)||+exp<Date.now()||!equal(sig,await hmac(id+'.'+exp,env.ADMIN_SESSION_SECRET)))return null;let row=await env.DB.prepare('SELECT id,username,name,email,phone,address,birthday FROM accounts WHERE id=?').bind(id).first();return row?publicAccount(row):null}
const clearAdmin='dv_admin=; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=0',clearUser='dv_user=; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=0';
function withCookies(data,cookies,status=200){let r=json(data,status);for(let c of cookies)r.headers.append('Set-Cookie',c);return r}
async function accountsRoute(request,env){let url=new URL(request.url),path=url.pathname;if(path==='/api/auth/me'&&request.method==='GET')return json({user:await currentAccount(request,env)});
 if(!['/api/auth/login','/api/auth/register','/api/auth/logout','/api/profile'].includes(path))return json({error:'Không tìm thấy.'},404);
 if(request.method!=='POST')return json({error:'Phương thức không hợp lệ.'},405);if(request.headers.get('Origin')!==url.origin)return json({error:'Yêu cầu không hợp lệ.'},403);
 if(path==='/api/auth/logout')return withCookies({ok:true},[clearUser,clearAdmin]);
 let body;try{let raw=await request.text();if(raw.length>8192)return json({error:'Dữ liệu quá dài.'},413);body=JSON.parse(raw);if(!body||Array.isArray(body)||typeof body!=='object')throw new SyntaxError()}catch{return json({error:'Dữ liệu không hợp lệ.'},400)}
 if (path === '/api/profile') return saveCustomerProfile(request, env, body);
 let username=String(body.username||'').trim().toLowerCase(),password=body.password;if(typeof password!=='string'||password.length>128||!username)return json({error:'Vui lòng nhập tài khoản và mật khẩu.'},400);
 const ip=request.headers.get('CF-Connecting-IP')||'unknown',key='accounts:'+ip,now=Date.now();let attempt=attempts.get(key);if(!attempt||attempt.until<now){attempt={count:0,until:now+300000};attempts.set(key,attempt)}if(attempt.count>=12)return json({error:'Bạn đã thử quá nhiều lần. Vui lòng thử lại sau 5 phút.'},429);attempt.count++;
 if(path==='/api/auth/login'&&username===env.ADMIN_USERNAME?.toLowerCase()){if(!equal(password,env.ADMIN_PASSWORD))return json({error:'Tài khoản hoặc mật khẩu không đúng.'},401);let exp=String(now+8*3600000);attempts.delete(key);return withCookies({user:{id:'admin',username:env.ADMIN_USERNAME,name:'Quản trị viên',role:'admin'}},[clearUser,'dv_admin='+exp+'.'+await hmac(exp,env.ADMIN_SESSION_SECRET)+'; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=28800'])}
 if(!env.DB)return json({error:'Hệ thống tài khoản chưa sẵn sàng.'},503);
 if(path==='/api/auth/register'){let name=String(body.name||'').trim();if(!name||name.length>80||! /^[a-z0-9_]{3,32}$/.test(username)||password.length<6)return json({error:'Tên đăng nhập gồm 3–32 chữ không dấu, số hoặc dấu gạch dưới. Mật khẩu tối thiểu 6 ký tự.'},400);if(username===env.ADMIN_USERNAME?.toLowerCase())return json({error:'Tên đăng nhập đã được sử dụng.'},409);let existing=await env.DB.prepare('SELECT id FROM accounts WHERE username=?').bind(username).first();if(existing)return json({error:'Tên đăng nhập đã được sử dụng.'},409);let salt=crypto.randomUUID(),hash=await passwordHash(password,salt),id=crypto.randomUUID();try{await env.DB.prepare('INSERT INTO accounts (id,username,name,password_hash,salt) VALUES (?,?,?,?,?)').bind(id,username,name,hash,salt).run()}catch(e){if(String(e).includes('UNIQUE'))return json({error:'Tên đăng nhập đã được sử dụng.'},409);throw e}attempts.delete(key);return json({ok:true},201)}
 let row=await env.DB.prepare('SELECT * FROM accounts WHERE username=?').bind(username).first();let hash=await passwordHash(password,row?.salt||'dummy-login-salt');if(!row||!equal(hash,row.password_hash))return json({error:'Tài khoản hoặc mật khẩu không đúng.'},401);attempts.delete(key);let exp=String(now+8*3600000),v=row.id+'.'+exp;return withCookies({user:publicAccount(row)},[clearAdmin,'dv_user='+v+'.'+await hmac(v,env.ADMIN_SESSION_SECRET)+'; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=28800']);
}


async function saveCustomerProfile(request, env, body) {
  const user = await currentAccount(request, env);
  if (user?.role !== 'customer') return json({ error: 'Vui lòng đăng nhập tài khoản khách hàng.' }, 401);
  const profile = {};
  const limits = { name: 80, email: 120, phone: 20, address: 250, birthday: 10 };
  const labels = { name: 'Họ tên', email: 'Email', phone: 'Số điện thoại', address: 'Địa chỉ', birthday: 'Ngày sinh' };
  const invalid = field => json({ error: labels[field] + ' không hợp lệ.', field }, 400);
  for (const [field, limit] of Object.entries(limits)) {
    const value = body[field] ?? '';
    if (typeof value !== 'string' || value.trim().length > limit) return invalid(field);
    profile[field] = value.trim();
  }
  const { name, email, phone, address, birthday } = profile;
  if (!name) return invalid('name');
  if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return invalid('email');
  if (phone && (!/^[0-9+ ()-]+$/.test(phone) || phone.replace(/\D/g, '').length < 8)) return invalid('phone');
  if (birthday && !validCalendarDay(birthday)) return invalid('birthday');
  await env.DB.prepare('UPDATE accounts SET name=?,email=?,phone=?,address=?,birthday=? WHERE id=?')
    .bind(name, email, phone, address, birthday, user.id).run();
  return json({ user: { ...user, ...profile } });
}
