# GoodBooks API - MongoDB Implementation

A FastAPI-based REST API for the GoodBooks-10k dataset with MongoDB backend, featuring books, ratings, tags, and user recommendations.

## 🚀 Features

- **Complete CRUD Operations** for books, ratings, tags, and user data
- **Advanced Search & Filtering** with pagination support
- **Rating System** with aggregation and statistics
- **Tag-based Book Discovery** with relationship mapping
- **User To-Read Lists** with book recommendations
- **API Key Authentication** for protected endpoints
- **Rate Limiting** (60 requests/minute per IP)
- **Request Logging** with JSONL format
- **Health Checks** and metrics endpoints
- **Docker Support** with MongoDB integration

## 📋 API Endpoints

### Books
- `GET /books` - List books with search, filtering, and pagination
- `GET /books/{book_id}` - Get book details
- `GET /books/{book_id}/tags` - Get tags for a book
- `GET /books/{book_id}/ratings/summary` - Get rating statistics

### Authors & Tags
- `GET /authors/{author_name}/books` - Get books by author
- `GET /tags` - List tags with book counts

### Users
- `GET /users/{user_id}/to-read` - Get user's to-read list

### Ratings (Protected)
- `POST /ratings` - Create/update rating (requires API key)

### System
- `GET /healthz` - Health check
- `GET /metrics` - Basic metrics
- `GET /docs` - Interactive API documentation

## 🛠️ Technology Stack

- **FastAPI** - Modern Python web framework
- **MongoDB** - NoSQL database
- **Pydantic** - Data validation and serialization
- **Pandas** - Data processing for ingestion
- **Docker** - Containerization
- **Uvicorn** - ASGI server

## 📦 Installation & Setup

### Option 1: Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Lab-Assignment-1
   ```

2. **Start services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **Load sample data**
   ```bash
   # Wait for MongoDB to be ready, then run:
   docker-compose exec api python ingest/loaddata.py
   ```

4. **Access the application**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - MongoDB Express: http://localhost:8081 (admin/password)

### Option 2: Local Development

1. **Prerequisites**
   - Python 3.11+
   - MongoDB 7.0+
   - Git

2. **Setup Python environment**
   ```bash
   python -m venv myenv
   source myenv/bin/activate  # On Windows: myenv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   export MONGODB_URI="mongodb://localhost:27017"
   export DB_NAME="books"
   export API_KEY="dev-key"
   ```

4. **Start MongoDB**
   ```bash
   # Using Docker
   docker run -d -p 27017:27017 --name mongodb mongo:7.0
   
   # Or install locally
   # Follow MongoDB installation guide for your OS
   ```

5. **Load data**
   ```bash
   python ingest/loaddata.py
   ```

6. **Start the API server**
   ```bash
   uvicorn app.main:app --reload
   ```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `DB_NAME` | `books` | Database name |
| `API_KEY` | `dev-key` | API key for protected endpoints |
| `INGEST_MODE` | `samples` | Data ingestion mode (samples/full) |
| `CSV_BASE` | (empty) | Local CSV directory path |

### Data Ingestion

The `ingest/loaddata.py` script supports multiple modes:

```bash
# Load sample data (default)
python ingest/loaddata.py --mode samples

# Load full dataset
python ingest/loaddata.py --mode full

# Load from local CSV files
python ingest/loaddata.py --mode full --base /path/to/csvs

# Load specific collections only
python ingest/loaddata.py --collections books ratings
```

## 📊 API Usage Examples

### Search Books
```bash
curl "http://localhost:8000/books?q=orwell&year_from=1930&year_to=1950&sort=avg&order=desc&page=1&page_size=10"
```

### Get Book Details
```bash
curl "http://localhost:8000/books/170"
```

### Create Rating (Protected)
```bash
curl -X POST "http://localhost:8000/ratings" \
  -H "x-api-key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 2001, "book_id": 170, "rating": 5}'
```

### Get Rating Summary
```bash
curl "http://localhost:8000/books/170/ratings/summary"
```

## 🗄️ Database Schema

### Collections

1. **books** - Book information and metadata
2. **ratings** - User ratings (1-5 stars)
3. **tags** - Tag definitions
4. **book_tags** - Book-tag relationships
5. **to_read** - User reading lists

### Key Relationships
- `books.book_id` ↔ `ratings.book_id`
- `books.goodreads_book_id` ↔ `book_tags.goodreads_book_id`
- `tags.tag_id` ↔ `book_tags.tag_id`
- `users.user_id` ↔ `to_read.user_id`

## 🔒 Authentication

Protected endpoints require an API key in the `x-api-key` header:

```bash
curl -H "x-api-key: dev-key" http://localhost:8000/ratings
```

## 📈 Monitoring & Logging

- **Health Check**: `GET /healthz`
- **Metrics**: `GET /metrics`
- **Request Logs**: JSONL format printed to stdout
- **Rate Limiting**: 60 requests/minute per IP

## 🐳 Docker Services

| Service | Port | Description |
|---------|------|-------------|
| `api` | 8000 | FastAPI application |
| `mongodb` | 27017 | MongoDB database |
| `mongo-express` | 8081 | MongoDB web interface |

## 🧪 Testing

Access the interactive API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📁 Project Structure

```
Lab-Assignment-1/
├── app/
│   └── main.py              # FastAPI application
├── ingest/
│   └── loaddata.py          # Data ingestion script
├── docker-compose.yml       # Docker services configuration
├── Dockerfile              # API container definition
├── mongo-init.js           # MongoDB initialization script
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is part of an Advanced Database Systems lab assignment.

## 🆘 Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   - Ensure MongoDB is running
   - Check connection string in environment variables
   - Verify network connectivity

2. **API Key Authentication Failed**
   - Verify `x-api-key` header is set correctly
   - Check `API_KEY` environment variable

3. **Data Loading Issues**
   - Ensure CSV files are accessible
   - Check MongoDB is ready before running ingestion
   - Verify network connectivity for remote CSV URLs

4. **Docker Issues**
   - Ensure Docker and Docker Compose are installed
   - Check port conflicts (8000, 27017, 8081)
   - Restart services: `docker-compose restart`

### Logs

View application logs:
```bash
# Docker
docker-compose logs -f api

# Local
# Logs are printed to stdout in JSONL format
```

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review API documentation at `/docs`
3. Check application logs
4. Create an issue in the repository
