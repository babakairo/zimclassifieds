#!/usr/bin/env python3
"""
ZimClassifieds Launch Checklist & Helper

Run this script to verify your deployment is ready.
Usage: python3 launch_checklist.py
"""

import os
import sys
from pathlib import Path

def check_file(path, name):
    if os.path.exists(path):
        print(f"✅ {name}")
        return True
    else:
        print(f"❌ {name} — MISSING")
        return False

def check_env(key, name, required=False):
    val = os.environ.get(key)
    if val:
        print(f"✅ {name} — set")
        return True
    else:
        status = "MISSING (required)" if required else "not set (optional)"
        symbol = "❌" if required else "⚠️"
        print(f"{symbol} {name} — {status}")
        return not required

def main():
    print("\n🚀 ZimClassifieds Launch Checklist\n")
    
    checks = []
    
    # File checks
    print("📁 Project Files:")
    checks.append(check_file('app.py', 'app.py'))
    checks.append(check_file('requirements.txt', 'requirements.txt'))
    checks.append(check_file('Procfile', 'Procfile'))
    checks.append(check_file('zimclassifieds.db', 'Database (zimclassifieds.db)'))
    checks.append(check_file('static/uploads', 'Upload folder'))
    checks.append(check_file('templates', 'Templates folder'))
    
    print("\n🔐 Security:")
    checks.append(check_env('SECRET_KEY', 'SECRET_KEY', required=True))
    
    print("\n📧 Email (for verification — optional but recommended):")
    smtp_configured = all([
        os.environ.get('SMTP_SERVER'),
        os.environ.get('SMTP_PORT'),
        os.environ.get('SMTP_USER'),
        os.environ.get('SMTP_PASSWORD'),
    ])
    if smtp_configured:
        print("✅ SMTP configured")
        checks.append(True)
    else:
        print("⚠️ SMTP not configured (emails will print to console in dev)")
        checks.append(True)
    
    print("\n🛡️ reCAPTCHA (optional but recommended):")
    recaptcha_configured = all([
        os.environ.get('RECAPTCHA_SITE_KEY'),
        os.environ.get('RECAPTCHA_SECRET_KEY'),
    ])
    if recaptcha_configured:
        print("✅ reCAPTCHA configured")
        checks.append(True)
    else:
        print("⚠️ reCAPTCHA not configured (will skip spam protection)")
        checks.append(True)
    
    print("\n📊 Analytics (optional):")
    checks.append(check_env('GA_MEASUREMENT_ID', 'Google Analytics'))
    
    print("\n" + "="*50)
    if all(checks):
        print("✅ All checks passed! Ready to deploy.\n")
        print("Next steps:")
        print("1. Push to GitHub: git push origin main")
        print("2. Deploy to Render: https://render.com/new/web-service")
        print("3. Set env vars in Render dashboard")
        print("4. Visit your live URL!")
        return 0
    else:
        print(f"⚠️ Some checks failed. Review above.\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
