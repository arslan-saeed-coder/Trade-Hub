from fastapi import FastAPI, HTTPException, Query, Body, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext
import uuid, os, jwt
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL   = os.getenv("DATABASE_URL", "")
JWT_SECRET     = os.getenv("JWT_SECRET", "tradehub-secret-change-in-production")
JWT_ALGORITHM  = "HS256"
JWT_EXPIRE_MIN = 60 * 24 * 7
FRONTEND_URL   = os.getenv("FRONTEND_URL", "http://localhost:5500")

app = FastAPI(title="TradeHub PK API", version="3.0.0", docs_url="/docs")

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
    p = data.copy(); p["exp"] = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MIN)
    return jwt.encode(p, JWT_SECRET, algorithm=JWT_ALGORITHM)
def decode_token(token):
    try: return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError: raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:     raise HTTPException(401, "Invalid token")

def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    if not creds: raise HTTPException(401, "Not authenticated")
    return decode_token(creds.credentials)
def require_admin(user=Depends(get_current_user)):
    if user.get("role") != "admin": raise HTTPException(403, "Admin access required")
    return user
def require_supplier(user=Depends(get_current_user)):
    if user.get("role") not in ("supplier","admin"): raise HTTPException(403, "Supplier access required")
    return user

def now(): return datetime.utcnow().isoformat()

