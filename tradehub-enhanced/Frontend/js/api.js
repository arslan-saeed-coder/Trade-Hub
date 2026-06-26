// ===== TRADEHUB PK — API CLIENT =====
// Single source of truth for all backend calls.
// Set VITE_API_URL in Vercel environment variables.

const API_BASE = window.TRADEHUB_API_URL || 'https://your-backend.railway.app';

// ---- Token helpers ----
const getToken  = ()        => localStorage.getItem('th_token');
const setToken  = (t)       => localStorage.setItem('th_token', t);
const clearAuth = ()        => { localStorage.removeItem('th_token'); localStorage.removeItem('th_session'); };

function authHeaders() {
  const t = getToken();
  return t ? { 'Authorization': `Bearer ${t}`, 'Content-Type': 'application/json' }
           : { 'Content-Type': 'application/json' };
}

async function apiCall(method, path, body = null, requireAuth = false) {
  const opts = { method, headers: requireAuth ? authHeaders() : { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  try {
    const res = await fetch(`${API_BASE}${path}`, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
    return data;
  } catch (err) {
    console.error(`API ${method} ${path}:`, err.message);
    throw err;
  }
}

// ===== AUTH =====
const Auth = {
  async register(name, email, password, phone, role = 'buyer') {
    const data = await apiCall('POST', '/api/auth/register', { name, email, password, phone, role });
    setToken(data.token);
    localStorage.setItem('th_session', JSON.stringify(data.user));
    return data;
  },
  async login(email, password) {
    const data = await apiCall('POST', '/api/auth/login', { email, password });
    setToken(data.token);
    localStorage.setItem('th_session', JSON.stringify(data.user));
    return data;
  },
  async me() {
    return apiCall('GET', '/api/auth/me', null, true);
  },
  logout() {
    clearAuth();
    window.location.href = window.location.pathname.includes('/pages/') ? '../index.html' : 'index.html';
  },
  getSession() {
    return JSON.parse(localStorage.getItem('th_session') || 'null');
  },
  isLoggedIn() {
    return !!getToken();
  },
};

// ===== SUPPLIERS =====
const Suppliers = {
  async list(params = {}) {
    const q = new URLSearchParams(Object.entries(params).filter(([,v]) => v !== null && v !== undefined));
    return apiCall('GET', `/api/suppliers?${q}`);
  },
  async get(id) {
    return apiCall('GET', `/api/suppliers/${id}`);
  },
  async create(payload) {
    return apiCall('POST', '/api/suppliers', payload, true);
  },
  async update(id, payload) {
    return apiCall('PUT', `/api/suppliers/${id}`, payload, true);
  },
  async delete(id) {
    return apiCall('DELETE', `/api/suppliers/${id}`, null, true);
  },
  async approve(id) {
    return apiCall('PATCH', `/api/admin/suppliers/${id}/approve`, null, true);
  },
  async reject(id) {
    return apiCall('PATCH', `/api/admin/suppliers/${id}/reject`, null, true);
  },
  async verify(id, verified = true, score = 90) {
    return apiCall('PATCH', `/api/admin/suppliers/${id}/verify`, { verified, score }, true);
  },
  async feature(id, featured = true) {
    return apiCall('PATCH', `/api/admin/suppliers/${id}/feature`, { featured }, true);
  },
  async dashboard(id) {
    return apiCall('GET', `/api/supplier-dashboard/${id}`, null, true);
  },
};

// ===== PRODUCTS =====
const Products = {
  async list(params = {}) {
    const q = new URLSearchParams(Object.entries(params).filter(([,v]) => v !== null && v !== undefined));
    return apiCall('GET', `/api/products?${q}`);
  },
  async get(id)          { return apiCall('GET', `/api/products/${id}`); },
  async create(payload)  { return apiCall('POST', '/api/products', payload, true); },
  async update(id, payload) { return apiCall('PUT', `/api/products/${id}`, payload, true); },
  async delete(id)       { return apiCall('DELETE', `/api/products/${id}`, null, true); },
};

// ===== INQUIRIES =====
const Inquiries = {
  async send(supplier_id, buyer_name, buyer_email, message, quantity, budget) {
    return apiCall('POST', '/api/inquiries', { supplier_id, buyer_name, buyer_email, message, quantity, budget });
  },
  async list(params = {}) {
    const q = new URLSearchParams(Object.entries(params).filter(([,v]) => v));
    return apiCall('GET', `/api/inquiries?${q}`, null, true);
  },
};

// ===== RFQs =====
const RFQs = {
  async submit(payload) { return apiCall('POST', '/api/rfqs', payload); },
  async list(params={}) {
    const q = new URLSearchParams(Object.entries(params).filter(([,v]) => v));
    return apiCall('GET', `/api/rfqs?${q}`);
  },
};

// ===== REVIEWS =====
const Reviews = {
  async submit(supplier_id, reviewer_name, rating, comment) {
    return apiCall('POST', '/api/reviews', { supplier_id, reviewer_name, rating, comment });
  },
  async list(supplier_id) { return apiCall('GET', `/api/reviews/${supplier_id}`); },
};

// ===== FAVORITES =====
const Favorites = {
  async add(user_email, item_type, item_id)  { return apiCall('POST', '/api/favorites', { user_email, item_type, item_id }); },
  async list(user_email)                      { return apiCall('GET', `/api/favorites?user_email=${encodeURIComponent(user_email)}`); },
  async remove(id)                            { return apiCall('DELETE', `/api/favorites/${id}`); },
};

// ===== SEARCH =====
const Search = {
  async query(q, category) {
    const params = new URLSearchParams({ q });
    if (category) params.append('category', category);
    return apiCall('GET', `/api/search?${params}`);
  },
};

// ===== STATS =====
const Stats = {
  async public()  { return apiCall('GET', '/api/stats'); },
  async admin()   { return apiCall('GET', '/api/admin/stats', null, true); },
};

// ===== ADMIN =====
const Admin = {
  async users()                 { return apiCall('GET', '/api/admin/users', null, true); },
  async setUserStatus(id, status) { return apiCall('PATCH', `/api/admin/users/${id}/status`, status, true); },
};

// ===== CATEGORIES =====
const Categories = { async list() { return apiCall('GET', '/api/categories'); } };

// ===== PLANS =====
const Plans = { async list() { return apiCall('GET', '/api/subscription-plans'); } };

// ===== UI HELPERS =====
function showToast(msg, type = 'success') {
  let stack = document.getElementById('toastStack');
  if (!stack) { stack = document.createElement('div'); stack.id = 'toastStack'; stack.className = 'toast-stack'; document.body.appendChild(stack); }
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.textContent = msg;
  stack.appendChild(t);
  setTimeout(() => t.remove(), 3200);
}

function handleApiError(err, fallbackMsg = 'Something went wrong.') {
  showToast(err?.message || fallbackMsg, 'error');
}

// Auto-restore session from token on page load
document.addEventListener('DOMContentLoaded', async () => {
  const token = getToken();
  const session = Auth.getSession();
  if (token && !session) {
    try {
      const user = await Auth.me();
      localStorage.setItem('th_session', JSON.stringify(user));
    } catch {
      clearAuth(); // token expired
    }
  }
});
