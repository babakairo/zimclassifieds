# Quick Start — Get Your Site Live in 5 Minutes

You're ready to launch! Choose one platform below and follow the steps.

## **Option 1: Render (Easiest — Recommended)**

**Time: ~10 minutes**

1. Go to https://render.com and sign up (use GitHub OAuth)
2. Click **New Web Service** → Connect your GitHub repo
3. Render auto-reads your `Procfile` and `requirements.txt`
4. Set env vars (SECRET_KEY, RECAPTCHA, SMTP, GA)
5. Click Deploy
6. Your site is live at `https://zimclassifieds-xxxx.onrender.com` ✅

**Next:** Add a custom domain (zimclassifieds.com) from Render settings.

---

## **Option 2: Railway (Also Very Easy)**

**Time: ~8 minutes**

1. Go to https://railway.app and sign up
2. Click **+ New Project** → Import from GitHub
3. Select your repo
4. Railway auto-detects Flask
5. Go to **Variables** and add env vars (same as Render)
6. Deploy
7. Your site is live ✅

**Cost:** Free tier; pay as you grow (~$5/mo for small usage)

---

## **Option 3: Fly.io (Global & Fast)**

**Time: ~12 minutes**

1. Install `flyctl`: https://fly.io/docs/hands-on/install-flyctl/
2. Go to https://fly.io and sign up
3. In your project folder, run:
   ```bash
   flyctl auth login
   flyctl launch
   flyctl secrets set SECRET_KEY=your-key SMTP_SERVER=... (and other vars)
   flyctl deploy
   ```
4. Your site is live at `https://zimclassifieds-xxxx.fly.dev` ✅

**Cost:** Free tier + ~$3/mo if you need more resources

---

## **Option 4: DigitalOcean App Platform (Most Control)**

**Time: ~15 minutes**

1. Go to https://www.digitalocean.com/products/app-platform
2. Click **Create App**
3. Connect GitHub repo
4. DigitalOcean auto-reads Procfile
5. Add env vars
6. Deploy
7. Your site is live ✅

**Cost:** $12+/mo minimum

---

## **What You Need Before Deploying**

✅ GitHub repo with your code (I can help push if needed)
✅ SECRET_KEY set (generate one: https://randomkeygen.com)
✅ Optional: reCAPTCHA keys (free; https://www.google.com/recaptcha/admin)
✅ Optional: SendGrid API key for emails (free tier; https://sendgrid.com)
✅ Optional: Google Analytics ID (free; https://analytics.google.com)

---

## **Environment Variables to Set on Your Platform**

```
SECRET_KEY=<random-long-string>
RECAPTCHA_SITE_KEY=<your-key>
RECAPTCHA_SECRET_KEY=<your-key>
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=<your-sendgrid-key>
EMAIL_FROM=noreply@zimclassifieds.com
GA_MEASUREMENT_ID=G-XXXXX
```

---

## **After You Deploy**

1. **Test the site:** Visit your live URL
2. **Test signup:** Create an account → verify email works
3. **Test listing:** Post a listing → check it's pending → approve in admin
4. **Test admin:** Login as admin at `/admin/login`
5. **Check logs:** If something fails, check the platform logs (Render / Railway / Fly shows them)

---

## **Marketing: Day 1 After Launch**

- Post on Zimbabwe forums (TechZim, ZimForum, etc.)
- Share in WhatsApp / Telegram groups
- Tweet about your launch
- Ask friends to post test listings
- Encourage early adopters to invite friends (viral growth)

---

## **Which Platform Should I Pick?**

- 🚀 **Easiest?** Render or Railway
- 💸 **Cheapest?** Render (free tier is generous) or Fly.io
- 🌍 **Fastest globally?** Fly.io
- 🎛️ **Most control?** DigitalOcean or self-hosted

---

**Ready to launch?** Pick one and tell me! I'll help you set it up. 🎉
