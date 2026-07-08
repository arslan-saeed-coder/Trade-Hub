from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
import os
import uuid
from urllib.parse import quote_plus

import jwt
from dotenv import load_dotenv
from fastapi import Body, Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, Integer, String, Text, create_engine,
    func, extract
)
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "tradehub-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MIN = int(os.getenv("JWT_EXPIRE_MIN", str(60 * 24 * 7)))
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5500")
ADMIN_WHATSAPP = os.getenv("ADMIN_WHATSAPP", "923009999999")
STORE_NAME = os.getenv("STORE_NAME", "My Store")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@tradehubpk.com").lower()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DATABASE_URL") or "sqlite:///./tradehub_store.db"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

connect_args: Dict[str, Any] = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif "supabase" in DATABASE_URL and "sslmode=" not in DATABASE_URL:
    connect_args = {"sslmode": "require"}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

app = FastAPI(title="My Store API", version="5.0.0", docs_url="/docs")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5500", "http://127.0.0.1:5500", "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)
VALID_ORDER_STATUSES = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"]

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(120), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default="customer", index=True)
    phone = Column(String(40), nullable=True)
    status = Column(String(30), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    orders = relationship("Order", back_populates="customer")

class Category(Base):
    __tablename__ = "categories"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(120), nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    products = relationship("Product", back_populates="category_ref")

class Product(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(180), nullable=False, index=True)
    category_id = Column(String, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    category = Column(String(120), nullable=False, index=True)
    price = Column(Float, nullable=False, default=0)
    stock = Column(Integer, nullable=False, default=0)
    image = Column(Text, nullable=True)
    description = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default="active", index=True)
    views = Column(Integer, nullable=False, default=0)
    owner_label = Column(String(160), nullable=False, default="Sold by My Store (Verified Seller)")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    category_ref = relationship("Category", back_populates="products")
    orders = relationship("Order", back_populates="product")

class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(40), nullable=False, unique=True, index=True)
    customer_user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    customer_name = Column(String(140), nullable=False)
    phone = Column(String(40), nullable=False)
    email = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    address = Column(Text, nullable=False)
    product_id = Column(String, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    product_name = Column(String(180), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    order_status = Column(String(30), nullable=False, default="pending", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    customer = relationship("User", back_populates="orders")
    product = relationship("Product", back_populates="orders")

class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6)
    phone: Optional[str] = None
    role: str = "customer"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ProductCreate(BaseModel):
    name: str = Field(min_length=2)
    category: str = Field(min_length=2)
    price: float = Field(ge=0)
    stock: int = Field(ge=0)
    image: Optional[str] = None
    description: str = Field(min_length=3)
    status: str = "active"

class ProductUpdate(ProductCreate):
    pass

class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=2)
    phone: str = Field(min_length=7)
    email: Optional[EmailStr] = None
    city: str = Field(min_length=2)
    address: str = Field(min_length=8)
    product_id: str
    quantity: int = Field(gt=0)
    notes: Optional[str] = ""

class StatusUpdate(BaseModel):
    status: str


def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(pw: str) -> str:
    return pwd_ctx.hash(pw)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


def create_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MIN)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")


def public_user(u: User) -> dict:
    return {"id": u.id, "name": u.name, "email": u.email, "role": u.role, "phone": u.phone, "status": u.status, "created_at": u.created_at.isoformat() if u.created_at else None}


def product_dict(p: Product) -> dict:
    return {
        "id": p.id, "name": p.name, "category": p.category, "price": p.price, "stock": p.stock,
        "image": p.image, "description": p.description, "status": p.status, "views": p.views,
        "seller_name": STORE_NAME, "seller_label": "Sold by My Store (Verified Seller)",
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


def order_dict(o: Order) -> dict:
    return {
        "id": o.id, "order_id": o.order_id, "customer_user_id": o.customer_user_id,
        "customer_name": o.customer_name, "phone": o.phone, "email": o.email, "city": o.city,
        "address": o.address, "product_id": o.product_id, "product_name": o.product_name,
        "quantity": o.quantity, "unit_price": o.unit_price, "total_price": o.total_price,
        "notes": o.notes or "", "order_status": o.order_status,
        "created_at": o.created_at.isoformat() if o.created_at else None,
        "updated_at": o.updated_at.isoformat() if o.updated_at else None,
    }


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(db_session)) -> User:
    if not creds:
        raise HTTPException(401, "Not authenticated")
    payload = decode_token(creds.credentials)
    user = db.get(User, payload.get("sub"))
    if not user or user.status != "active":
        raise HTTPException(401, "User not found or inactive")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(403, "Admin access required")
    return user


