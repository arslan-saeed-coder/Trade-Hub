from fastapi import FastAPI, HTTPException, Query, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import uuid, os, jwt
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL   = os.getenv("DATABASE_URL", "")
JWT_SECRET     = os.getenv("JWT_SECRET", "tradehub-secret-change-in-production")
JWT_ALGORITHM  = "HS256"
JWT_EXPIRE_MIN = 60 * 24 * 7
FRONTEND_URL   = os.getenv("FRONTEND_URL", "http://localhost:5500")

STORE_NAME = os.getenv("STORE_NAME", "My Store")

app = FastAPI(title="TradeHub PK Store API", version="4.0.0", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5500", "http://127.0.0.1:5500", "http://localhost:3000"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer  = HTTPBearer(auto_error=False)

def hash_password(pw): return pwd_ctx.hash(pw)
def verify_password(plain, hashed): return pwd_ctx.verify(plain, hashed)
def create_token(data):
    p = data.copy(); p["exp"] = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MIN)
    return jwt.encode(p, JWT_SECRET, algorithm=JWT_ALGORITHM)
def decode_token(token):
    try: return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError: raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:     raise HTTPException(401, "Invalid token")

def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    if not creds: raise HTTPException(401, "Not authenticated")
    return decode_token(creds.credentials)

