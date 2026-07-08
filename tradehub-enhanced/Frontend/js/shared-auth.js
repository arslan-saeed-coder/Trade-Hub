(function () {
  const modalHTML = `<div class="modal-overlay" id="authModal"><div class="modal"><div class="modal-header"><h3 id="modalTitle">Welcome back</h3><button class="modal-close" onclick="closeModal()">✕</button></div><div class="modal-tabs"><button class="modal-tab active" id="tabLogin" onclick="switchTab('login')">Login</button><button class="modal-tab" id="tabRegister" onclick="switchTab('register')">Register</button></div><div id="loginForm"><div class="form-group"><label>Email</label><input type="email" id="loginEmail" placeholder="you@example.com"></div><div class="form-group"><label>Password</label><input type="password" id="loginPass" placeholder="••••••••"></div><button class="btn-submit" id="loginBtn" onclick="handleLogin()">Login</button></div><div id="registerForm" style="display:none"><div class="form-group"><label>Full Name</label><input type="text" id="regName" placeholder="Muhammad Ali"></div><div class="form-group"><label>Email</label><input type="email" id="regEmail" placeholder="you@example.com"></div><div class="form-group"><label>Phone</label><input type="tel" id="regPhone" placeholder="03001234567"></div><div class="form-group"><label>Password</label><input type="password" id="regPass" placeholder="Min 6 characters"></div><button class="btn-submit" id="regBtn" onclick="handleRegister()">Create Account</button></div></div></div>`;

  document.body.insertAdjacentHTML("beforeend", modalHTML);

  if (!document.getElementById("toastStack")) {
    document.body.insertAdjacentHTML("beforeend", '<div class="toast-stack" id="toastStack"></div>');
  }

  document.addEventListener("DOMContentLoaded", () => {
    const user = Auth.getSession();
    if (user) updateNavForUser(user);

    document.getElementById("authModal")?.addEventListener("click", (e) => {
      if (e.target.id === "authModal") closeModal();
    });
  });
})();

function openModal(tab) {
  document.getElementById("authModal").classList.add("show");
  switchTab(tab || "login");
}

function closeModal() {
  document.getElementById("authModal").classList.remove("show");
}

function switchTab(tab) {
  const isLogin = tab === "login";

  document.getElementById("loginForm").style.display = isLogin ? "block" : "none";
  document.getElementById("registerForm").style.display = isLogin ? "none" : "block";

  document.getElementById("tabLogin").classList.toggle("active", isLogin);
  document.getElementById("tabRegister").classList.toggle("active", !isLogin);

  document.getElementById("modalTitle").textContent = isLogin
    ? "Welcome back"
    : "Create customer account";
}

async function handleLogin() {
  const email = document.getElementById("loginEmail").value.trim();
  const pass = document.getElementById("loginPass").value;

  if (!email || !pass) {
    return showToast("Please fill all fields.", "error");
  }

  try {
    const data = await Auth.login(email, pass);

    closeModal();

    const userName = data.user.name || data.user.full_name || "User";
    showToast(`Welcome back, ${userName}!`, "success");

    updateNavForUser(data.user);

    setTimeout(() => {
      if (data.user.role === "admin") {
        window.location.href = "/admin/index.html";
      } else {
        window.location.href = "/pages/buyer-dashboard.html";
      }
    }, 700);
  } catch (e) {
    showToast(e.message || "Login failed.", "error");
  }
}

async function handleRegister() {
  const name = document.getElementById("regName").value.trim();
  const email = document.getElementById("regEmail").value.trim();
  const phone = document.getElementById("regPhone").value.trim();
  const pass = document.getElementById("regPass").value;

  if (!name || !email || !phone || !pass) {
    return showToast("Please fill all fields.", "error");
  }

  try {
    const data = await Auth.register(name, email, pass, phone);

    closeModal();

    const userName = data.user.name || data.user.full_name || name;
    showToast(`Account created successfully. Welcome, ${userName}!`, "success");

    updateNavForUser(data.user);

    setTimeout(() => {
      window.location.href = "/pages/buyer-dashboard.html";
    }, 700);
  } catch (e) {
    showToast(e.message || "Registration failed.", "error");
  }
}

function updateNavForUser(user) {
  const actions = document.querySelector(".nav-actions");
  if (!actions) return;

  actions.innerHTML = `
    <a href="/pages/buyer-dashboard.html" class="btn-login">My Account</a>
    ${
      user.role === "admin"
        ? `<a href="/admin/index.html" class="btn-login">Admin</a>`
        : ""
    }
    <button class="btn-register" onclick="Auth.logout()">Logout</button>
  `;
}
