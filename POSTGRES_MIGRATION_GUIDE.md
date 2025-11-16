# PostgreSQL Migration & Deployment Guide

## ✅ What's Been Done

1. ✅ Created `database.py` - Smart database adapter (works with SQLite OR PostgreSQL)
2. ✅ Created `create_postgres_schema.py` - PostgreSQL schema creator
3. ✅ Created `migrate_to_postgres.py` - Data migration tool
4. ✅ Updated `requirements.txt` - Added psycopg2-binary
5. ✅ Created `Procfile` - For Heroku deployment
6. ✅ Created `runtime.txt` - Python version for Heroku
7. ✅ Installed psycopg2-binary locally

---

## 🚀 Quick Start Options

### Option A: Deploy to Heroku (Easiest - Recommended)

#### Step 1: Install Heroku CLI
Download from: https://devcenter.heroku.com/articles/heroku-cli

#### Step 2: Login and Create App
```bash
cd Z:\AWS\classifieds
heroku login
heroku create zimclassifieds-prod
```

#### Step 3: Add PostgreSQL Database
```bash
# Free tier (10,000 rows limit)
heroku addons:create heroku-postgresql:mini

# Check database URL
heroku config:get DATABASE_URL
```

#### Step 4: Set Environment Variables
```bash
heroku config:set SECRET_KEY="your-random-secret-key-here"
heroku config:set FLASK_ENV="production"
```

#### Step 5: Deploy
```bash
git add .
git commit -m "Add PostgreSQL support"
git push heroku main
```

#### Step 6: Create Database Tables
```bash
heroku run python create_postgres_schema.py
```

#### Step 7: Open Your App
```bash
heroku open
```

---

### Option B: Test PostgreSQL Locally

#### Step 1: Install PostgreSQL
- Windows: Download from https://www.postgresql.org/download/windows/
- Or use Docker: `docker run --name postgres -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres`

#### Step 2: Create Database
```bash
# Using psql command line
psql -U postgres
CREATE DATABASE zimclassifieds;
\q
```

#### Step 3: Set Environment Variable
```powershell
$env:DATABASE_URL="postgresql://postgres:password@localhost:5432/zimclassifieds"
```

#### Step 4: Create Tables
```bash
python create_postgres_schema.py
```

#### Step 5: Migrate Data (if you have existing data)
```bash
python migrate_to_postgres.py
```

#### Step 6: Run App
```bash
python app.py
```

---

### Option C: Deploy to Railway (Easy Alternative)

#### Step 1: Sign Up
Go to https://railway.app and sign up

#### Step 2: Create New Project
- Click "New Project"
- Select "Deploy from GitHub"
- Connect your zimclassifieds repository

#### Step 3: Add PostgreSQL
- Click "New" → "Database" → "PostgreSQL"
- Railway automatically sets DATABASE_URL

#### Step 4: Deploy
- Railway auto-deploys from your main branch
- Create tables: Run `python create_postgres_schema.py` in Railway terminal

---

## 🔄 Migration Steps (Detailed)

### If You Have Existing SQLite Data:

#### Step 1: Backup SQLite Database
```powershell
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
Copy-Item zimclassifieds.db "zimclassifieds_backup_$stamp.db"
```

#### Step 2: Set PostgreSQL URL
```powershell
# Local PostgreSQL
$env:DATABASE_URL="postgresql://username:password@localhost:5432/zimclassifieds"

# Or Heroku (get from: heroku config:get DATABASE_URL)
$env:DATABASE_URL="postgresql://..."
```

#### Step 3: Create PostgreSQL Schema
```bash
python create_postgres_schema.py
```

Expected output:
```
Connecting to PostgreSQL database...
Creating tables...
✅ PostgreSQL schema created successfully!
```

#### Step 4: Migrate Data
```bash
python migrate_to_postgres.py
```

Expected output:
```
📋 Migrating table: users
   ✅ Migrated 5 rows
📋 Migrating table: sellers
   ✅ Migrated 3 rows
...
✅ Migration completed successfully!
📊 Total rows migrated: 125
```

#### Step 5: Verify Migration
```bash
python view_database.py
# Choose option 4 for quick stats
```

---

## 🧪 Testing the Migration

### Test Database Connection
```bash
python -c "from database import get_db, DB_TYPE; print(f'Database type: {DB_TYPE}'); db = get_db(); print('✅ Connection successful')"
```

### Expected Output (PostgreSQL):
```
Database type: postgresql
✅ Connection successful
```

### Expected Output (SQLite - when DATABASE_URL not set):
```
Database type: sqlite
✅ Connection successful
```

---

## 🔧 Troubleshooting

### Error: "psycopg2 not installed"
```bash
pip install psycopg2-binary
```

### Error: "DATABASE_URL not set"
```powershell
# Set it temporarily
$env:DATABASE_URL="postgresql://..."

# Or add to your script
# Create .env file:
echo "DATABASE_URL=postgresql://..." > .env
```

### Error: "Connection refused"
- Check PostgreSQL is running: `pg_isready`
- Check firewall settings
- Verify credentials

### Error: "SSL connection required"
Update database.py connection (already handled in the code)

---

## 📊 Comparing SQLite vs PostgreSQL

| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| **Connection** | File-based | Network-based |
| **Concurrent Writes** | ❌ Single only | ✅ Multiple |
| **Scalability** | ❌ Limited | ✅ Excellent |
| **Deployment** | Easy | Requires server |
| **Best For** | Development | Production |

---

## 🎯 Next Steps

### For Development:
1. Keep using SQLite (no DATABASE_URL set)
2. Test locally as usual
3. Everything works automatically

### For Production:
1. Choose hosting: Heroku, Railway, AWS, or DigitalOcean
2. Set up PostgreSQL database
3. Set DATABASE_URL environment variable
4. Deploy app
5. Run `create_postgres_schema.py`
6. (Optional) Migrate existing data with `migrate_to_postgres.py`

---

## 🚨 Important Notes

1. **Development uses SQLite automatically** - No changes needed for local dev
2. **Production uses PostgreSQL** - Just set DATABASE_URL environment variable
3. **Same code works for both** - The database.py adapter handles differences
4. **Data migration is optional** - Only needed if you have existing data to move

---

## 💡 Quick Commands Reference

```bash
# Check current database type
python -c "from database import DB_TYPE; print(DB_TYPE)"

# Create PostgreSQL tables
python create_postgres_schema.py

# Migrate data from SQLite to PostgreSQL
python migrate_to_postgres.py

# View database (works with both)
python view_database.py

# Deploy to Heroku
git push heroku main

# View Heroku logs
heroku logs --tail

# Access Heroku database
heroku pg:psql
```

---

## ✅ Ready to Deploy?

Choose your deployment method:
- **Heroku**: Follow "Option A" above (easiest, free tier available)
- **Railway**: Follow "Option C" above (modern, generous free tier)
- **AWS/DigitalOcean**: See PRODUCTION_DATABASE_SETUP.md for detailed guide

**Current Status:**
- ✅ Code ready for PostgreSQL
- ✅ Migration scripts created
- ✅ Dependencies installed
- ✅ Deployment files created
- 🎯 Ready to deploy!