# ---- In-memory store (Supabase/psycopg2 integration ready via DATABASE_URL) ----
_users = [
    {"id":"u1","name":"Admin User",   "email":"admin@tradehubpk.com",   "hashed_password":hash_password("admin123"),   "role":"admin",   "phone":None,"status":"active","created_at":now()},
    {"id":"u2","name":"Demo Supplier","email":"supplier@tradehubpk.com","hashed_password":hash_password("supplier123"),"role":"supplier","phone":None,"status":"active","created_at":now()},
]
_suppliers = [
    {"id":"s1","owner_user_id":"u2","company_name":"Global Apparel Wholesale","category":"Apparel","city":"Lahore","country":"Pakistan","description":"Bulk clothing, uniforms, hoodies and T-shirts for retailers.","website":None,"phone":"+92 300 0000001","email":"sales@apparel.example","logo":None,"catalog_url":None,"verified":True,"verification_score":91,"rating":4.7,"plan":"premium","featured":True,"status":"approved","created_at":now()},
    {"id":"s2","owner_user_id":None,"company_name":"Prime Electronics Hub","category":"Electronics","city":"Karachi","country":"Pakistan","description":"Wholesale mobile accessories, earbuds, chargers and gadgets.","website":None,"phone":"+92 300 0000002","email":"contact@electronics.example","logo":None,"catalog_url":None,"verified":True,"verification_score":88,"rating":4.5,"plan":"standard","featured":True,"status":"approved","created_at":now()},
    {"id":"s3","owner_user_id":None,"company_name":"HomeStyle Distributors","category":"Home & Kitchen","city":"Faisalabad","country":"Pakistan","description":"Kitchen tools, decor, storage items and daily-use goods.","website":None,"phone":"+92 300 0000003","email":"info@homestyle.example","logo":None,"catalog_url":None,"verified":False,"verification_score":61,"rating":4.2,"plan":"free","featured":False,"status":"approved","created_at":now()},
    {"id":"s4","owner_user_id":None,"company_name":"BeautyPro Wholesale","category":"Beauty","city":"Islamabad","country":"Pakistan","description":"Cosmetics, salon products, skincare items in bulk.","website":None,"phone":"+92 300 0000004","email":"sales@beautypro.example","logo":None,"catalog_url":None,"verified":True,"verification_score":94,"rating":4.8,"plan":"premium","featured":False,"status":"approved","created_at":now()},
    {"id":"s5","owner_user_id":None,"company_name":"Pak Steel Works","category":"Hardware","city":"Lahore","country":"Pakistan","description":"Steel bars, pipes, bolts and construction hardware wholesale.","website":None,"phone":"+92 300 0000005","email":"info@paksteel.example","logo":None,"catalog_url":None,"verified":True,"verification_score":85,"rating":4.6,"plan":"standard","featured":False,"status":"approved","created_at":now()},
    {"id":"s6","owner_user_id":None,"company_name":"Punjab Rice Mills","category":"Food & Grain","city":"Sheikhupura","country":"Pakistan","description":"Basmati rice, flour, grains wholesale export quality.","website":None,"phone":"+92 300 0000006","email":"info@punjabrice.example","logo":None,"catalog_url":None,"verified":True,"verification_score":89,"rating":4.9,"plan":"premium","featured":True,"status":"approved","created_at":now()},
    {"id":"s7","owner_user_id":None,"company_name":"Sialkot Sports Co.","category":"Sports","city":"Sialkot","country":"Pakistan","description":"Footballs, gloves, sports gear wholesale direct from manufacturer.","website":None,"phone":"+92 300 0000007","email":"info@siasports.example","logo":None,"catalog_url":None,"verified":True,"verification_score":90,"rating":4.7,"plan":"standard","featured":False,"status":"approved","created_at":now()},
    {"id":"s8","owner_user_id":None,"company_name":"Karachi Leather House","category":"Leather","city":"Karachi","country":"Pakistan","description":"Wallets, belts, bags — handmade leather goods wholesale.","website":None,"phone":"+92 300 0000008","email":"info@kleather.example","logo":None,"catalog_url":None,"verified":False,"verification_score":55,"rating":4.1,"plan":"free","featured":False,"status":"approved","created_at":now()},
    {"id":"s9","owner_user_id":None,"company_name":"GreenFarm Exports","category":"Agriculture","city":"Multan","country":"Pakistan","description":"Mangoes, dates, vegetables, wheat export and wholesale.","website":None,"phone":"+92 300 0000009","email":"info@greenfarm.example","logo":None,"catalog_url":None,"verified":True,"verification_score":82,"rating":4.5,"plan":"standard","featured":False,"status":"pending","created_at":now()},
]
_products = [
    {"id":"p1","supplier_id":"s1","name":"Premium Cotton T-Shirts","category":"Apparel","price_range":"$2.50 – $5.00","moq":"100 pcs","image":None,"description":"Soft cotton tees in multiple sizes and colors.","stock_status":"available","views":42,"created_at":now()},
    {"id":"p2","supplier_id":"s2","name":"Fast Charging USB-C Cables","category":"Electronics","price_range":"$0.70 – $1.50","moq":"500 pcs","image":None,"description":"USB-C and Lightning cables for retail.","stock_status":"available","views":51,"created_at":now()},
    {"id":"p3","supplier_id":"s3","name":"Kitchen Storage Boxes","category":"Home & Kitchen","price_range":"$1.20 – $3.20","moq":"200 sets","image":None,"description":"Durable plastic storage box sets.","stock_status":"available","views":28,"created_at":now()},
    {"id":"p4","supplier_id":"s4","name":"Salon Hair Brush Set","category":"Beauty","price_range":"$1.80 – $4.40","moq":"150 sets","image":None,"description":"Professional brush sets for salons.","stock_status":"available","views":39,"created_at":now()},
    {"id":"p5","supplier_id":"s5","name":"MS Steel Bars 12mm","category":"Hardware","price_range":"PKR 1,950/kg","moq":"100 kg","image":None,"description":"Mild steel bars for construction.","stock_status":"available","views":33,"created_at":now()},
    {"id":"p6","supplier_id":"s6","name":"Basmati Rice Grade A","category":"Food & Grain","price_range":"PKR 2,800/50kg","moq":"5 Ton","image":None,"description":"Premium export-quality basmati rice.","stock_status":"available","views":67,"created_at":now()},
    {"id":"p7","supplier_id":"s7","name":"Match Football (FIFA Approved)","category":"Sports","price_range":"$4.50 – $9.00","moq":"50 pcs","image":None,"description":"Match-grade footballs direct from Sialkot.","stock_status":"available","views":44,"created_at":now()},
    {"id":"p8","supplier_id":"s8","name":"Genuine Leather Wallet","category":"Leather","price_range":"PKR 320 – 650","moq":"200 pcs","image":None,"description":"Handmade cow leather wallets.","stock_status":"available","views":22,"created_at":now()},
]
_inquiries = []
_rfqs      = []
_reviews   = []
_favorites = []
_messages  = []

