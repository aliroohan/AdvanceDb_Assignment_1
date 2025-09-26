import pandas as pd
import pymongo
from dotenv import load_dotenv
import os

load_dotenv()
def connect_to_db():
    client = pymongo.MongoClient(os.getenv("MONGODB_URI"))
    db = client["books"]
    collection = db["books"]
    return client, db, collection

def _coerce_dtypes(df: pd.DataFrame, dtypes: dict) -> pd.DataFrame:
    cols = [c for c in dtypes.keys() if c in df.columns]
    df = df[cols].copy()
    for col, typ in dtypes.items():
        if col not in df.columns:
            continue
        if typ == "long":
            df.loc[:, col] = pd.to_numeric(df[col], errors="coerce")
            df = df.dropna(subset=[col])
            df.loc[:, col] = df[col].astype("int64")
        elif typ == "double":
            df.loc[:, col] = pd.to_numeric(df[col], errors="coerce")
            df.loc[:, col] = df[col].astype("float64")
        elif typ == "string":
            df.loc[:, col] = df[col].astype(str)
    return df

def load_data(file_path: str, dtypes: dict):
    if file_path.startswith("http://") or file_path.startswith("https://"):
        df = pd.read_csv(file_path)
    else:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        df = pd.read_csv(file_path)
    if dtypes:
        df = _coerce_dtypes(df, dtypes)
    return df

def main():
    client, db, collection = connect_to_db()
    arr = ['books', 'ratings', 'tags', 'book_tags', 'to_read']
    dtype_map = {
        'books': {
            'book_id': 'long',
            'goodreads_book_id': 'long',
            'title': 'string',
            'authors': 'string',
            'original_publication_year': 'long',
            'average_rating': 'double',
            'ratings_count': 'long',
            'image_url': 'string',
            'small_image_url': 'string',
        },
        'ratings': {
            'user_id': 'long',
            'book_id': 'long',
            'rating': 'long',
        },
        'tags': {
            'tag_id': 'long',
            'tag_name': 'string',
        },
        'book_tags': {
            'goodreads_book_id': 'long',
            'tag_id': 'long',
            'count': 'long',
        },
        'to_read': {
            'user_id': 'long',
            'book_id': 'long',
        },
    }
    for i in arr:
        collection = db[i]
        data = load_data(f"https://raw.githubusercontent.com/zygmuntz/goodbooks-10k/master/samples/{i}.csv", dtype_map.get(i, {}))
        for index, row in data.iterrows():
            collection.insert_one(row.to_dict())
    print("Data loaded successfully")

if __name__ == "__main__":
    main()