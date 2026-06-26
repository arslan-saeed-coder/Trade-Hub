// ===== TRADEHUB PK — MAIN JS =====

const SUPPLIERS = [
  { id: 1, name: 'Al-Hamza Textiles', initial: 'AH', category: 'Textiles', location: 'Faisalabad', moq: '500 meters', wa: '923001234567', verified: true },
  { id: 2, name: 'Pak Steel Works', initial: 'PS', category: 'Hardware', location: 'Lahore', moq: '100 kg', wa: '923011234567', verified: true },
  { id: 3, name: 'Green Farm Exports', initial: 'GF', category: 'Agriculture', location: 'Multan', moq: '1 Ton', wa: '923021234567', verified: true },
  { id: 4, name: 'Sialkot Sports Co.', initial: 'SS', category: 'Sports', location: 'Sialkot', moq: '50 pcs', wa: '923031234567', verified: true },
  { id: 5, name: 'Karachi Leather House', initial: 'KL', category: 'Leather', location: 'Karachi', moq: '200 pcs', wa: '923041234567', verified: false },
  { id: 6, name: 'Punjab Rice Mills', initial: 'PR', category: 'Food & Grain', location: 'Sheikhupura', moq: '5 Ton', wa: '923051234567', verified: true },
];

const PRODUCTS = [
  { id: 1, name: 'Basmati Rice Premium Grade', emoji: '🍚', price: 'PKR 2,800', unit: '/50kg bag', supplier: 'Punjab Rice Mills', category: 'Food & Grain', moq: 'Min 5 Ton' },
  { id: 2, name: 'Cotton Fabric (Plain Weave)', emoji: '👕', price: 'PKR 180', unit: '/meter', supplier: 'Al-Hamza Textiles', category: 'Textiles', moq: 'Min 500 m' },
  { id: 3, name: 'MS Steel Bars 12mm', emoji: '🔩', price: 'PKR 1,950', unit: '/kg', supplier: 'Pak Steel Works', category: 'Hardware', moq: 'Min 100 kg' },
  { id: 4, name: 'Football (Match Grade)', emoji: '⚽', price: 'PKR 450', unit: '/piece', supplier: 'Sialkot Sports Co.', category: 'Sports', moq: 'Min 50 pcs' },
  { id: 5, name: 'Leather Wallet (Handmade)', emoji: '👜', price: 'PKR 320', unit: '/piece', supplier: 'Karachi Leather House', category: 'Leather', moq: 'Min 200 pcs' },
  { id: 6, name: 'Wheat Flour (Grade A)', emoji: '🌾', price: 'PKR 1,100', unit: '/40kg bag', supplier: 'Green Farm Exports', category: 'Agriculture', moq: 'Min 1 Ton' },
  { id: 7, name: 'PVC Pipe 2-inch', emoji: '🔧', price: 'PKR 850', unit: '/length', supplier: 'Pak Steel Works', category: 'Hardware', moq: 'Min 200 pcs' },
  { id: 8, name: 'Polyester Yarn 30/1', emoji: '🧵', price: 'PKR 950', unit: '/kg', supplier: 'Al-Hamza Textiles', category: 'Textiles', moq: 'Min 1 Ton' },
];

function doSearch() {
  const q = document.getElementById('searchInput')?.value.trim();
  if (q) window.location.href = `pages/products.html?q=${encodeURIComponent(q)}`;
}
document.getElementById('searchInput')?.addEventListener('keydown', e => {
  if (e.key === 'Enter') doSearch();
});

function renderSuppliers() {
  const grid = document.getElementById('suppliersGrid');
  if (!grid) return;
  grid.innerHTML = SUPPLIERS.slice(0, 6).map(s => `
    <div class="supplier-card">
      <div class="supplier-card-top">
        <div class="supplier-logo">${s.initial}</div>
        <div>
          <div class="supplier-name">${s.name} ${s.verified ? '✅' : ''}</div>
          <span class="supplier-category">${s.category}</span>
        </div>
      </div>
      <div class="supplier-meta">
        <div class="supplier-meta-row"><span>📍</span> ${s.location}</div>
        <div class="supplier-meta-row"><span>📦</span> MOQ: ${s.moq}</div>
      </div>
      <div class="supplier-actions">
        <a href="pages/supplier-detail.html?id=${s.id}" class="btn-contact">View Profile</a>
        <a href="https://wa.me/${s.wa}" target="_blank" class="btn-wa">💬</a>
      </div>
    </div>
  `).join('');
}