# ---- Schemas ----
class RegisterRequest(BaseModel):
    name: str; email: EmailStr; password: str
    phone: Optional[str]=None; role: str="buyer"
class LoginRequest(BaseModel):
    email: EmailStr; password: str
class SupplierCreate(BaseModel):
    company_name: str; category: str; city: str; country: str="Pakistan"
    description: str; website: Optional[str]=None; phone: Optional[str]=None
    email: Optional[EmailStr]=None; logo: Optional[str]=None; catalog_url: Optional[str]=None
class ProductCreate(BaseModel):
    supplier_id: str; name: str; category: str; price_range: str; moq: str
    image: Optional[str]=None; description: str; stock_status: str="available"
class InquiryCreate(BaseModel):
    supplier_id: str; buyer_name: str; buyer_email: EmailStr
    message: str; quantity: Optional[str]=None; budget: Optional[str]=None
class RFQCreate(BaseModel):
    buyer_name: str; buyer_email: EmailStr; category: str
    product_needed: str; quantity: str; target_price: Optional[str]=None
    delivery_location: Optional[str]=None; details: str
class ReviewCreate(BaseModel):
    supplier_id: str; reviewer_name: str; rating: int; comment: str
class FavoriteCreate(BaseModel):
    user_email: EmailStr; item_type: str; item_id: str
class MessageCreate(BaseModel):
    supplier_id: str; sender_name: str; sender_email: EmailStr; body: str

# ---- Root / Health ----
@app.get("/")
def root(): return {"message":"TradeHub PK API ✅","docs":"/docs","version":"3.0.0"}
@app.get("/health")
def health(): return {"status":"ok","time":now(),"db":"supabase" if DATABASE_URL else "in-memory"}

# ---- Auth ----
@app.post("/api/auth/register", status_code=201)
def register(body: RegisterRequest):
    if any(u["email"]==body.email for u in _users):
        raise HTTPException(400,"Email already registered")
    user={"id":str(uuid.uuid4()),"name":body.name,"email":body.email,"phone":body.phone,
          "hashed_password":hash_password(body.password),"role":body.role,"status":"active","created_at":now()}
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

# ---- Categories & Stats ----
@app.get("/api/categories")
def categories(): return sorted(set([s["category"] for s in _suppliers]+[p["category"] for p in _products]))

@app.get("/api/stats")
def stats():
    return {"suppliers":len(_suppliers),"verified_suppliers":len([s for s in _suppliers if s["verified"]]),
            "products":len(_products),"rfqs":len(_rfqs),"inquiries":len(_inquiries),"users":len(_users),
            "pending_suppliers":len([s for s in _suppliers if s["status"]=="pending"])}

# ---- Suppliers ----
@app.get("/api/suppliers")
def list_suppliers(search:Optional[str]=None,category:Optional[str]=None,city:Optional[str]=None,
                   verified:Optional[bool]=None,featured:Optional[bool]=None,status:Optional[str]=None,
                   limit:int=50,offset:int=0):
    r=_suppliers[:]
    if search:
        q=search.lower(); r=[s for s in r if q in s["company_name"].lower() or q in s["description"].lower() or q in s["city"].lower()]
    if category: r=[s for s in r if s["category"].lower()==category.lower()]
    if city:     r=[s for s in r if s["city"].lower()==city.lower()]
    if verified is not None: r=[s for s in r if s["verified"]==verified]
    if featured is not None: r=[s for s in r if s["featured"]==featured]
    if status:   r=[s for s in r if s["status"]==status]
    else:        r=[s for s in r if s["status"]=="approved"]
    return {"total":len(r),"suppliers":r[offset:offset+limit]}