def require_customer(user: User = Depends(get_current_user)) -> User:
    if user.role not in ("customer", "admin"):
        raise HTTPException(403, "Customer access required")
    return user


def get_or_create_category(db: Session, name: str) -> Category:
    clean = name.strip()
    cat = db.query(Category).filter(func.lower(Category.name) == clean.lower()).first()
    if cat:
        return cat
    cat = Category(name=clean)
    db.add(cat)
    db.flush()
    return cat


def generate_order_id(db: Session) -> str:
    prefix = datetime.now(timezone.utc).strftime("ORD-%Y%m%d")
    for _ in range(10):
        candidate = f"{prefix}-{uuid.uuid4().hex[:8].upper()}"
        if not db.query(Order).filter(Order.order_id == candidate).first():
            return candidate
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"


def build_whatsapp_url(order: Order) -> str:
    message = (
        f"New Order Received\n"
        f"Order ID: {order.order_id}\n"
        f"Product: {order.product_name}\n"
        f"Quantity: {order.quantity}\n"
        f"Total Price: PKR {order.total_price:,.0f}\n"
        f"Customer Name: {order.customer_name}\n"
        f"Phone: {order.phone}\n"
        f"City: {order.city}\n"
        f"Address: {order.address}"
    )
    return f"https://wa.me/{ADMIN_WHATSAPP}?text={quote_plus(message)}"


def seed_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = db.query(User).filter(func.lower(User.email) == ADMIN_EMAIL).first()
        if not admin:
            db.add(User(name="Store Owner", email=ADMIN_EMAIL, hashed_password=hash_password(ADMIN_PASSWORD), role="admin", status="active"))
        if db.query(Product).count() == 0:
            samples = [
                ("Samsung Galaxy Fast Charger", "Mobile Accessories", 2499, 35, "25W USB-C fast charger for Samsung and Android devices.", "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?auto=format&fit=crop&w=900&q=80"),
                ("Gaming RGB Headset", "Gaming", 3999, 22, "Comfortable over-ear gaming headset with mic and RGB lighting.", "https://images.unsplash.com/photo-1599669454699-248893623440?auto=format&fit=crop&w=900&q=80"),
                ("Wireless Bluetooth Earbuds", "Audio", 2999, 50, "Compact TWS earbuds with clear sound and charging case.", "https://images.unsplash.com/photo-1606220945770-b5b6c2c55bf1?auto=format&fit=crop&w=900&q=80"),
                ("USB-C Braided Cable", "Mobile Accessories", 799, 120, "Durable fast charging USB-C cable for daily use.", "https://images.unsplash.com/photo-1618384887929-16ec33fab9ef?auto=format&fit=crop&w=900&q=80"),
                ("Portable Bluetooth Speaker", "Audio", 4499, 18, "Powerful portable speaker with deep bass and long battery life.", "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?auto=format&fit=crop&w=900&q=80"),
                ("Laptop Cooling Pad", "Computing", 2799, 28, "Slim cooling pad for laptops with quiet fans and adjustable height.", "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=900&q=80"),
            ]
            for name, category, price, stock, description, image in samples:
                cat = get_or_create_category(db, category)
                db.add(Product(name=name, category=cat.name, category_id=cat.id, price=price, stock=stock, description=description, image=image, status="active"))
        db.commit()
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    seed_data()

@app.get("/")
def root():
    return {"ok": True, "app": "My Store", "mode": "single-owner e-commerce", "database": "sqlalchemy"}

@app.post("/api/auth/register", status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(db_session)):
    if db.query(User).filter(func.lower(User.email) == payload.email.lower()).first():
        raise HTTPException(400, "Email already registered")
    user = User(name=payload.name.strip(), email=payload.email.lower(), hashed_password=hash_password(payload.password), role="customer", phone=payload.phone, status="active")
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token({"sub": user.id, "role": user.role, "email": user.email})
    return {"token": token, "user": public_user(user)}

