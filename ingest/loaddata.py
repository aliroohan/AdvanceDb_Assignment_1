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

def load_data(file_path):
    return pd.read_csv(file_path)

def main():
    client, db, collection = connect_to_db()
    arr = ['books', 'ratings', 'tags', 'book_tags', 'to_read']
    for i in arr:
        collection = db[i]
        data = load_data(f"https://raw.githubusercontent.com/zygmuntz/goodbooks-10k/master/samples/{i}.csv")
        for index, row in data.iterrows():
            collection.insert_one(row.to_dict())
    print("Data loaded successfully")

if __name__ == "__main__":
    main()