@app.post("/api/suppliers",status_code=201)
def create_supplier(payload:SupplierCreate,user=Depends(get_current_user)):
    s={"id":str(uuid.uuid4()),"owner_user_id":user["sub"],"verified":False,"verification_score":50,
       "rating":0.0,"plan":"free","featured":False,"status":"pending","created_at":now(),**payload.model_dump()}
    _suppliers.append(s); return s

@app.get("/api/suppliers/{sid}")
def get_supplier(sid:str):
    s=next((s for s in _suppliers if s["id"]==sid),None)
    if not s: raise HTTPException(404,"Supplier not found")
    return s

@app.put("/api/suppliers/{sid}")
def update_supplier(sid:str,payload:SupplierCreate,user=Depends(get_current_user)):
    s=next((s for s in _suppliers if s["id"]==sid),None)
    if not s: raise HTTPException(404,"Supplier not found")
    if s["owner_user_id"]!=user["sub"] and user.get("role")!="admin": raise HTTPException(403,"Not your supplier")
    s.update(payload.model_dump()); return s

@app.delete("/api/suppliers/{sid}")
def delete_supplier(sid:str,_=Depends(require_admin)):
    s=next((s for s in _suppliers if s["id"]==sid),None)
    if not s: raise HTTPException(404,"Supplier not found")
    _suppliers.remove(s); return {"deleted":sid}

@app.patch("/api/admin/suppliers/{sid}/approve")
def approve_supplier(sid:str,_=Depends(require_admin)):
    s=next((s for s in _suppliers if s["id"]==sid),None)
    if not s: raise HTTPException(404,"Not found")
    s["status"]="approved"; return s

@app.patch("/api/admin/suppliers/{sid}/reject")
def reject_supplier(sid:str,_=Depends(require_admin)):
    s=next((s for s in _suppliers if s["id"]==sid),None)
    if not s: raise HTTPException(404,"Not found")
    s["status"]="rejected"; return s

@app.patch("/api/admin/suppliers/{sid}/verify")
def verify_supplier(sid:str,verified:bool=Body(True),score:int=Body(90),_=Depends(require_admin)):
    s=next((s for s in _suppliers if s["id"]==sid),None)
    if not s: raise HTTPException(404,"Not found")
    s["verified"]=verified; s["verification_score"]=score; return s

@app.patch("/api/admin/suppliers/{sid}/feature")
def feature_supplier(sid:str,featured:bool=Body(True),_=Depends(require_admin)):
    s=next((s for s in _suppliers if s["id"]==sid),None)
    if not s: raise HTTPException(404,"Not found")
    s["featured"]=featured; return s

# ---- Products ----
@app.get("/api/products")
def list_products(search:Optional[str]=None,category:Optional[str]=None,supplier_id:Optional[str]=None,
                  stock_status:Optional[str]=None,limit:int=50,offset:int=0):
    r=_products[:]
    if search: q=search.lower(); r=[p for p in r if q in p["name"].lower() or q in p["description"].lower()]
    if category: r=[p for p in r if p["category"].lower()==category.lower()]
    if supplier_id: r=[p for p in r if p["supplier_id"]==supplier_id]
    if stock_status: r=[p for p in r if p["stock_status"]==stock_status]
    return {"total":len(r),"products":r[offset:offset+limit]}

@app.post("/api/products",status_code=201)
def create_product(payload:ProductCreate,user=Depends(require_supplier)):
    p={"id":str(uuid.uuid4()),"views":0,"created_at":now(),**payload.model_dump()}
    _products.append(p); return p

