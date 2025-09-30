// MongoDB initialization script
db = db.getSiblingDB('books');

// Create collections with validation
db.createCollection('books', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: [
        "book_id",
        "goodreads_book_id", 
        "title",
        "authors",
        "original_publication_year",
        "average_rating",
        "ratings_count",
        "image_url",
        "small_image_url"
      ],
      properties: {
        book_id: { bsonType: "long" },
        goodreads_book_id: { bsonType: "long" },
        title: { bsonType: "string" },
        authors: { bsonType: "string" },
        original_publication_year: { bsonType: "long" },
        average_rating: { bsonType: "double" },
        ratings_count: { bsonType: "long" },
        image_url: { bsonType: "string" },
        small_image_url: { bsonType: "string" }
      }
    }
  }
});

db.createCollection('ratings', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["user_id", "book_id", "rating"],
      properties: {
        user_id: { bsonType: "long" },
        book_id: { bsonType: "long" },
        rating: { bsonType: "long" }
      }
    }
  }
});

db.createCollection('tags', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["tag_id", "tag_name"],
      properties: {
        tag_id: { bsonType: "long" },
        tag_name: { bsonType: "string" }
      }
    }
  }
});

db.createCollection('book_tags', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["goodreads_book_id", "tag_id", "count"],
      properties: {
        goodreads_book_id: { bsonType: "long" },
        tag_id: { bsonType: "long" },
        count: { bsonType: "long" }
      }
    }
  }
});

db.createCollection('to_read', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["user_id", "book_id"],
      properties: {
        user_id: { bsonType: "long" },
        book_id: { bsonType: "long" }
      }
    }
  }
});

// Create indexes for better performance
db.books.createIndex({ "book_id": 1 }, { unique: true });
db.books.createIndex({ "goodreads_book_id": 1 });
db.books.createIndex({ "title": "text", "authors": "text" });
db.books.createIndex({ "average_rating": 1 });
db.books.createIndex({ "original_publication_year": 1 });

db.ratings.createIndex({ "user_id": 1, "book_id": 1 }, { unique: true });
db.ratings.createIndex({ "book_id": 1 });
db.ratings.createIndex({ "user_id": 1 });

db.tags.createIndex({ "tag_id": 1 }, { unique: true });
db.tags.createIndex({ "tag_name": 1 });

db.book_tags.createIndex({ "goodreads_book_id": 1, "tag_id": 1 }, { unique: true });
db.book_tags.createIndex({ "tag_id": 1 });

db.to_read.createIndex({ "user_id": 1, "book_id": 1 }, { unique: true });
db.to_read.createIndex({ "user_id": 1 });

print("Database and collections initialized successfully!");
