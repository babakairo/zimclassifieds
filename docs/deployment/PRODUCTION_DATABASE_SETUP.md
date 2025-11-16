# Production Database Setup Guide

## Current Status
- **Development:** SQLite (`zimclassifieds.db`)
- **Production:** PostgreSQL (recommended)

---

## Why PostgreSQL for Production?

### SQLite Limitations:
- ❌ Single writer at a time (blocks concurrent writes)
- ❌ No network access (can't scale horizontally)
- ❌ Limited concurrent connections
- ❌ File-based (no distributed systems)

### PostgreSQL Benefits:
- ✅ Multi-user concurrent access
- ✅ Network-based (multiple servers can connect)
- ✅ ACID compliance with transactions
- ✅ Full-text search
- ✅ JSON/JSONB support
- ✅ Robust replication and backup
- ✅ Free and open source

---

## Option 1: Heroku (Easiest)

### Free Tier Available
```bash
# Install Heroku CLI
# Then deploy with PostgreSQL addon
heroku create zimclassifieds
heroku addons:create heroku-postgresql:mini
```

**Pros:**
- Free tier available
- Automatic backups
- Easy deployment
- Managed infrastructure

**Database URL automatically set as:**
```
DATABASE_URL=postgresql://username:password@host:5432/dbname
```

---

## Option 2: AWS RDS PostgreSQL

### Setup:
1. Go to AWS RDS Console
2. Create PostgreSQL database
3. Choose free tier (db.t3.micro)
4. Note connection details

**Configuration:**
```bash
DATABASE_URL=postgresql://username:password@your-db.region.rds.amazonaws.com:5432/zimclassifieds
```

**Estimated Cost:** ~$15-30/month (after free tier)

---

## Option 3: DigitalOcean Managed Postgres

### Setup:
1. Create database cluster
2. Add connection pool
3. Configure firewall rules

**Configuration:**
```bash
DATABASE_URL=postgresql://doadmin:password@your-db.region.db.ondigitalocean.com:25060/zimclassifieds?sslmode=require
```

**Cost:** Starting at $15/month

---

## Option 4: Railway (Developer Friendly)

### Quick Setup:
```bash
# Railway provides free PostgreSQL
# Auto-deploys from GitHub
# Free tier: 500 hours/month
```

**Pros:**
- Very easy setup
- Free tier generous
- GitHub integration

---

## Code Changes Required

### 1. Update `requirements.txt`
```txt
# Add PostgreSQL adapter
psycopg2-binary==2.9.9
```

### 2. Update Database Connection in `app.py`

**Current (SQLite):**
```python
import sqlite3

DATABASE = 'zimclassifieds.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db
```

**New (PostgreSQL):**
```python
import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get('DATABASE_URL') or 'postgresql://localhost/zimclassifieds'

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    conn.cursor_factory = RealDictCursor
    return conn
```

### 3. SQL Syntax Changes

**SQLite → PostgreSQL differences:**

| Feature | SQLite | PostgreSQL |
|---------|---------|------------|
| Auto-increment | `AUTOINCREMENT` | `SERIAL` or `GENERATED ALWAYS AS IDENTITY` |
| Text type | `TEXT` | `TEXT` or `VARCHAR(n)` |
| Boolean | `INTEGER (0/1)` | `BOOLEAN` |
| Timestamp | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` ✅ |
| BLOB | `BLOB` | `BYTEA` |

**Example Update:**
```sql
-- SQLite
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_verified INTEGER DEFAULT 0
);

-- PostgreSQL
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email_verified BOOLEAN DEFAULT FALSE
);
```

---

## Migration Steps

### Step 1: Install PostgreSQL Locally (Testing)
```bash
# Windows: Download from postgresql.org
# Or use Docker:
docker run --name postgres-test -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres
```

### Step 2: Install psycopg2
```bash
pip install psycopg2-binary
```

### Step 3: Export SQLite Data
```bash
# Use this script (I'll create it)
python migrate_to_postgres.py
```

### Step 4: Test Locally
```bash
# Set environment variable
$env:DATABASE_URL="postgresql://localhost/zimclassifieds"
python app.py
```

### Step 5: Deploy to Production
```bash
# Set production DATABASE_URL
# Run migrations
# Test thoroughly
```

---

## Recommended Production Setup

### For Small-Medium Traffic (0-10k users):
- **Database:** Heroku Postgres or Railway (Free/Starter)
- **Server:** Heroku Web dyno or Railway
- **File Storage:** AWS S3 or Cloudinary
- **Cost:** $0-15/month

### For Medium-High Traffic (10k-100k users):
- **Database:** AWS RDS PostgreSQL (t3.small)
- **Server:** AWS EC2 or DigitalOcean Droplet
- **File Storage:** AWS S3
- **CDN:** CloudFlare
- **Cost:** $50-150/month

### For High Traffic (100k+ users):
- **Database:** AWS RDS PostgreSQL (Multi-AZ, replica)
- **Server:** Multiple instances behind load balancer
- **Cache:** Redis
- **File Storage:** AWS S3 + CloudFront CDN
- **Cost:** $500+/month

---

## Quick Start: Heroku Deployment (Recommended)

### 1. Install Heroku CLI
```bash
# Download from heroku.com/cli
```

### 2. Prepare for Deployment
```bash
cd Z:\AWS\classifieds

# Create Procfile
echo "web: gunicorn app:app" > Procfile

# Add to requirements.txt
echo "gunicorn==21.2.0" >> requirements.txt
echo "psycopg2-binary==2.9.9" >> requirements.txt

# Create runtime.txt
echo "python-3.11.0" > runtime.txt
```

### 3. Initialize Git (if not already)
```bash
git init
git add .
git commit -m "Initial commit"
```

### 4. Create Heroku App
```bash
heroku login
heroku create zimclassifieds
heroku addons:create heroku-postgresql:mini
```

### 5. Set Config Variables
```bash
heroku config:set SECRET_KEY="your-secret-key-here"
heroku config:set FLASK_ENV="production"
```

### 6. Deploy
```bash
git push heroku main
heroku run python migrate_db.py
heroku open
```

---

## Environment Variables Needed

```bash
# Production settings
export DATABASE_URL="postgresql://..."
export SECRET_KEY="random-secret-key-here"
export FLASK_ENV="production"
export STRIPE_SECRET_KEY="sk_live_..."
export STRIPE_PUBLISHABLE_KEY="pk_live_..."
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export S3_BUCKET="zimclassifieds-uploads"
```

---

## Next Steps

1. **Choose a hosting platform** (Heroku recommended for easy start)
2. **I'll create migration scripts** to convert SQLite → PostgreSQL
3. **Update code** for PostgreSQL compatibility
4. **Test locally** with PostgreSQL
5. **Deploy to production**

Would you like me to:
- Create the PostgreSQL migration script?
- Set up Heroku deployment files?
- Update app.py for PostgreSQL support?