def get_optional_user(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    if not creds: return None
    try: return decode_token(creds.credentials)
    except HTTPException: return None

def require_admin(user=Depends(get_current_user)):
    if user.get("role") != "admin": raise HTTPException(403, "Admin access required")
    return user

def now(): return datetime.now(timezone.utc).isoformat()

# ---- In-memory store (Supabase/psycopg2 integration ready via DATABASE_URL) ----
_users = [
    {"id":"u1","name":"Admin User","email":"admin@tradehubpk.com","hashed_password":hash_password("admin123"),
     "role":"admin","phone":None,"status":"active","created_at":now()},
]

_products = [
    {"id":"p1","name":"Fast Charging USB-C Cable","category":"Electronics","price":450.0,"image":None,
     "description":"Durable braided USB-C fast charging cable, 1.2m.","stock_status":"available","stock_qty":120,"views":0,"created_at":now()},
    {"id":"p2","name":"Wireless Bluetooth Earbuds","category":"Electronics","price":2200.0,"image":None,
     "description":"Compact wireless earbuds with charging case.","stock_status":"available","stock_qty":45,"views":0,"created_at":now()},
    {"id":"p3","name":"Premium Cotton T-Shirt","category":"Apparel","price":950.0,"image":None,
     "description":"Soft 100% cotton tee, available in multiple sizes.","stock_status":"available","stock_qty":80,"views":0,"created_at":now()},
]

_orders = []
_order_seq = 1000

# ---- Schemas ----
class RegisterRequest(BaseModel):
    name: str; email: EmailStr; password: str
    phone: Optional[str]=None

class LoginRequest(BaseModel):
    email: EmailStr; password: str

class ProductCreate(BaseModel):
    name: str; category: str; price: float
    image: Optional[str]=None; description: str=""
    stock_status: str="available"; stock_qty: int=0

class OrderCreate(BaseModel):
    product_id: str
    quantity: int = 1
    customer_name: str
    phone: str
    email: Optional[EmailStr] = None
    address: str
    city: str
    notes: Optional[str] = None

class OrderStatusUpdate(BaseModel):
    status: str

VALID_STATUSES = ["Pending","Confirmed","Processing","Shipped","Delivered","Cancelled"]

# ---- Root / Health ----
@app.get("/")
def root(): return {"message":f"{STORE_NAME} API ✅","docs":"/docs","version":"4.0.0"}

@app.get("/health")
def health(): return {"status":"ok","time":now(),"db":"supabase" if DATABASE_URL else "in-memory"}

@app.get("/api/store")
def store_info(): return {"name": STORE_NAME, "badge": "Verified Seller"}

# ---- Auth ----
@app.post("/api/auth/register", status_code=201)
def register(body: RegisterRequest):
    if any(u["email"]==body.email for u in _users):
        raise HTTPException(400,"Email already registered")
    user={"id":str(uuid.uuid4()),"name":body.name,"email":body.email,"phone":body.phone,
          "hashed_password":hash_password(body.password),"role":"customer","status":"active","created_at":now()}
    _users.append(user)
    token=create_token({"sub":user["id"],"email":user["email"],"role":user["role"],"name":user["name"]})
    return {"token":token,"user":{k:v for k,v in user.items() if k!="hashed_password"}}

@app.post("/api/auth/login")
def login(body: LoginRequest):
    user=next((u for u in _users if u["email"]==body.email),None)
    if not user or not verify_password(body.password,user["hashed_password"]):
        raise HTTPException(401,"Invalid email or password")
    if user.get("status")=="banned": raise HTTPException(403,"Account suspended")
    token=create_token({"sub":user["id"],"email":user["email"],"role":user["role"],"name":user["name"]})
    return {"token":token,"user":{k:v for k,v in user.items() if k!="hashed_password"}}

@app.get("/api/auth/me")
def me(user=Depends(get_current_user)):
    u=next((u for u in _users if u["id"]==user["sub"]),None)
    if not u: raise HTTPException(404,"User not found")
    return {k:v for k,v in u.items() if k!="hashed_password"}

# ---- Categories ----
@app.get("/api/categories")
def categories(): return sorted(set(p["category"] for p in _products))

# ---- Public stats ----
@app.get("/api/stats")
def stats():
    return {"products": len(_products), "categories": len(set(p["category"] for p in _products))}

# ---- Products (single-owner: admin only can create/edit/delete) ----
@app.get("/api/products")
def list_products(search:Optional[str]=None,category:Optional[str]=None,
                  stock_status:Optional[str]=None,limit:int=50,offset:int=0):
    r=_products[:]
    if search: q=search.lower(); r=[p for p in r if q in p["name"].lower() or q in p["description"].lower()]
    if category: r=[p for p in r if p["category"].lower()==category.lower()]
    if stock_status: r=[p for p in r if p["stock_status"]==stock_status]
    return {"total":len(r),"products":r[offset:offset+limit]}

@app.post("/api/products",status_code=201)
def create_product(payload:ProductCreate,_=Depends(require_admin)):
    p={"id":str(uuid.uuid4()),"views":0,"created_at":now(),**payload.model_dump()}
    _products.append(p); return p

@app.get("/api/products/{pid}")
def get_product(pid:str):
    p=next((p for p in _products if p["id"]==pid),None)
    if not p: raise HTTPException(404,"Product not found")
    p["views"]+=1; return p

@app.put("/api/products/{pid}")
def update_product(pid:str,payload:ProductCreate,_=Depends(require_admin)):
    p=next((p for p in _products if p["id"]==pid),None)
    if not p: raise HTTPException(404,"Product not found")
    p.update(payload.model_dump()); return p

@app.delete("/api/products/{pid}")
def delete_product(pid:str,_=Depends(require_admin)):
    p=next((p for p in _products if p["id"]==pid),None)
    if not p: raise HTTPException(404,"Product not found")
    _products.remove(p); return {"deleted":pid}

# ---- Orders ----
def _order_number():
    global _order_seq
    _order_seq += 1
    return f"ORD-{_order_seq}"

@app.post("/api/orders", status_code=201)
def create_order(payload: OrderCreate, user=Depends(get_optional_user)):
    product = next((p for p in _products if p["id"] == payload.product_id), None)
    if not product:
        raise HTTPException(404, "Product not found")
    if payload.quantity < 1:
        raise HTTPException(400, "Quantity must be at least 1")
    if not payload.customer_name.strip() or not payload.phone.strip() or not payload.address.strip() or not payload.city.strip():
        raise HTTPException(400, "Full name, phone, address and city are required")

    total = round(product["price"] * payload.quantity, 2)
    order = {
        "id": str(uuid.uuid4()),
        "order_number": _order_number(),
        "user_id": user["sub"] if user else None,
        "product_id": product["id"],
        "product_name": product["name"],
        "unit_price": product["price"],
        "quantity": payload.quantity,
        "total_price": total,
        "customer_name": payload.customer_name.strip(),
        "phone": payload.phone.strip(),
        "email": payload.email,
        "address": payload.address.strip(),
        "city": payload.city.strip(),
        "notes": payload.notes,
        "status": "Pending",
        "created_at": now(),
        "updated_at": now(),
    }
    _orders.append(order)
    return order

@app.get("/api/orders")
def list_orders(status: Optional[str] = None, _=Depends(require_admin)):
    r = _orders[:]
    if status: r = [o for o in r if o["status"] == status]
    return {"total": len(r), "orders": sorted(r, key=lambda o: o["created_at"], reverse=True)}

@app.get("/api/orders/my")
def my_orders(user=Depends(get_current_user)):
    r = [o for o in _orders if o.get("user_id") == user["sub"]]
    return {"total": len(r), "orders": sorted(r, key=lambda o: o["created_at"], reverse=True)}

@app.get("/api/orders/{oid}")
def get_order(oid: str, _=Depends(require_admin)):
    o = next((o for o in _orders if o["id"] == oid), None)
    if not o: raise HTTPException(404, "Order not found")
    return o

@app.patch("/api/orders/{oid}/status")
def update_order_status(oid: str, payload: OrderStatusUpdate, _=Depends(require_admin)):
    if payload.status not in VALID_STATUSES:
        raise HTTPException(400, f"Status must be one of {VALID_STATUSES}")
    o = next((o for o in _orders if o["id"] == oid), None)
    if not o: raise HTTPException(404, "Order not found")
    o["status"] = payload.status
    o["updated_at"] = now()
    return o

@app.delete("/api/orders/{oid}")
def delete_order(oid: str, _=Depends(require_admin)):
    o = next((o for o in _orders if o["id"] == oid), None)
    if not o: raise HTTPException(404, "Order not found")
    _orders.remove(o)
    return {"deleted": oid}

# ---- Admin ----
@app.get("/api/admin/users")
def admin_users(_=Depends(require_admin)):
    return [{k:v for k,v in u.items() if k!="hashed_password"} for u in _users]

@app.get("/api/admin/stats")
def admin_stats(_=Depends(require_admin)):
    today = datetime.now(timezone.utc).date().isoformat()
    this_month = datetime.now(timezone.utc).strftime("%Y-%m")
    by_status = {s: len([o for o in _orders if o["status"] == s]) for s in VALID_STATUSES}
    today_orders = len([o for o in _orders if o["created_at"][:10] == today])
    monthly_sales = round(sum(o["total_price"] for o in _orders
                               if o["created_at"][:7] == this_month and o["status"] != "Cancelled"), 2)
    return {
        "total_products": len(_products),
        "total_orders": len(_orders),
        "pending_orders": by_status["Pending"],
        "confirmed_orders": by_status["Confirmed"],
        "processing_orders": by_status["Processing"],
        "shipped_orders": by_status["Shipped"],
        "delivered_orders": by_status["Delivered"],
        "cancelled_orders": by_status["Cancelled"],
        "today_orders": today_orders,
        "monthly_sales": monthly_sales,
        "total_users": len(_users),
    }

# ---- Search ----
@app.get("/api/search")
def universal_search(q:str=Query(...),category:Optional[str]=None):
    ql=q.lower()
    pro=[p for p in _products if ql in p["name"].lower() or ql in p["description"].lower()]
    if category: pro=[p for p in pro if p["category"].lower()==category.lower()]
    return {"query":q,"products":pro}
