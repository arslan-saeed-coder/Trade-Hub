const API_BASE = window.TRADEHUB_API_URL || 'https://trade-hub-production.up.railway.app';
const getToken = () => localStorage.getItem('th_token');
const setToken = t => localStorage.setItem('th_token', t);
const clearAuth = () => { localStorage.removeItem('th_token'); localStorage.removeItem('th_session'); };
function authHeaders(){ const t=getToken(); return {'Content-Type':'application/json', ...(t?{Authorization:`Bearer ${t}`}:{})}; }
async function apiCall(method,path,body=null,requireAuth=false){
  const opts={method,headers:requireAuth?authHeaders():{'Content-Type':'application/json'}};
  if(body!==null && body!==undefined) opts.body=JSON.stringify(body);
  const res=await fetch(`${API_BASE}${path}`,opts);
  const data=await res.json().catch(()=>({}));
  if(!res.ok) throw new Error(data.detail || `Error ${res.status}`);
  return data;
}
const Auth={
  async register(name,email,password,phone){ const d=await apiCall('POST','/api/auth/register',{name,email,password,phone,role:'customer'}); setToken(d.token); localStorage.setItem('th_session',JSON.stringify(d.user)); return d; },
  async login(email,password){ const d=await apiCall('POST','/api/auth/login',{email,password}); setToken(d.token); localStorage.setItem('th_session',JSON.stringify(d.user)); return d; },
  async me(){ return apiCall('GET','/api/auth/me',null,true); },
  getSession(){ return JSON.parse(localStorage.getItem('th_session')||'null'); },
  isLoggedIn(){ return !!getToken(); },
  isAdmin(){ const u=this.getSession(); return !!u && u.role==='admin'; },
  logout(){ clearAuth(); window.location.href=window.location.pathname.includes('/admin/')?'../index.html':(window.location.pathname.includes('/pages/')?'../index.html':'index.html'); }
};
const Products={
  async list(params={}){ const q=new URLSearchParams(Object.entries(params).filter(([,v])=>v!==''&&v!==null&&v!==undefined)); return apiCall('GET',`/api/products?${q}`); },
  async get(id){ return apiCall('GET',`/api/products/${id}`); },
  async create(payload){ return apiCall('POST','/api/products',payload,true); },
  async update(id,payload){ return apiCall('PUT',`/api/products/${id}`,payload,true); },
  async delete(id){ return apiCall('DELETE',`/api/products/${id}`,null,true); }
};
const Orders={
  async create(payload){ return apiCall('POST','/api/orders',payload,true); },
  async list(params={}){ const q=new URLSearchParams(Object.entries(params).filter(([,v])=>v)); return apiCall('GET',`/api/orders?${q}`,null,true); },
  async setStatus(id,status){ return apiCall('PATCH',`/api/orders/${id}/status`,{status},true); },
  async delete(id){ return apiCall('DELETE',`/api/orders/${id}`,null,true); }
};
const Stats={ public:()=>apiCall('GET','/api/stats'), admin:()=>apiCall('GET','/api/admin/stats',null,true) };
const Categories={ list:()=>apiCall('GET','/api/categories') };
function showToast(msg,type='success'){
  let stack=document.getElementById('toastStack'); if(!stack){stack=document.createElement('div');stack.id='toastStack';stack.className='toast-stack';document.body.appendChild(stack);}
  const t=document.createElement('div'); t.className=`toast toast-${type}`; t.textContent=msg; stack.appendChild(t); setTimeout(()=>t.remove(),3600);
}
document.addEventListener('DOMContentLoaded',async()=>{ const token=getToken(); if(token && !Auth.getSession()){ try{ const u=await Auth.me(); localStorage.setItem('th_session',JSON.stringify(u)); }catch{ clearAuth(); } } });
