import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

from database import db, create_document, get_documents
from schemas import DigitalProduct, Order, LibraryItem

app = FastAPI(title="E-Products API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "E-Products Backend Running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
                response["database_name"] = getattr(db, 'name', None)
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# ---------------------------------------------
# Helpers
# ---------------------------------------------

def _serialize(doc: dict):
    if not doc:
        return doc
    d = doc.copy()
    if "_id" in d:
        d["id"] = str(d.pop("_id"))
    return d

# Fallback demo data if DB is not configured
DEMO_PRODUCTS = [
    {
        "title": "Mastering React for Beginners",
        "description": "Interactive e-book with hands-on projects.",
        "price": 29.0,
        "cover_image": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?q=80&w=1200&auto=format&fit=crop",
        "category": "ebook",
        "download_url": None,
        "in_stock": True,
    },
    {
        "title": "Full-Stack Course Bundle",
        "description": "Self-paced video + workbook bundle.",
        "price": 79.0,
        "cover_image": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?q=80&w=1200&auto=format&fit=crop",
        "category": "course",
        "download_url": None,
        "in_stock": True,
    },
]

DEMO_LIBRARY = [
    {
        "title": "Clean Code",
        "kind": "book",
        "platform": "Amazon",
        "link": "https://www.amazon.com/dp/0132350882",
        "thumbnail": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?q=80&w=600&auto=format&fit=crop",
        "author_or_channel": "Robert C. Martin",
        "note": "A classic on writing maintainable software.",
    },
    {
        "title": "React Hooks Crash Course",
        "kind": "video",
        "platform": "YouTube",
        "link": "https://www.youtube.com/results?search_query=react+hooks+crash+course",
        "thumbnail": "https://i.ytimg.com/vi/DPnqb74Smug/maxresdefault.jpg",
        "author_or_channel": "Traversy Media",
        "note": "Great intro to hooks.",
    },
    {
        "title": "Our Planet",
        "kind": "streaming",
        "platform": "Netflix",
        "link": "https://www.netflix.com/title/80049832",
        "thumbnail": "https://images.unsplash.com/photo-1518733057094-95b53143d2a7?q=80&w=1200&auto=format&fit=crop",
        "author_or_channel": "Netflix",
        "note": "Nature documentary (desktop only link).",
    },
]

# ---------------------------------------------
# Products
# ---------------------------------------------

@app.get("/api/products", response_model=List[DigitalProduct])
def list_products():
    try:
        if db is None:
            return DEMO_PRODUCTS
        docs = get_documents("digitalproduct")
        if not docs:
            # If collection empty, show demo
            return DEMO_PRODUCTS
        return [DigitalProduct(**_serialize(d)) for d in docs]
    except Exception:
        return DEMO_PRODUCTS

# ---------------------------------------------
# Orders (simple email checkout)
# ---------------------------------------------

class OrderResponse(BaseModel):
    order_id: str
    message: str

@app.post("/api/order", response_model=OrderResponse)
def create_order(order: Order):
    try:
        data = order.dict()
        if db is not None:
            order_id = create_document("order", data)
        else:
            order_id = "demo-order-id"
        return {"order_id": order_id, "message": "Order received. Check your email for delivery."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------
# Library (third-party recommendations)
# ---------------------------------------------

@app.get("/api/library", response_model=List[LibraryItem])
def list_library(kind: Optional[str] = Query(None, description="Filter by kind: book|video|streaming")):
    try:
        if db is None:
            items = DEMO_LIBRARY
        else:
            filter_q = {"kind": kind} if kind else {}
            docs = get_documents("libraryitem", filter_q)
            items = [LibraryItem(**_serialize(d)) for d in docs] if docs else []
            if not items:
                items = DEMO_LIBRARY
        if kind:
            items = [i for i in items if i["kind"] == kind]
        return items
    except Exception:
        return [i for i in DEMO_LIBRARY if (i["kind"] == kind) or (kind is None)]

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
