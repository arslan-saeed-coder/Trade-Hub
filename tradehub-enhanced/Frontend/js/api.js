// ===== MY STORE — API CLIENT =====
// Single source of truth for all backend calls.

const API_BASE = window.TRADEHUB_API_URL || 'https://trade-hub-production.up.railway.app';

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
  async register(name, email, password, phone) {
    const data = await apiCall('POST', '/api/auth/register', { name, email, password, phone });
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
  isAdmin() {
    const s = Auth.getSession();
    return !!s && s.role === 'admin';
  },
};

// ===== STORE =====
const Store = {
  async info() { return apiCall('GET', '/api/store'); },
};

// ===== PRODUCTS =====
const Products = {
  async list(params = {}) {
    const q = new URLSearchParams(Object.entries(params).filter(([,v]) => v !== null && v !== undefined && v !== ''));
    return apiCall('GET', `/api/products?${q}`);
  },
  async get(id)             { return apiCall('GET', `/api/products/${id}`); },
  async create(payload)     { return apiCall('POST', '/api/products', payload, true); },
  async update(id, payload) { return apiCall('PUT', `/api/products/${id}`, payload, true); },
  async delete(id)          { return apiCall('DELETE', `/api/products/${id}`, null, true); },
};

// ===== ORDERS =====
const Orders = {
  async create(payload) { return apiCall('POST', '/api/orders', payload, false); },
  async list(params = {}) {
    const q = new URLSearchParams(Object.entries(params).filter(([,v]) => v));
    return apiCall('GET', `/api/orders?${q}`, null, true);
  },
  async my() { return apiCall('GET', '/api/orders/my', null, true); },
  async get(id) { return apiCall('GET', `/api/orders/${id}`, null, true); },
  async updateStatus(id, status) { return apiCall('PATCH', `/api/orders/${id}/status`, { status }, true); },
  async delete(id) { return apiCall('DELETE', `/api/orders/${id}`, null, true); },
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

// ===== CATEGORIES =====
const Categories = { async list() { return apiCall('GET', '/api/categories'); } };

// ===== WHATSAPP =====
// Set your store's WhatsApp number (with country code, no + or spaces) here.
window.STORE_WHATSAPP_NUMBER = window.STORE_WHATSAPP_NUMBER || '923000000000';

function buildWhatsAppOrderUrl(order) {
  const lines = [
    'Hello, I have placed an order.',
    '',
    `Order ID: ${order.order_number}`,
    `Product: ${order.product_name}`,
    `Quantity: ${order.quantity}`,
    `Total: PKR ${order.total_price}`,
    `My Name: ${order.customer_name}`,
    '',
    'Please confirm my order.',
  ];
  const text = encodeURIComponent(lines.join('\n'));
  return `https://wa.me/${window.STORE_WHATSAPP_NUMBER}?text=${text}`;
}

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
