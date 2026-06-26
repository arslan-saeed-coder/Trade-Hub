# 🏪 TradeHub PK — B2B Wholesale Marketplace

Pakistan's B2B wholesale marketplace — FastAPI backend + Vanilla HTML/CSS/JS frontend.

---

## 📁 Project Structure

```
tradehub-pk/
├── Backend/          ← FastAPI (deploy to Railway)
│   ├── main.py
│   ├── requirements.txt
│   ├── Procfile
│   ├── railway.json
│   ├── .env.example  ← copy to .env and fill values
│   └── .gitignore
└── Frontend/         ← Static HTML (deploy to Vercel)
    ├── index.html
    ├── vercel.json
    ├── js/
    │   ├── config.js       ← SET YOUR RAILWAY URL HERE
    │   ├── api.js          ← All backend API calls
    │   ├── main.js         ← Homepage logic
    │   └── shared-auth.js  ← Auth modal (all inner pages)
    ├── css/
    ├── pages/
    └── admin/
```

---

## 🚀 DEPLOYMENT GUIDE — Step by Step

### STEP 1 — Push to GitHub

```bash
git init
git add .
git commit -m "TradeHub PK initial commit"
git remote add origin https://github.com/YOUR_USERNAME/tradehub-pk.git
git push -u origin main
```

---

### STEP 2 — Set up Supabase (Database)

1. Go to https://supabase.com → Create new project
2. Choose a region close to Pakistan (e.g. Singapore)
3. Go to **Settings → Database → Connection string**
4. Select **URI** mode and copy the connection string
5. Replace `[YOUR-PASSWORD]` with your DB password
6. It looks like: `postgresql://postgres:PASSWORD@db.XXXX.supabase.co:5432/postgres`

> **Note:** The backend currently uses in-memory storage with demo data.
> It works without Supabase — data resets on restart.
> Add `DATABASE_URL` to enable persistent PostgreSQL storage.

---

### STEP 3 — Deploy Backend to Railway

1. Go to https://railway.app → Login with GitHub
2. Click **New Project → Deploy from GitHub repo**
3. Select your repo → Choose the **Backend** folder as root
4. Railway auto-detects Python from `requirements.txt`
5. Go to **Variables** tab and add:

```
DATABASE_URL   = postgresql://postgres:PASSWORD@db.XXXX.supabase.co:5432/postgres
JWT_SECRET     = (generate: python -c "import secrets; print(secrets.token_hex(32))")
FRONTEND_URL   = https://your-project.vercel.app
APP_NAME       = TradeHub PK API
```

6. Click **Deploy**
7. Copy your Railway URL (e.g. `https://tradehub-pk-backend.railway.app`)
8. Test it: visit `https://your-backend.railway.app/health` — should return `{"status":"ok"}`

**Admin login credentials (demo):**
- Email: `admin@tradehubpk.com`
- Password: `admin123`

**Supplier demo:**
- Email: `supplier@tradehubpk.com`
- Password: `supplier123`

---

### STEP 4 — Update Frontend Config

Open `Frontend/js/config.js` and update your Railway URL:

```js
window.TRADEHUB_API_URL = 'https://tradehub-pk-backend.railway.app';
```

Commit and push this change.

---

### STEP 5 — Deploy Frontend to Vercel

1. Go to https://vercel.com → Login with GitHub
2. Click **New Project → Import Git Repository**
3. Select your repo
4. Set **Root Directory** to `Frontend`
5. Framework: **Other** (plain HTML)
6. Click **Deploy**
7. Copy your Vercel URL (e.g. `https://tradehub-pk.vercel.app`)

---

### STEP 6 — Update CORS in Railway

Go back to Railway → Variables → Update:

```
FRONTEND_URL = https://tradehub-pk.vercel.app
```

Redeploy backend (Railway does this automatically on variable change).

---

## 🔐 Default Credentials

| Role     | Email                      | Password     |
|----------|----------------------------|--------------|
| Admin    | admin@tradehubpk.com       | admin123     |
| Supplier | supplier@tradehubpk.com    | supplier123  |

> ⚠️ Change these immediately in production by updating the `_users` list in `main.py`
> or (better) by adding real users through the `/api/auth/register` endpoint.

---

## 🌐 API Endpoints

Base URL: `https://your-backend.railway.app`

| Method | Endpoint                        | Description              | Auth     |
|--------|---------------------------------|--------------------------|----------|
| GET    | /health                         | Health check             | None     |
| POST   | /api/auth/register              | Register buyer/supplier  | None     |
| POST   | /api/auth/login                 | Login                    | None     |
| GET    | /api/auth/me                    | Get current user         | Token    |
| GET    | /api/suppliers                  | List suppliers           | None     |
| POST   | /api/suppliers                  | Create supplier          | Token    |
| GET    | /api/suppliers/{id}             | Get supplier             | None     |
| GET    | /api/products                   | List products            | None     |
| POST   | /api/inquiries                  | Send inquiry             | None     |
| POST   | /api/rfqs                       | Submit RFQ               | None     |
| GET    | /api/search?q=term              | Search all               | None     |
| GET    | /api/stats                      | Public stats             | None     |
| PATCH  | /api/admin/suppliers/{id}/approve | Approve supplier       | Admin    |
| GET    | /api/admin/stats                | Admin dashboard stats    | Admin    |

Full docs: `https://your-backend.railway.app/docs`

---

## 📊 Admin Panel

URL: `https://your-frontend.vercel.app/admin/`

Login with admin credentials above. Features:
- ✅ Approve/reject supplier applications
- 🗂️ Manage categories
- 📦 View & remove product listings
- 💬 View buyer inquiries
- 👥 Manage all users
- 📊 Platform analytics

---

## 🛠️ Local Development

```bash
# Backend
cd Backend
pip install -r requirements.txt
cp .env.example .env      # fill in your values
uvicorn main:app --reload --port 8000

# Frontend (any live server)
cd Frontend
# Open with VS Code Live Server, or:
python -m http.server 5500
# Visit http://localhost:5500
```

Update `Frontend/js/config.js`:
```js
window.TRADEHUB_API_URL = 'http://localhost:8000';
```

---

## 🔧 Built With

- **Backend:** FastAPI, Uvicorn, Pydantic, PyJWT, Passlib/bcrypt, psycopg2
- **Database:** Supabase (PostgreSQL)
- **Frontend:** Vanilla HTML, CSS, JavaScript (no frameworks)
- **Deploy:** Railway (backend) + Vercel (frontend)

---

Built by **Arslan Saeed** — UMT Lahore, Cybersecurity & CS
