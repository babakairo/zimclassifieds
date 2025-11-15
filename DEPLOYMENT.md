# ZimClassifieds — Quick Deployment Guide

## Deploying to Render (Recommended for Launch)

### What You Need
1. GitHub account (free)
2. Render account (free at render.com)
3. A domain (optional; Render gives you a free subdomain)
4. SendGrid account (free tier for SMTP; optional if you don't need email)
5. Google reCAPTCHA keys (free; optional but recommended for spam prevention)

### **Deployment Steps**

#### **1. Create a GitHub Repository**

```bash
# From your project directory
git init
git add .
git commit -m "Initial commit: ZimClassifieds launch"
git remote add origin https://github.com/YOUR-USERNAME/zimclassifieds.git
git branch -M main
git push -u origin main
```

#### **2. Create a Render Account & Connect to GitHub**

1. Go to [render.com](https://render.com)
2. Sign up (use GitHub OAuth for quickest setup)
3. Authorize Render to access your GitHub repos

#### **3. Deploy the App on Render**

1. Click **"New Web Service"** from Render dashboard
2. Select your GitHub repo (`zimclassifieds`)
3. Fill in:
   - **Name**: `zimclassifieds` (or any name)
   - **Environment**: `Python`
   - **Region**: Choose closest to Zimbabwe (e.g., `Frankfurt` or `Singapore` for Africa)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -w 4 -b 0.0.0.0:$PORT app:app`
4. Click **"Create Web Service"**

Render will now build and deploy your app. This takes ~2–3 minutes.

#### **4. Set Environment Variables on Render**

After deployment starts, go to **Settings** → **Environment** and add:

```
SECRET_KEY=<generate-a-random-long-string>
RECAPTCHA_SITE_KEY=<your-recaptcha-site-key>
RECAPTCHA_SECRET_KEY=<your-recaptcha-secret-key>
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=<your-sendgrid-api-key>
EMAIL_FROM=noreply@zimclassifieds.com
GA_MEASUREMENT_ID=<your-google-analytics-id>
```

**Important**: After adding env vars, restart the service (Render will redeploy automatically).

#### **5. Get Your Live URL**

Once deployed, Render gives you a free URL like:
```
https://zimclassifieds-xxxx.onrender.com
```

Visit it! The site is now live. 🎉

#### **6. (Optional) Point a Custom Domain**

If you bought a domain (e.g., zimclassifieds.com):

1. Go to Render Settings → **Custom Domain**
2. Enter your domain (e.g., `zimclassifieds.com`)
3. Update your domain registrar (Namecheap, GoDaddy, etc.) with the CNAME Render provides
4. Wait 5–10 min for DNS to propagate

---

### **Getting the Required Keys (Free)**

#### **Google reCAPTCHA**
1. Go to [google.com/recaptcha/admin](https://www.google.com/recaptcha/admin)
2. Click **+** to create a new site
3. Fill in:
   - **Label**: ZimClassifieds
   - **reCAPTCHA type**: v2 Checkbox
   - **Domains**: your domain (e.g., zimclassifieds.com or render domain)
4. Copy the Site Key and Secret Key → add to Render env

#### **SendGrid (SMTP for Email)**
1. Sign up free at [sendgrid.com](https://sendgrid.com)
2. Verify your sender email (or use a free SendGrid sandbox)
3. Go to **Settings** → **API Keys** → Create a new API key
4. Copy API key → set as `SMTP_PASSWORD` in Render

#### **Google Analytics** (optional)
1. Go to [analytics.google.com](https://analytics.google.com)
2. Create a new property for your site
3. Get your Measurement ID (looks like `G-XXXXXXXXXX`) → add to Render env

---

### **Testing After Deploy**

1. Visit your live URL
2. Test signup (verify email shows in Render logs or your SMTP service)
3. Create a listing (should be pending if email not verified)
4. Login as admin and approve the listing
5. Check mobile responsiveness (visit on phone)

---

### **Troubleshooting**

- **App won't deploy**: Check Render build logs; usually a missing dependency. Run `pip install -r requirements.txt` locally to test.
- **Email not sending**: Make sure SendGrid API key is correct and your sender email is verified.
- **reCAPTCHA not showing**: Check browser console for JS errors; verify site key is correct.
- **Listings not saved**: Check that `zimclassifieds.db` is in the project directory and writable.

---

### **Next Steps After Launch**

1. **Monitor**: Add uptime monitoring (UptimeRobot; free tier)
2. **Backups**: Set up daily DB backups (Render supports "disks" for persistent storage)
3. **Marketing**: Share on social media, Zimbabwe forums, classifieds groups
4. **Iterate**: Gather user feedback and add paid features after reaching ~100 active users

---

### **Alternative Deployment Platforms**

If Render doesn't work for you, here are quick alternatives:

**Railway** (also very easy):
- Go to [railway.app](https://railway.app)
- Connect GitHub → select repo
- Set env vars → deploy
- ~5 minutes

**Fly.io** (fast & global):
- Install `flyctl` CLI
- Run `fly launch` in project dir
- Set env vars
- Deploy with `fly deploy`

**DigitalOcean App Platform**:
- Similar to Render; ~$12/mo minimum
- More control over resources

---

**Questions? Ask in the chat and I'll help troubleshoot!**