@app.post("/api/auth/login")
def login(payload: LoginRequest, db: Session = Depends(db_session)):
    user = db.query(User).filter(func.lower(User.email) == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(401, "Invalid email or password")
    if user.status != "active":
        raise HTTPException(403, "Account disabled")
    token = create_token({"sub": user.id, "role": user.role, "email": user.email})
    return {"token": token, "user": public_user(user)}

@app.get("/api/auth/me")
def me(user: User = Depends(get_current_user)):
    return public_user(user)

@app.get("/api/stats")
def public_stats(db: Session = Depends(db_session)):
    return {"total_products": db.query(Product).filter(Product.status == "active").count(), "store_name": STORE_NAME, "verified_seller": True}

@app.get("/api/categories")
def list_categories(db: Session = Depends(db_session)):
    rows = db.query(Category).order_by(Category.name.asc()).all()
    if rows:
        return [c.name for c in rows]
    return [r[0] for r in db.query(Product.category).filter(Product.status == "active").distinct().order_by(Product.category.asc()).all()]

@app.get("/api/products")
def list_products(search: Optional[str] = None, category: Optional[str] = None, status: Optional[str] = None, limit: int = 50, offset: int = 0, db: Session = Depends(db_session)):
    q = db.query(Product)
    if status:
        q = q.filter(Product.status == status)
    else:
        q = q.filter(Product.status == "active")
    if search:
        like = f"%{search.lower()}%"
        q = q.filter(func.lower(Product.name).like(like) | func.lower(Product.description).like(like) | func.lower(Product.category).like(like))
    if category:
        q = q.filter(func.lower(Product.category) == category.lower())
    total = q.count()
    rows = q.order_by(Product.created_at.desc()).offset(offset).limit(limit).all()
    return {"total": total, "products": [product_dict(p) for p in rows]}

@app.get("/api/products/{pid}")
def get_product(pid: str, db: Session = Depends(db_session)):
    p = db.query(Product).filter(Product.id == pid, Product.status == "active").first()
    if not p:
        raise HTTPException(404, "Product not found")
    p.views += 1
    db.commit()
    db.refresh(p)
    return product_dict(p)

@app.post("/api/products", status_code=201)
def create_product(payload: ProductCreate, _: User = Depends(require_admin), db: Session = Depends(db_session)):
    if payload.status not in ("active", "inactive"):
        raise HTTPException(400, "Product status must be active or inactive")
    cat = get_or_create_category(db, payload.category)
    product = Product(**payload.model_dump(), category=cat.name, category_id=cat.id, owner_label="Sold by My Store (Verified Seller)")
    db.add(product)
    db.commit()
    db.refresh(product)
    return product_dict(product)

@app.put("/api/products/{pid}")
def update_product(pid: str, payload: ProductUpdate, _: User = Depends(require_admin), db: Session = Depends(db_session)):
    product = db.get(Product, pid)
    if not product:
        raise HTTPException(404, "Product not found")
    if payload.status not in ("active", "inactive"):
        raise HTTPException(400, "Product status must be active or inactive")
    cat = get_or_create_category(db, payload.category)
    for k, v in payload.model_dump().items():
        setattr(product, k, v)
    product.category = cat.name
    product.category_id = cat.id
    product.owner_label = "Sold by My Store (Verified Seller)"
    product.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(product)
    return product_dict(product)

@app.delete("/api/products/{pid}")
def delete_product(pid: str, _: User = Depends(require_admin), db: Session = Depends(db_session)):
    product = db.get(Product, pid)
    if not product:
        raise HTTPException(404, "Product not found")
    db.delete(product)
    db.commit()
    return {"deleted": pid}

@app.post("/api/orders", status_code=201)
def create_order(payload: OrderCreate, user: User = Depends(require_customer), db: Session = Depends(db_session)):
    product = db.query(Product).filter(Product.id == payload.product_id, Product.status == "active").with_for_update().first()
    if not product:
        raise HTTPException(404, "Product not found")
    if product.stock < payload.quantity:
        raise HTTPException(400, "Not enough stock available")
    total = round(product.price * payload.quantity, 2)
    order = Order(
        order_id=generate_order_id(db), customer_user_id=user.id,
        customer_name=payload.customer_name.strip(), phone=payload.phone.strip(), email=str(payload.email) if payload.email else None,
        city=payload.city.strip(), address=payload.address.strip(), product_id=product.id, product_name=product.name,
        quantity=payload.quantity, unit_price=product.price, total_price=total, notes=(payload.notes or "").strip(), order_status="pending"
    )
    product.stock -= payload.quantity
    db.add(order)
    db.commit()
    db.refresh(order)
    return {"order": order_dict(order), "whatsapp_url": build_whatsapp_url(order)}

@app.get("/api/orders")
def list_orders(status: Optional[str] = None, user: User = Depends(get_current_user), db: Session = Depends(db_session)):
    q = db.query(Order)
    if user.role != "admin":
        q = q.filter(Order.customer_user_id == user.id)
    if status:
        q = q.filter(Order.order_status == status)
    return [order_dict(o) for o in q.order_by(Order.created_at.desc()).all()]

@app.patch("/api/orders/{order_id}/status")
def update_order_status(order_id: str, payload: StatusUpdate = Body(...), _: User = Depends(require_admin), db: Session = Depends(db_session)):
    status_value = payload.status
    if status_value not in VALID_ORDER_STATUSES:
        raise HTTPException(400, f"Invalid status. Use one of: {', '.join(VALID_ORDER_STATUSES)}")
    order = db.query(Order).filter((Order.order_id == order_id) | (Order.id == order_id)).first()
    if not order:
        raise HTTPException(404, "Order not found")
    order.order_status = status_value
    order.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(order)
    return order_dict(order)

@app.delete("/api/orders/{order_id}")
def delete_order(order_id: str, _: User = Depends(require_admin), db: Session = Depends(db_session)):
    order = db.query(Order).filter((Order.order_id == order_id) | (Order.id == order_id)).first()
    if not order:
        raise HTTPException(404, "Order not found")
    db.delete(order)
    db.commit()
    return {"deleted": order_id}

@app.get("/api/admin/users")
def admin_users(_: User = Depends(require_admin), db: Session = Depends(db_session)):
    return [public_user(u) for u in db.query(User).order_by(User.created_at.desc()).all()]

@app.get("/api/admin/stats")
def admin_stats(_: User = Depends(require_admin), db: Session = Depends(db_session)):
    today = datetime.now(timezone.utc).date()
    month_start = today.replace(day=1)
    by_status = {s: db.query(Order).filter(Order.order_status == s).count() for s in VALID_ORDER_STATUSES}
    revenue = db.query(func.coalesce(func.sum(Order.total_price), 0)).filter(Order.order_status != "cancelled").scalar() or 0
    today_orders = db.query(Order).filter(func.date(Order.created_at) == today.isoformat()).count()
    monthly_orders = db.query(Order).filter(Order.created_at >= datetime.combine(month_start, datetime.min.time()).replace(tzinfo=timezone.utc)).count()
    monthly = []
    current_year = datetime.now(timezone.utc).year
    for m in range(1, 13):
        orders_count = db.query(Order).filter(extract("year", Order.created_at) == current_year, extract("month", Order.created_at) == m).count()
        sales = db.query(func.coalesce(func.sum(Order.total_price), 0)).filter(extract("year", Order.created_at) == current_year, extract("month", Order.created_at) == m, Order.order_status != "cancelled").scalar() or 0
        monthly.append({"month": m, "orders": orders_count, "sales": round(float(sales), 2)})
    recent_orders = db.query(Order).order_by(Order.created_at.desc()).limit(10).all()
    return {
        "total_products": db.query(Product).count(), "total_orders": db.query(Order).count(),
        "pending_orders": by_status["pending"], "confirmed_orders": by_status["confirmed"],
        "processing_orders": by_status["processing"], "shipped_orders": by_status["shipped"],
        "delivered_orders": by_status["delivered"], "cancelled_orders": by_status["cancelled"],
        "today_orders": today_orders, "monthly_orders": monthly_orders, "revenue": round(float(revenue), 2),
        "status_distribution": by_status, "monthly": monthly,
        "recent_orders": [order_dict(o) for o in recent_orders]
    }

@app.get("/api/search")
def search(q: str = Query(...), category: Optional[str] = None, db: Session = Depends(db_session)):
    return list_products(search=q, category=category, db=db)
