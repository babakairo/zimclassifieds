# ZimClassifieds Project Organization

## 📋 Overview
This document explains how the ZimClassifieds project is organized and how it's separated from other projects in your workspace.

## 🗂️ Workspace Structure

Your `Z:\AWS` workspace contains multiple independent projects:

```
Z:\AWS/
├── classifieds/              ✅ ZimClassifieds (main project - tracked in git)
├── landlord-tenant-app/      ⚠️  Separate project (not part of ZimClassifieds)
├── downloads/                📁 General downloads folder
├── app.py                    ⚠️  YouTube-related (not part of ZimClassifieds)
├── youtube.py                ⚠️  YouTube-related (not part of ZimClassifieds)
├── main.py                   ⚠️  YouTube-related (not part of ZimClassifieds)
├── run_youtube.py            ⚠️  YouTube-related (not part of ZimClassifieds)
└── ... (other YouTube files)
```

### ✅ What IS Part of ZimClassifieds
Only files inside `Z:\AWS\classifieds/` are part of the ZimClassifieds project and tracked in the git repository at `babakairo/zimclassifieds`.

### ⚠️ What is NOT Part of ZimClassifieds
- **landlord-tenant-app/** - A separate Flask app for property management
- **YouTube-related files** in the root AWS directory:
  - app.py, youtube.py, main.py, run_youtube.py
  - search_violation.py, test_api.py
  - copyright_guardian.db
  - *.csv files (YouTube data)
  - templates/ folder in root (YouTube templates)

## 📁 ZimClassifieds Clean Structure

The ZimClassifieds project (`Z:\AWS\classifieds/`) is now organized as follows:

```
classifieds/
├── Core Application Files
│   ├── app.py                 # Main Flask application
│   ├── bnpl.py                # Buy Now Pay Later module
│   ├── sellers.py             # Seller management
│   ├── cart.py                # Shopping cart
│   ├── transporters.py        # Courier/logistics
│   ├── database.py            # Database abstraction
│   └── config.json            # Configuration
│
├── Configuration & Deployment
│   ├── requirements.txt       # Python dependencies
│   ├── runtime.txt            # Python version
│   ├── Procfile               # Heroku config
│   ├── .gitignore             # Git ignore rules
│   └── .env.example           # Environment template
│
├── Documentation (docs/)
│   ├── bnpl/                  # BNPL system docs
│   │   ├── BNPL_IMPLEMENTATION.md
│   │   ├── BNPL_CASH_COLLECTION_GUIDE.md
│   │   ├── BNPL_CHECKOUT_INTEGRATION.md
│   │   ├── BNPL_NAVIGATION_UPDATE.md
│   │   └── BNPL_QUICK_START.md
│   ├── deployment/            # Deployment guides
│   │   ├── DEPLOYMENT.md
│   │   ├── POSTGRES_MIGRATION_GUIDE.md
│   │   ├── PRODUCTION_DATABASE_SETUP.md
│   │   └── MIGRATION_COMPLETE.md
│   ├── guides/                # User guides
│   │   ├── QUICK_START.md
│   │   ├── STRIPE_SETUP.md
│   │   └── COMPETITIVE_STRATEGY.md
│   └── *.md                   # Project status documents
│
├── Utility Scripts (scripts/)
│   ├── seed_marketplace.py    # Test data generator
│   ├── migrate_to_postgres.py # Database migration
│   ├── check_db.py            # Database viewer
│   ├── test_functionality.py  # Integration tests
│   └── view_database.py       # Database inspector
│
├── Templates (templates/)
│   ├── base.html              # Base template
│   ├── products/              # Product pages
│   ├── sellers/               # Seller portal
│   ├── cart/                  # Shopping cart
│   ├── checkout/              # Checkout flow
│   ├── bnpl/                  # BNPL pages
│   └── transporters/          # Courier portal
│
└── Static Assets (static/)
    ├── css/                   # Stylesheets
    ├── js/                    # JavaScript
    └── uploads/               # User uploads
        ├── products/          # Product images
        ├── ids/               # ID documents
        └── police_clearance/  # Driver clearances
```

## 🧹 What Was Cleaned Up

### Files Removed from Git Tracking
- ✅ `app.py.backup` - Removed from git (backup files excluded)
- ✅ Database backups (`*.db.bak_*`) - Added to .gitignore
- ✅ `__pycache__/` - Properly ignored

### Files Reorganized
- ✅ **25+ documentation files** moved to `docs/` folder
- ✅ **10 utility scripts** moved to `scripts/` folder
- ✅ Documentation organized by category (bnpl, deployment, guides)

### Enhanced .gitignore
Now properly excludes:
- Database files (*.db, *.db-journal, *.db.bak_*)
- Backup files (*.backup, *.bak, app.py.backup)
- Python cache (__pycache__/, *.pyc)
- Virtual environments (.venv/, venv/)
- IDE files (.vscode/, .idea/)
- Uploads (static/uploads/*)
- Logs (*.log)
- OS files (.DS_Store, Thumbs.db)

## 🔄 Git Repository Status

### Repository: babakairo/zimclassifieds
- **Branch:** main
- **Last Commit:** Project reorganization (Nov 16, 2025)
- **Commits:** 
  1. Initial BNPL implementation
  2. Complete Paynow integration
  3. Project reorganization (current)

### What's Tracked in Git
Only the `classifieds/` folder contents are tracked. The repository contains:
- ✅ Core application files (app.py, bnpl.py, etc.)
- ✅ Templates and static assets
- ✅ Configuration files (requirements.txt, config.json template)
- ✅ Documentation (docs/ folder)
- ✅ Utility scripts (scripts/ folder)
- ✅ README.md

### What's NOT Tracked
- ❌ Database files (zimclassifieds.db)
- ❌ Upload files (static/uploads/*)
- ❌ Environment files (.env)
- ❌ Backup files (*.backup)
- ❌ Python cache files
- ❌ Other projects (landlord-tenant-app, YouTube files)

## 🚀 Development Workflow

### Working on ZimClassifieds
```bash
# Always work from the classifieds directory
cd Z:\AWS\classifieds

# Activate virtual environment (using landlord-tenant-app's venv)
& 'Z:\AWS\landlord-tenant-app\.venv\Scripts\Activate.ps1'

# Run the app
python app.py

# Make changes, test, commit
git add .
git commit -m "Your changes"
git push origin main
```

### Other Projects Remain Separate
- **Landlord-Tenant App**: Has its own virtual environment and is not tracked in ZimClassifieds git
- **YouTube Tools**: Separate scripts in root AWS folder, not part of ZimClassifieds

## 📊 Project Statistics

### ZimClassifieds Repository
- **Total Files:** ~80 files
- **Python Files:** 10 core modules
- **Templates:** 40+ HTML files
- **Documentation:** 25 markdown files
- **Scripts:** 10 utility scripts
- **Lines of Code:** ~11,000+ lines (including docs)

### Key Modules
- `bnpl.py` - 1,050+ lines (BNPL system)
- `app.py` - 1,000+ lines (main application)
- `sellers.py` - 500+ lines (seller management)
- `transporters.py` - 400+ lines (courier system)

## 🎯 Next Steps

### For Clean Development
1. ✅ Project structure is now clean and organized
2. ✅ All unnecessary files excluded from git
3. ✅ Documentation properly categorized
4. ✅ Scripts separated from core code

### For Production
1. Create virtual environment specific to ZimClassifieds
2. Install dependencies from requirements.txt
3. Configure environment variables
4. Register for Paynow and Africa's Talking
5. Deploy to production server

## 📝 Notes

### Virtual Environment
Currently using `landlord-tenant-app/.venv` for convenience. Consider creating a dedicated virtual environment:

```bash
cd Z:\AWS\classifieds
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Database
Using SQLite for development (`zimclassifieds.db`). Production setup uses PostgreSQL (see `docs/deployment/POSTGRES_MIGRATION_GUIDE.md`).

### Configuration
- **Development:** Uses `config.json` with placeholder credentials
- **Production:** Override with environment variables or update config.json with real credentials

---

**Last Updated:** November 16, 2025  
**Organization Status:** ✅ Complete - Clean structure implemented
