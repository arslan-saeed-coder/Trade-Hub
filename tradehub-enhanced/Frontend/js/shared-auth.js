// ===== TRADEHUB PK — SHARED AUTH (inner pages) =====
// Requires api.js to be loaded first

(function () {
  const modalHTML = `
  <div class="modal-overlay" id="authModal">
    <div class="modal">
      <div class="modal-header">
        <h3 id="modalTitle">Welcome back</h3>
        <button class="modal-close" onclick="closeModal()">✕</button>
      </div>
      <div class="modal-tabs">
        <button class="modal-tab active" id="tabLogin" onclick="switchTab('login')">Login</button>
        <button class="modal-tab" id="tabRegister" onclick="switchTab('register')">Register</button>
      </div>
      <div id="loginForm">
        <div class="form-group"><label>Email</label><input type="email" placeholder="you@example.com" id="loginEmail"></div>
        <div class="form-group"><label>Password</label><input type="password" placeholder="••••••••" id="loginPass"></div>
        <button class="btn-submit" id="loginBtn" onclick="handleLogin()">Login</button>
        <div class="divider">or</div>
        <button class="btn-submit" style="background:#25D366" onclick="goSupplierReg()">Supplier Registration →</button>
      </div>
      <div id="registerForm" style="display:none">
        <div class="form-group"><label>Full Name</label><input type="text" placeholder="Muhammad Ali" id="regName"></div>
        <div class="form-group"><label>Email</label><input type="email" placeholder="you@example.com" id="regEmail"></div>
        <div class="form-group"><label>Phone</label><input type="tel" placeholder="03001234567" id="regPhone"></div>
        <div class="form-group"><label>Password</label><input type="password" placeholder="Min 8 characters" id="regPass"></div>
        <button class="btn-submit" id="regBtn" onclick="handleRegister()">Create Account</button>
      </div>
    </div>
  </div>`;
  document.body.insertAdjacentHTML('beforeend', modalHTML);

  if (!document.getElementById('toastStack')) {
    document.body.insertAdjacentHTML('beforeend', '<div class="toast-stack" id="toastStack"></div>');
  }

  document.addEventListener('DOMContentLoaded', function () {
    const session = typeof Auth !== 'undefined' ? Auth.getSession() : JSON.parse(localStorage.getItem('th_session') || 'null');
    if (session) updateNavForUser(session);
    document.getElementById('authModal').addEventListener('click', function (e) {
      if (e.target === this) closeModal();
    });
  });
})();

function goSupplierReg() {
  const path = window.location.pathname;
  const inPages = path.includes('/pages/');
  window.location.href = inPages ? 'supplier-register.html' : 'pages/supplier-register.html';
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

async function handleLogin() {
  const email = document.getElementById('loginEmail').value.trim();
  const pass  = document.getElementById('loginPass').value;
  if (!email || !pass) { showToast('Please fill all fields.', 'error'); return; }
  const btn = document.getElementById('loginBtn');
  btn.textContent = 'Logging in…'; btn.disabled = true;
  try {
    const data = await Auth.login(email, pass);
    closeModal();
    showToast(`Welcome back, ${data.user.name}!`, 'success');
    updateNavForUser(data.user);
  } catch (err) {
    showToast(err.message || 'Login failed.', 'error');
  } finally {
    btn.textContent = 'Login'; btn.disabled = false;
  }
}

async function handleRegister() {
  const name  = document.getElementById('regName').value.trim();
  const email = document.getElementById('regEmail').value.trim();
  const phone = document.getElementById('regPhone').value.trim();
  const pass  = document.getElementById('regPass').value;
  if (!name || !email || !phone || !pass) { showToast('Please fill all fields.', 'error'); return; }
  if (pass.length < 6) { showToast('Password must be at least 6 characters.', 'error'); return; }
  const btn = document.getElementById('regBtn');
  btn.textContent = 'Creating account…'; btn.disabled = true;
  try {
    const data = await Auth.register(name, email, pass, phone, 'buyer');
    closeModal();
    showToast(`Account created! Welcome, ${data.user.name}!`, 'success');
    updateNavForUser(data.user);
  } catch (err) {
    showToast(err.message || 'Registration failed.', 'error');
  } finally {
    btn.textContent = 'Create Account'; btn.disabled = false;
  }
}

function updateNavForUser(user) {
  const actions = document.querySelector('.nav-actions');
  if (!actions) return;
  const path = window.location.pathname;
  const inPages = path.includes('/pages/') || (path !== '/' && !path.endsWith('index.html') && path.split('/').length > 2);
  const dashPath = inPages ? 'buyer-dashboard.html' : 'pages/buyer-dashboard.html';
  actions.innerHTML = `
    <a href="${dashPath}" class="btn-login">My Account</a>
    <button class="btn-register" onclick="Auth.logout()">Logout</button>
  `;
}

function logout() {
  if (typeof Auth !== 'undefined') Auth.logout();
  else { localStorage.removeItem('th_token'); localStorage.removeItem('th_session'); location.reload(); }
}

function showToast(msg, type = 'success') {
  let stack = document.getElementById('toastStack');
  if (!stack) { stack = document.createElement('div'); stack.id = 'toastStack'; stack.className = 'toast-stack'; document.body.appendChild(stack); }
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.textContent = msg;
  stack.appendChild(t);
  setTimeout(() => t.remove(), 3100);
}
function sendInquiry(el) {
  const productName = typeof el === 'string' ? el : el.getAttribute('data-name');
  const session = typeof Auth !== 'undefined' ? Auth.getSession() : JSON.parse(localStorage.getItem('th_session') || 'null');
  if (!session) { openModal('login'); showToast('Please login to send inquiries.', 'error'); return; }
  showToast(`Inquiry sent for "${productName}"!`, 'success');
}
