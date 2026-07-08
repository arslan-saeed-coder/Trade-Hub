// ===== MY STORE — ADMIN PANEL JS =====

let editingProductId = null;
let ALL_PRODUCTS = [];
let ALL_ORDERS = [];

const STATUS_OPTIONS = ["Pending","Confirmed","Processing","Shipped","Delivered","Cancelled"];

function spawnParticles() {
  const container = document.getElementById('particles');
  if (!container) return;
  const colors = ['#00ff88','#00e5ff','#a855f7','#ff0080','#ff6600','#ffd700'];
  for (let i = 0; i < 35; i++) {
    const p = document.createElement('div');
    p.className = 'particle';
    const size = Math.random() * 3 + 1;
    p.style.cssText = `
      left:${Math.random()*100}%;
      width:${size}px; height:${size}px;
      background:${colors[Math.floor(Math.random()*colors.length)]};
      animation-duration:${Math.random()*12+8}s;
      animation-delay:${Math.random()*10}s;
      box-shadow:0 0 6px currentColor;
    `;
    container.appendChild(p);
  }
}

function showPage(id, el) {
  document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.sidebar-item').forEach(i => i.classList.remove('active'));
  document.getElementById('page-'+id).classList.add('active');
  if (el) el.classList.add('active');
  const titles = {dashboard:'Dashboard', products:'Product Catalog', orders:'Order Management'};
  const titleEl = document.getElementById('topbarTitle');
  if (titleEl) titleEl.textContent = titles[id] || id;
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

function searchTable(tableId, query) {
  const q = query.toLowerCase();
  const rows = document.querySelectorAll(`#${tableId} tbody tr`);
  rows.forEach(row => {
    const text = row.textContent.toLowerCase();
    row.style.display = text.includes(q) ? '' : 'none';
  });
}

// ---- Auth gate ----
async function adminLogin(){
  const email = document.getElementById('loginEmail').value.trim();
  const pass = document.getElementById('loginPass').value;
  const errEl = document.getElementById('loginError');
  errEl.style.display = 'none';
  if (!email || !pass) { errEl.textContent = 'Please enter email and password.'; errEl.style.display='block'; return; }
  const btn = document.getElementById('loginBtn');
  btn.disabled = true; btn.textContent = 'Signing in…';
  try {
    const data = await Auth.login(email, pass);
    if (data.user.role !== 'admin') {
      Auth.logout ? clearAuth() : null;
      errEl.textContent = 'This account does not have admin access.';
      errEl.style.display = 'block';
      return;
    }
    enterAdmin(data.user);
  } catch(err){
    errEl.textContent = err.message || 'Login failed.';
    errEl.style.display = 'block';
  } finally {
    btn.disabled = false; btn.textContent = 'Login';
  }
}

function enterAdmin(user){
  document.getElementById('loginScreen').classList.add('hidden');
  document.getElementById('adminLayout').classList.remove('hidden');
  document.getElementById('adminNameTag').textContent = user.name || 'Admin';
  loadAll();
}

function adminLogout() {
  if (confirm('Logout from admin panel?')) {
    clearAuth();
    window.location.href = '../index.html';
  }
}

async function loadAll(){
  await Promise.all([loadStats(), loadProducts(), loadOrders()]);
}

// ---- Dashboard ----
async function loadStats(){
  try {
    const s = await Stats.admin();
    document.getElementById('stat-products').textContent = s.total_products;
    document.getElementById('stat-orders').textContent = s.total_orders;
    document.getElementById('stat-today-sub').textContent = `${s.today_orders} today`;
    document.getElementById('stat-pending-orders').textContent = s.pending_orders;
    document.getElementById('stat-monthly-sales').textContent = `PKR ${s.monthly_sales.toLocaleString()}`;
    document.getElementById('stat-confirmed').textContent = s.confirmed_orders;
    document.getElementById('stat-processing').textContent = s.processing_orders;
    document.getElementById('stat-shipped').textContent = s.shipped_orders;
    document.getElementById('stat-delivered').textContent = s.delivered_orders;
    document.getElementById('pending-badge').textContent = s.pending_orders;
  } catch(err){
    showToast('Could not load stats: ' + err.message, 'error');
  }
}

function renderRecentOrders(){
  const body = document.getElementById('recentOrdersBody');
  const recent = ALL_ORDERS.slice(0, 6);
  if (!recent.length){ body.innerHTML = `<tr><td colspan="5" style="color:var(--text-muted)">No orders yet.</td></tr>`; return; }
  body.innerHTML = recent.map(o => `
    <tr>
      <td><strong>${o.order_number}</strong></td>
      <td>${o.customer_name}</td>
      <td>${o.product_name}</td>
      <td>PKR ${o.total_price.toLocaleString()}</td>
      <td><span class="pill ${pillClass(o.status)}">${o.status}</span></td>
    </tr>
  `).join('');
}

function pillClass(status){
  if (status === 'Delivered' || status === 'Confirmed') return 'pill-approved';
  if (status === 'Cancelled') return 'pill-rejected';
  return 'pill-pending';
}

// ---- Products ----
async function loadProducts(){
  const body = document.getElementById('prodTableBody');
  try {
    const data = await Products.list({ limit: 200 });
    ALL_PRODUCTS = data.products;
    renderProducts();
  } catch(err){
    body.innerHTML = `<tr><td colspan="6" style="color:var(--neon-pink)">Couldn't load products: ${err.message}</td></tr>`;
  }
}

function renderProducts(){
  const body = document.getElementById('prodTableBody');
  if (!ALL_PRODUCTS.length){ body.innerHTML = `<tr><td colspan="6" style="color:var(--text-muted)">No products yet. Add your first one above.</td></tr>`; return; }
  body.innerHTML = ALL_PRODUCTS.map(p => `
    <tr>
      <td><strong>${p.name}</strong></td>
      <td>${p.category}</td>
      <td>PKR ${p.price.toLocaleString()}</td>
      <td>${p.stock_qty ?? '—'}</td>
      <td><span class="pill ${p.stock_status==='available' ? 'pill-approved' : 'pill-rejected'}">${p.stock_status==='available' ? 'Available' : 'Out of Stock'}</span></td>
      <td><div class="actions-cell">
        <button class="btn-approve" onclick='editProduct(${JSON.stringify(p).replace(/'/g,"&#39;")})'>✎ Edit</button>
        <button class="btn-delete" onclick="deleteProduct('${p.id}')">🗑</button>
      </div></td>
    </tr>
  `).join('');
}

function editProduct(p){
  editingProductId = p.id;
  document.getElementById('prodFormTitle').textContent = `Editing: ${p.name}`;
  document.getElementById('pfName').value = p.name;
  document.getElementById('pfCategory').value = p.category;
  document.getElementById('pfPrice').value = p.price;
  document.getElementById('pfStock').value = p.stock_qty || 0;
  document.getElementById('pfStatus').value = p.stock_status;
  document.getElementById('pfImage').value = p.image || '';
  document.getElementById('pfDesc').value = p.description || '';
  document.getElementById('pfSubmitBtn').textContent = 'Save Changes';
  document.getElementById('pfCancelBtn').classList.remove('hidden');
  document.getElementById('page-products').scrollIntoView({behavior:'smooth'});
}

function resetProductForm(){
  editingProductId = null;
  document.getElementById('prodFormTitle').textContent = 'Add New Product';
  ['pfName','pfCategory','pfPrice','pfStock','pfImage','pfDesc'].forEach(id => document.getElementById(id).value = '');
  document.getElementById('pfStatus').value = 'available';
  document.getElementById('pfSubmitBtn').textContent = '+ Add Product';
  document.getElementById('pfCancelBtn').classList.add('hidden');
}

async function submitProduct(){
  const name = document.getElementById('pfName').value.trim();
  const category = document.getElementById('pfCategory').value.trim();
  const price = parseFloat(document.getElementById('pfPrice').value);
  const stock_qty = parseInt(document.getElementById('pfStock').value) || 0;
  const stock_status = document.getElementById('pfStatus').value;
  const image = document.getElementById('pfImage').value.trim() || null;
  const description = document.getElementById('pfDesc').value.trim();

  if (!name || !category || !price || price <= 0){
    showToast('Name, category and a valid price are required.', 'error');
    return;
  }
  const payload = { name, category, price, stock_qty, stock_status, image, description };
  const btn = document.getElementById('pfSubmitBtn');
  btn.disabled = true;
  try {
    if (editingProductId){
      await Products.update(editingProductId, payload);
      showToast('Product updated!', 'success');
    } else {
      await Products.create(payload);
      showToast('Product added!', 'success');
    }
    resetProductForm();
    await loadProducts();
    await loadStats();
  } catch(err){
    showToast(err.message || 'Could not save product.', 'error');
  } finally {
    btn.disabled = false;
  }
}

async function deleteProduct(id){
  if (!confirm('Delete this product? This cannot be undone.')) return;
  try {
    await Products.delete(id);
    showToast('Product deleted.', 'info');
    await loadProducts();
    await loadStats();
  } catch(err){
    showToast(err.message || 'Could not delete product.', 'error');
  }
}

// ---- Orders ----
async function loadOrders(){
  const body = document.getElementById('orderTableBody');
  try {
    const data = await Orders.list();
    ALL_ORDERS = data.orders;
    renderOrders();
    renderRecentOrders();
  } catch(err){
    body.innerHTML = `<tr><td colspan="10" style="color:var(--neon-pink)">Couldn't load orders: ${err.message}</td></tr>`;
  }
}

function fmtDate(iso){
  const d = new Date(iso);
  return d.toLocaleDateString('en-PK', { day:'numeric', month:'short', year:'numeric' });
}

function renderOrders(){
  const body = document.getElementById('orderTableBody');
  if (!ALL_ORDERS.length){ body.innerHTML = `<tr><td colspan="10" style="color:var(--text-muted)">No orders yet.</td></tr>`; return; }
  body.innerHTML = ALL_ORDERS.map(o => `
    <tr>
      <td><strong>${o.order_number}</strong></td>
      <td>${o.customer_name}<br><span style="color:var(--text-muted);font-size:.75rem">${o.email || ''}</span></td>
      <td><a href="https://wa.me/${o.phone.replace(/\D/g,'')}" target="_blank" style="color:var(--neon-green)">${o.phone}</a></td>
      <td>${o.product_name}</td>
      <td>${o.quantity}</td>
      <td>PKR ${o.total_price.toLocaleString()}</td>
      <td>${o.city}</td>
      <td>${fmtDate(o.created_at)}</td>
      <td><span class="pill ${pillClass(o.status)}">${o.status}</span></td>
      <td><div class="actions-cell">
        <select class="status-select" onchange="changeOrderStatus('${o.id}', this.value)">
          ${STATUS_OPTIONS.map(s => `<option value="${s}" ${s===o.status?'selected':''}>${s}</option>`).join('')}
        </select>
      </div></td>
    </tr>
  `).join('');
}

async function changeOrderStatus(orderId, status){
  try {
    await Orders.updateStatus(orderId, status);
    showToast(`Order marked ${status}.`, 'success');
    await loadOrders();
    await loadStats();
  } catch(err){
    showToast(err.message || 'Could not update order.', 'error');
    await loadOrders();
  }
}

document.addEventListener('DOMContentLoaded', () => {
  spawnParticles();
  const dateEl = document.getElementById('topbarDate');
  if (dateEl) {
    dateEl.textContent = new Date().toLocaleDateString('en-PK', { weekday:'short', day:'numeric', month:'short', year:'numeric' });
  }

  // If we already have an admin session/token, skip the login screen.
  const session = Auth.getSession();
  if (session && session.role === 'admin' && Auth.isLoggedIn()) {
    enterAdmin(session);
  }

  document.getElementById('loginPass')?.addEventListener('keydown', e => { if (e.key === 'Enter') adminLogin(); });
});