function renderProducts() {
  const grid = document.getElementById('productsGrid');
  if (!grid) return;
  grid.innerHTML = PRODUCTS.slice(0, 8).map(p => `
    <div class="product-card">
      <div class="product-img">${p.emoji}</div>
      <div class="product-body">
        <div class="product-price">${p.price} <small>${p.unit}</small></div>
        <div class="product-name">${p.name}</div>
        <div class="product-supplier">by ${p.supplier}</div>
        <div class="product-moq">${p.moq}</div>
        <button class="btn-inquiry" onclick="sendInquiry(this)" data-name="${p.name.replace(/"/g,'&quot;')}">Send Inquiry</button>
      </div>
    </div>
  `).join('');
}

function openModal(tab) {
  document.getElementById('authModal').classList.add('show');
  switchTab(tab || 'login');
}
function closeModal() {
  document.getElementById('authModal').classList.remove('show');
}
function switchTab(tab) {
  const isLogin = tab === 'login';
  document.getElementById('loginForm').style.display = isLogin ? 'block' : 'none';
  document.getElementById('registerForm').style.display = isLogin ? 'none' : 'block';
  document.getElementById('tabLogin').classList.toggle('active', isLogin);
  document.getElementById('tabRegister').classList.toggle('active', !isLogin);
  document.getElementById('modalTitle').textContent = isLogin ? 'Welcome back' : 'Create account';
}
function handleLogin() {
  const email = document.getElementById('loginEmail').value.trim();
  const pass = document.getElementById('loginPass').value;
  if (!email || !pass) { showToast('Please fill all fields.', 'error'); return; }
  const saved = JSON.parse(localStorage.getItem('th_user') || 'null');
  if (saved && saved.email === email) {
    localStorage.setItem('th_session', JSON.stringify(saved));
    closeModal();
    showToast(`Welcome back, ${saved.name}!`, 'success');
    updateNavForUser(saved);
  } else {
    showToast('Invalid credentials. Please register first.', 'error');
  }
}
function handleRegister() {
  const name = document.getElementById('regName').value.trim();
  const email = document.getElementById('regEmail').value.trim();
  const phone = document.getElementById('regPhone').value.trim();
  const pass = document.getElementById('regPass').value;
  if (!name || !email || !phone || !pass) { showToast('Please fill all fields.', 'error'); return; }
  const user = { name, email, phone, savedSuppliers: [], inquiries: [] };
  localStorage.setItem('th_user', JSON.stringify(user));
  localStorage.setItem('th_session', JSON.stringify(user));
  closeModal();
  showToast(`Account created! Welcome, ${name}!`, 'success');
  updateNavForUser(user);
}
function updateNavForUser(user) {
  const actions = document.querySelector('.nav-actions');
  if (actions) {
    actions.innerHTML = `
      <a href="pages/buyer-dashboard.html" class="btn-login">My Account</a>
      <button class="btn-register" onclick="logout()">Logout</button>
    `;
  }
}
function logout() {
  localStorage.removeItem('th_session');
  location.reload();
}
function sendInquiry(el) {
  const productName = typeof el === 'string' ? el : el.getAttribute('data-name');
  const session = JSON.parse(localStorage.getItem('th_session') || 'null');
  if (!session) { openModal('login'); showToast('Please login to send inquiries.', 'error'); return; }
  showToast(`Inquiry sent for "${productName}"!`, 'success');
}
function showToast(msg, type = 'success') {
  const stack = document.getElementById('toastStack');
  if (!stack) return;
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.textContent = msg;
  stack.appendChild(t);
  setTimeout(() => t.remove(), 3100);
}

document.querySelectorAll('.nav-links a').forEach(link => {
  if (link.href === window.location.href) link.style.color = '#059669';
});

document.addEventListener('DOMContentLoaded', () => {
  renderSuppliers();
  renderProducts();
  const session = JSON.parse(localStorage.getItem('th_session') || 'null');
  if (session) updateNavForUser(session);
  document.getElementById('authModal')?.addEventListener('click', function(e) {
    if (e.target === this) closeModal();
  });
});
