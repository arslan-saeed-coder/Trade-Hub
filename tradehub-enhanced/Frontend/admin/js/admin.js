// ===== TRADEHUB PK — ADMIN PANEL JS =====

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
  const titles = {dashboard:'Dashboard', suppliers:'Supplier Management', products:'Product Listings', categories:'Category Manager', buyers:'Buyer Management'};
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

function approveSupplier(btn) {
  const row = btn.closest('tr');
  const pill = row.querySelector('.pill');
  if (pill) { pill.className = 'pill pill-approved'; pill.textContent = 'Approved'; }
  row.querySelector('.actions-cell').innerHTML = '<span style="color:var(--neon-green);font-size:.8rem;font-weight:600;">✓ Approved</span><button class="btn-delete" onclick="deleteRow(this)">🗑</button>';
  updateStat('stat-pending', -1);
  showToast('Supplier approved successfully!', 'success');
}
function rejectSupplier(btn) {
  const row = btn.closest('tr');
  const pill = row.querySelector('.pill');
  if (pill) { pill.className = 'pill pill-rejected'; pill.textContent = 'Rejected'; }
  row.querySelector('.actions-cell').innerHTML = '<span style="color:var(--neon-pink);font-size:.8rem;font-weight:600;">✕ Rejected</span><button class="btn-delete" onclick="deleteRow(this)">🗑</button>';
  showToast('Supplier rejected.', 'error');
}

function deleteRow(btn) {
  const row = btn.closest('tr');
  row.style.transition = 'opacity .3s';
  row.style.opacity = '0';
  setTimeout(() => row.remove(), 300);
  showToast('Listing removed.', 'info');
}

function deleteCat(btn) {
  const item = btn.closest('.cat-mgr-item');
  item.style.transition = 'all .25s';
  item.style.opacity = '0'; item.style.transform = 'scale(.9)';
  setTimeout(() => item.remove(), 250);
  showToast('Category deleted.', 'info');
}
function addCategory() {
  const input = document.getElementById('catInput');
  const val = input?.value.trim();
  if (!val) { showToast('Please enter a category name.', 'error'); return; }
  const grid = document.getElementById('catGrid');
  const div = document.createElement('div');
  div.className = 'cat-mgr-item';
  div.style.animation = 'fadeIn .3s ease-out';
  div.innerHTML = `
    <div>
      <div class="cat-mgr-name">${val}</div>
      <div class="cat-mgr-count">0 products</div>
    </div>
    <button class="cat-del-btn" onclick="deleteCat(this)">🗑️</button>
  `;
  grid?.appendChild(div);
  if (input) input.value = '';
  showToast(`Category "${val}" added!`, 'success');
}

function updateStat(id, delta) {
  const el = document.getElementById(id);
  if (!el) return;
  const cur = parseInt(el.textContent) || 0;
  el.textContent = Math.max(0, cur + delta);
}

function searchTable(tableId, query) {
  const q = query.toLowerCase();
  const rows = document.querySelectorAll(`#${tableId} tbody tr`);
  rows.forEach(row => {
    const text = row.textContent.toLowerCase();
    row.style.display = text.includes(q) ? '' : 'none';
  });
}

function adminLogout() {
  if (confirm('Logout from admin panel?')) {
    window.location.href = '../index.html';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  spawnParticles();
  const dateEl = document.getElementById('topbarDate');
  if (dateEl) {
    dateEl.textContent = new Date().toLocaleDateString('en-PK', { weekday:'short', day:'numeric', month:'short', year:'numeric' });
  }
  document.getElementById('overlay')?.addEventListener('click', () => {
    document.querySelectorAll('.slide-panel').forEach(p => p.classList.remove('open'));
    document.getElementById('overlay')?.classList.remove('show');
  });
});

const style = document.createElement('style');
style.textContent = `@keyframes fadeIn{from{opacity:0;transform:scale(.95)}to{opacity:1;transform:scale(1)}}`;
document.head.appendChild(style);