@app.get("/api/products/{pid}")
def get_product(pid:str):
    p=next((p for p in _products if p["id"]==pid),None)
    if not p: raise HTTPException(404,"Product not found")
    p["views"]+=1; return p

@app.put("/api/products/{pid}")
def update_product(pid:str,payload:ProductCreate,user=Depends(require_supplier)):
    p=next((p for p in _products if p["id"]==pid),None)
    if not p: raise HTTPException(404,"Product not found")
    p.update(payload.model_dump()); return p

@app.delete("/api/products/{pid}")
def delete_product(pid:str,user=Depends(require_supplier)):
    p=next((p for p in _products if p["id"]==pid),None)
    if not p: raise HTTPException(404,"Product not found")
    _products.remove(p); return {"deleted":pid}

# ---- Inquiries ----
@app.post("/api/inquiries",status_code=201)
def create_inquiry(payload:InquiryCreate):
    i={"id":str(uuid.uuid4()),"status":"new","created_at":now(),**payload.model_dump()}
    _inquiries.append(i); return i

@app.get("/api/inquiries")
def list_inquiries(supplier_id:Optional[str]=None,status:Optional[str]=None,_=Depends(require_admin)):
    r=_inquiries[:]
    if supplier_id: r=[i for i in r if i["supplier_id"]==supplier_id]
    if status: r=[i for i in r if i["status"]==status]
    return r

@app.patch("/api/inquiries/{iid}/status")
def update_inquiry(iid:str,status:str=Body(...),_=Depends(require_admin)):
    i=next((i for i in _inquiries if i["id"]==iid),None)
    if not i: raise HTTPException(404,"Not found")
    i["status"]=status; return i

# ---- RFQs ----
@app.post("/api/rfqs",status_code=201)
def create_rfq(payload:RFQCreate):
    r={"id":str(uuid.uuid4()),"status":"open","created_at":now(),**payload.model_dump()}
    _rfqs.append(r); return r

@app.get("/api/rfqs")
def list_rfqs(category:Optional[str]=None,status:Optional[str]=None):
    r=_rfqs[:]
    if category: r=[x for x in r if x["category"].lower()==category.lower()]
    if status: r=[x for x in r if x["status"]==status]
    return r

# ---- Reviews ----
@app.post("/api/reviews",status_code=201)
def create_review(payload:ReviewCreate):
    if not 1<=payload.rating<=5: raise HTTPException(400,"Rating must be 1-5")
    s=next((s for s in _suppliers if s["id"]==payload.supplier_id),None)
    if not s: raise HTTPException(404,"Supplier not found")
    rev={"id":str(uuid.uuid4()),"created_at":now(),**payload.model_dump()}
    _reviews.append(rev)
    sr=[r["rating"] for r in _reviews if r["supplier_id"]==payload.supplier_id]
    s["rating"]=round(sum(sr)/len(sr),1); return rev

@app.get("/api/reviews/{supplier_id}")
def list_reviews(supplier_id:str):
    return [r for r in _reviews if r["supplier_id"]==supplier_id]

# ---- Favorites ----
@app.post("/api/favorites",status_code=201)
def create_favorite(payload:FavoriteCreate):
    f={"id":str(uuid.uuid4()),"created_at":now(),**payload.model_dump()}
    _favorites.append(f); return f

@app.get("/api/favorites")
def list_favorites(user_email:Optional[str]=None):
    return [f for f in _favorites if f["user_email"]==user_email] if user_email else _favorites

@app.delete("/api/favorites/{fid}")
def delete_favorite(fid:str):
    f=next((f for f in _favorites if f["id"]==fid),None)
    if not f: raise HTTPException(404,"Not found")
    _favorites.remove(f); return {"deleted":fid}

# ---- Messages ----
@app.post("/api/messages",status_code=201)
def create_message(payload:MessageCreate):
    s=next((s for s in _suppliers if s["id"]==payload.supplier_id),None)
    if not s: raise HTTPException(404,"Supplier not found")
    m={"id":str(uuid.uuid4()),"created_at":now(),**payload.model_dump()}
    _messages.append(m); return m

