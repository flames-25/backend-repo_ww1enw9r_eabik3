import os
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product, Order

app = FastAPI(title="Shop Lite API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProductCreate(Product):
    pass


class ProductOut(Product):
    id: str


class OrderCreate(Order):
    pass


def serialize_doc(doc: dict):
    if not doc:
        return doc
    doc = dict(doc)
    _id = doc.get("_id")
    if isinstance(_id, ObjectId):
        doc["id"] = str(_id)
        del doc["_id"]
    return doc


@app.get("/")
def read_root():
    return {"message": "Shop Lite Backend Running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
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
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# Products Endpoints
@app.get("/api/products", response_model=List[ProductOut])
def list_products():
    if db is None:
        return []
    docs = get_documents("product")
    return [serialize_doc(d) for d in docs]


@app.post("/api/products", response_model=str)
def create_product(product: ProductCreate):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    inserted_id = create_document("product", product)
    return inserted_id


@app.get("/api/products/{product_id}", response_model=ProductOut)
def get_product(product_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        doc = db["product"].find_one({"_id": ObjectId(product_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product id")
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    return serialize_doc(doc)


@app.post("/api/products/seed")
def seed_products():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    count = db["product"].count_documents({})
    if count > 0:
        return {"inserted": 0, "message": "Products already exist"}
    samples = [
        {
            "title": "Minimal Tee",
            "description": "Soft cotton t‑shirt with relaxed fit.",
            "price": 24.00,
            "category": "Apparel",
            "in_stock": True,
            "image": "https://images.unsplash.com/photo-1512436991641-6745cdb1723f?q=80&w=800&auto=format&fit=crop"
        },
        {
            "title": "Everyday Backpack",
            "description": "Water‑resistant with laptop sleeve.",
            "price": 79.00,
            "category": "Bags",
            "in_stock": True,
            "image": "https://images.unsplash.com/photo-1547949003-9792a18a2601?q=80&w=800&auto=format&fit=crop"
        },
        {
            "title": "Ceramic Mug",
            "description": "12oz glazed mug for hot and cold drinks.",
            "price": 14.00,
            "category": "Home",
            "in_stock": True,
            "image": "https://images.unsplash.com/photo-1520975661595-6453be3f7070?q=80&w=800&auto=format&fit=crop"
        },
        {
            "title": "Running Sneakers",
            "description": "Breathable mesh, cushioned sole.",
            "price": 110.00,
            "category": "Footwear",
            "in_stock": True,
            "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?q=80&w=800&auto=format&fit=crop"
        }
    ]
    inserted = 0
    for p in samples:
        create_document("product", p)
        inserted += 1
    return {"inserted": inserted}


# Orders Endpoint
@app.post("/api/orders", response_model=str)
def create_order(order: OrderCreate):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    inserted_id = create_document("order", order)
    return inserted_id


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
