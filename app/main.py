from fastapi import FastAPI, Query, HTTPException, Depends, Request, Response, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import os, time, hashlib, json, threading
from typing import Any, Dict, List, Optional, Tuple


MONGO_URI = os.getenv("MONGO_URI", os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
DB_NAME = os.getenv("DB_NAME", "books")
API_KEY = os.getenv("API_KEY", "dev-key")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
app = FastAPI(title="GoodBooks API (MongoDB)")


class Book(BaseModel):
    book_id: int
    goodreads_book_id: int
    title: str
    authors: str
    original_publication_year: int
    average_rating: float
    ratings_count: int
    image_url: str
    small_image_url: str



class RatingIn(BaseModel):
    user_id: int
    book_id: int
    rating: int = Field(ge=1, le=5)


class Tag(BaseModel):
    tag_id: int
    tag_name: str
    book_count: Optional[int] = None  # Added for /tags endpoint


class BookTag(BaseModel):
    goodreads_book_id: int
    tag_id: int
    count: int


class ToRead(BaseModel):
    user_id: int
    book_id: int


class RatingSummary(BaseModel):
    avg: float 
    count: int
    histogram: Dict[int, int]  # rating -> count


class PaginatedResponse(BaseModel):
    items: List[Any]
    page: int
    page_size: int
    total: int


class ErrorOut(BaseModel):
    detail: str


class StatusResponse(BaseModel):
    status: str  


# --------------------------- Utils ----------------------------
def error(status: int, msg: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"detail": msg})


def require_key(x_api_key: str = Header(alias="x-api-key")):
    """Require x-api-ke1y header for protected endpoints"""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="invalid api key")
    return x_api_key


def validate_pagination(page: int, page_size: int) -> Tuple[int, int]:
    if page < 1:
        raise HTTPException(status_code=400, detail="page must be >= 1")
    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="page_size must be in [1, 100]")
    return page, page_size


def to_safe(doc: Dict[str, Any]) -> Dict[str, Any]:
    if doc is None:
        return doc
    d = dict(doc)
    if "_id" in d:
        d["_id"] = str(d["_id"])
    return d


# --------------------------- Logging --------------------------
_log_lock = threading.Lock()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    t0 = time.time()
    response = None
    try:
        response = await call_next(request)
        return response
    finally:
        dt = int((time.time() - t0) * 1000)
        rec = {
            "route": str(request.url.path),
            "params": dict(request.query_params),
            "status": response.status_code if response else 500,
            "latency_ms": dt,
            "client_ip": request.client.host if request.client else None,
            "ts": int(time.time()),
        }
        # Print JSONL; in real apps, write to file/stream
        with _log_lock:
            print(json.dumps(rec))


ps_start = time.time()
# --------------------------- Endpoints ------------------------
@app.get("/healthz")
def healthz():
    try:
        client.admin.command("ping")
        return {"status": "ok"}
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
def metrics():
    return {"uptime_s": int(time.time() - ps_start)}




@app.get("/books", response_model=PaginatedResponse, responses={400: {"model": ErrorOut}})
def list_books(
    q: Optional[str] = None,
    tag: Optional[str] = None,
    min_avg: Optional[float] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    sort: str = Query("avg", pattern=r"^(avg|ratings_count|year|title)$"),
    order: str = Query("desc", pattern=r"^(asc|desc)$"),
    page: int = 1,
    page_size: int = Query(20, le=100),
):
    page, page_size = validate_pagination(page, page_size)

    filt: Dict[str, Any] = {}
    if q:
        filt["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"authors": {"$regex": q, "$options": "i"}},
        ]
    if min_avg is not None:
        filt["average_rating"] = {"$gte": float(min_avg)}
    year_clause: Dict[str, Any] = {}
    if year_from is not None:
        year_clause["$gte"] = year_from
    if year_to is not None:
        year_clause["$lte"] = year_to
    if year_clause:
        filt["original_publication_year"] = year_clause

    # Optional tag filter via tags -> book_tags -> books
    if tag:
        tag_doc = db.tags.find_one({"tag_name": {"$regex": f"^{tag}$", "$options": "i"}})
        if not tag_doc:
            return {"items": [], "page": page, "page_size": page_size, "total": 0}
        tg_id = tag_doc.get("tag_id")
        gr_ids = list(db.book_tags.find({"tag_id": tg_id}, {"goodreads_book_id": 1}))
        goodreads_ids = [x["goodreads_book_id"] for x in gr_ids]
        if not goodreads_ids:
            return {"items": [], "page": page, "page_size": page_size, "total": 0}
        filt["goodreads_book_id"] = {"$in": goodreads_ids}

    sort_map = {
        "avg": "average_rating",
        "ratings_count": "ratings_count",
        "year": "original_publication_year",
        "title": "title",
    }
    direction = -1 if order == "desc" else 1

    total = db.books.count_documents(filt)
    cursor = (
        db.books.find(filt)
        .sort([(sort_map[sort], direction)])
        .skip((page - 1) * page_size)
        .limit(page_size)
    )
    items = [to_safe(x) for x in cursor]
    return {"items": items, "page": page, "page_size": page_size, "total": total}