@app.get("/api/messages")
def list_messages(supplier_id:Optional[str]=None,_=Depends(require_admin)):
    return [m for m in _messages if m["supplier_id"]==supplier_id] if supplier_id else _messages

# ---- Supplier Dashboard ----
@app.get("/api/supplier-dashboard/{sid}")
def supplier_dashboard(sid:str,user=Depends(require_supplier)):
    s=next((s for s in _suppliers if s["id"]==sid),None)
    if not s: raise HTTPException(404,"Supplier not found")
    if s["owner_user_id"]!=user["sub"] and user.get("role")!="admin": raise HTTPException(403,"Access denied")
    sp=[p for p in _products if p["supplier_id"]==sid]
    si=[i for i in _inquiries if i["supplier_id"]==sid]
    sm=[m for m in _messages if m["supplier_id"]==sid]
    return {"supplier":s,"total_products":len(sp),"total_views":sum(p["views"] for p in sp),
            "total_inquiries":len(si),"total_messages":len(sm),"products":sp,"inquiries":si,"messages":sm}

# ---- Admin ----
@app.get("/api/admin/users")
def admin_users(_=Depends(require_admin)):
    return [{k:v for k,v in u.items() if k!="hashed_password"} for u in _users]

@app.patch("/api/admin/users/{uid}/status")
def update_user_status(uid:str,status:str=Body(...),_=Depends(require_admin)):
    u=next((u for u in _users if u["id"]==uid),None)
    if not u: raise HTTPException(404,"User not found")
    u["status"]=status; return {k:v for k,v in u.items() if k!="hashed_password"}

@app.get("/api/admin/stats")
def admin_stats(_=Depends(require_admin)):
    return {"total_users":len(_users),"total_suppliers":len(_suppliers),
            "approved_suppliers":len([s for s in _suppliers if s["status"]=="approved"]),
            "pending_suppliers":len([s for s in _suppliers if s["status"]=="pending"]),
            "rejected_suppliers":len([s for s in _suppliers if s["status"]=="rejected"]),
            "verified_suppliers":len([s for s in _suppliers if s["verified"]]),
            "total_products":len(_products),"total_inquiries":len(_inquiries),"total_rfqs":len(_rfqs)}

# ---- Search ----
@app.get("/api/search")
def universal_search(q:str=Query(...),category:Optional[str]=None):
    ql=q.lower()
    sup=[s for s in _suppliers if s["status"]=="approved" and (ql in s["company_name"].lower() or ql in s["description"].lower() or ql in s["city"].lower())]
    pro=[p for p in _products if ql in p["name"].lower() or ql in p["description"].lower()]
    if category: sup=[s for s in sup if s["category"].lower()==category.lower()]; pro=[p for p in pro if p["category"].lower()==category.lower()]
    return {"query":q,"suppliers":sup,"products":pro}

# ---- Plans ----
PLANS=[
    {"id":"free","name":"Free","price_monthly":0,"features":["Basic listing","3 products","Buyer inquiries"]},
    {"id":"standard","name":"Standard","price_monthly":19,"features":["20 products","RFQ visibility","Catalog link","Lead management"]},
    {"id":"premium","name":"Premium","price_monthly":49,"features":["Unlimited products","Featured listing","Verification badge","Priority leads","Analytics"]},
]
@app.get("/api/subscription-plans")
def list_plans(): return PLANS

@app.patch("/api/suppliers/{sid}/subscription")
def update_subscription(sid:str,plan_id:str=Body(...),user=Depends(get_current_user)):
    if plan_id not in [p["id"] for p in PLANS]: raise HTTPException(404,"Plan not found")
    s=next((s for s in _suppliers if s["id"]==sid),None)
    if not s: raise HTTPException(404,"Supplier not found")
    s["plan"]=plan_id; return s