@app.get("/books/{book_id}", response_model=Book, responses={404: {"model": ErrorOut}})
def get_book(book_id: int, response: Response):
    doc = db.books.find_one({"book_id": int(book_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="book not found")
    # ETag based on stable fields
    etag_src = f"{doc.get('book_id')}-{doc.get('ratings_count')}-{doc.get('average_rating')}".encode()
    etag = hashlib.md5(etag_src).hexdigest()
    response.headers["ETag"] = etag
    return to_safe(doc)


@app.get("/books/{book_id}/tags", response_model=PaginatedResponse)
def book_tags(book_id: int, page: int = 1, page_size: int = Query(20, le=100)):
    page, page_size = validate_pagination(page, page_size)
    book = db.books.find_one({"book_id": int(book_id)})
    if not book:
        raise HTTPException(status_code=404, detail="book not found")
    gid = book.get("goodreads_book_id")
    tag_ids = [x["tag_id"] for x in db.book_tags.find({"goodreads_book_id": gid}, {"tag_id": 1})]
    total = len(tag_ids)
    slice_ids = tag_ids[(page - 1) * page_size : (page - 1) * page_size + page_size]
    items = [to_safe(t) for t in db.tags.find({"tag_id": {"$in": slice_ids}})]
    return {"items": items, "page": page, "page_size": page_size, "total": total}


@app.get("/authors/{author_name}/books", response_model=PaginatedResponse)
def author_books(author_name: str, exact: bool = False, page: int = 1, page_size: int = Query(20, le=100)):
    page, page_size = validate_pagination(page, page_size)
    if exact:
        filt = {"authors": {"$regex": f"^{author_name}$", "$options": "i"}}
    else:
        filt = {"authors": {"$regex": author_name, "$options": "i"}}
    total = db.books.count_documents(filt)
    items = [to_safe(x) for x in db.books.find(filt).skip((page - 1) * page_size).limit(page_size)]
    return {"items": items, "page": page, "page_size": page_size, "total": total}


@app.get("/tags", response_model=PaginatedResponse)
def list_tags(page: int = 1, page_size: int = Query(20, le=100)):
    page, page_size = validate_pagination(page, page_size)
    total = db.tags.count_documents({})
    tags = list(db.tags.find({}).skip((page - 1) * page_size).limit(page_size))
    # Compute per-tag book counts
    tag_ids = [t["tag_id"] for t in tags]
    counts = {x["_id"]: x["cnt"] for x in db.book_tags.aggregate([
        {"$match": {"tag_id": {"$in": tag_ids}}},
        {"$group": {"_id": "$tag_id", "cnt": {"$sum": 1}}},
    ])}
    items = []
    for t in tags:
        d = to_safe(t)
        d["book_count"] = int(counts.get(t["tag_id"], 0))
        items.append(d)
    return {"items": items, "page": page, "page_size": page_size, "total": total}


@app.get("/users/{user_id}/to-read", response_model=PaginatedResponse)
def user_to_read(user_id: int, page: int = 1, page_size: int = Query(20, le=100)):
    page, page_size = validate_pagination(page, page_size)
    # Join to books
    pipeline = [
        {"$match": {"user_id": int(user_id)}},
        {"$lookup": {
            "from": "books",
            "localField": "book_id",
            "foreignField": "book_id",
            "as": "book",
        }},
        {"$unwind": "$book"},
        {"$skip": (page - 1) * page_size},
        {"$limit": page_size},
    ]
    items = [to_safe(x["book"]) for x in db.to_read.aggregate(pipeline)]
    total = db.to_read.count_documents({"user_id": int(user_id)})
    return {"items": items, "page": page, "page_size": page_size, "total": total}


@app.get("/books/{book_id}/ratings/summary", response_model=RatingSummary)
def ratings_summary(book_id: int):
    pipeline = [
        {"$match": {"book_id": int(book_id)}},
        {"$group": {
            "_id": "$rating",
            "count": {"$sum": 1}
        }}
    ]
    buckets = {i: 0 for i in range(1, 6)}
    total = 0
    sumv = 0
    for g in db.ratings.aggregate(pipeline):
        r = int(g["_id"]) if g["_id"] is not None else 0
        c = int(g["count"]) if g["count"] is not None else 0
        if 1 <= r <= 5:
            buckets[r] = c
            total += c
            sumv += r * c
    avg = (sumv / total) if total else 0.0
    return {"avg": round(avg, 3), "count": total, "histogram": buckets}


@app.post("/ratings", status_code=201, response_model=StatusResponse, responses={
    200: {"model": StatusResponse},
    201: {"model": StatusResponse},
    400: {"model": ErrorOut},
    401: {"model": ErrorOut},
    409: {"model": ErrorOut},
}, dependencies=[Depends(require_key)])
def upsert_rating(r: RatingIn, response: Response):
    res = db.ratings.update_one(
        {"user_id": r.user_id, "book_id": r.book_id},
        {"$set": r.model_dump()},
        upsert=True,
    )
    if res.upserted_id:
        response.status_code = 201
        return {"status": "created"}
    # matched existing
    response.status_code = 200
    return {"status": "updated"}


