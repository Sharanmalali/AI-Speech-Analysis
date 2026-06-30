# Start Demo in 3 Steps ⚡

## ✅ Good News: The Static Data File is Already Created!

I've created `backend/app/routers/demo_data.json` with sample data. You just need to restart your backend.

---

## 🚀 Quick Start (Choose One)

### If Using Docker:

```bash
# 1. Open Docker Desktop (make sure it's running)

# 2. Open Command Prompt and run:
cd C:\Projects\AI-Speech-Analysis
docker compose up -d

# 3. Wait 30 seconds, then open browser:
http://localhost:3000/dashboard/demo
```

### If Running Locally (No Docker):

```bash
# Terminal 1 - Start Backend
cd C:\Projects\AI-Speech-Analysis\backend
.venv\Scripts\activate
uvicorn app.main:app --reload

# Terminal 2 - Start Frontend
cd C:\Projects\AI-Speech-Analysis\frontend
npm run dev

# 3. Open browser:
http://localhost:3000/dashboard/demo
```

---

## 🎯 What You Should See

When you visit `http://localhost:3000/dashboard/demo`:

1. ✅ **Demo Mode Banner** (purple/blue gradient at top)
2. ✅ **4 KPI Cards**: 3 speakers, ~180s duration, 1 atypical, processing time
3. ✅ **Three Tabs**: Overview, Speakers, Transcript
4. ✅ **Overview Tab**: 2 charts (speaking time, speech/pause) + timeline
5. ✅ **Speakers Tab**: 3 speaker cards with predictions
6. ✅ **Transcript Tab**: Kannada text + English translations

**No login required!** That's the point - judges can access instantly.

---

## ❌ If You Get Errors

### "502 Bad Gateway"
**Reason**: Backend not running or not restarted after I created the file

**Fix**:
```bash
# For Docker:
docker compose restart backend

# For Local:
# Stop backend (Ctrl+C) and restart:
uvicorn app.main:app --reload
```

### "Cannot connect to Docker"
**Reason**: Docker Desktop not running

**Fix**: 
1. Open Docker Desktop application
2. Wait for it to fully start
3. Try again

### "Page Not Found" or Redirects to Login
**Reason**: Wrong URL

**Fix**: Make sure you're visiting:
- ✅ `http://localhost:3000/dashboard/demo` (correct - no auth)
- ❌ `http://localhost:3000/dashboard` (wrong - requires auth)

### Blank Page
**Reason**: Frontend not running

**Fix**:
```bash
cd C:\Projects\AI-Speech-Analysis\frontend
npm run dev
```

---

## 🧪 Test It's Working

### Test 1: Backend API
Visit in browser: `http://localhost:8000/api/v1/demo/sample-result`

**Should see**: JSON data with speakers, transcriptions, etc.

### Test 2: Frontend Demo
Visit in browser: `http://localhost:3000/dashboard/demo`

**Should see**: Full demo page with charts and data

### Test 3: Landing Page Button
1. Visit: `http://localhost:3000`
2. Find "Try Demo" button (between "Start analysing" and "Sign in")
3. Click it
4. Should navigate to demo page

---

## 📝 No Test User Needed!

**Important**: You DON'T need to create any test users for the demo to work!

The demo endpoint is **public** - no authentication required. The static data file I created (`demo_data.json`) is loaded directly by the backend.

**Only needed if you want to generate NEW demo data from Sample1C.wav** (but the current static data works fine for hackathon!)

---

## 🎬 For Your Hackathon Demo

**What to say**:
> "Let me show you our platform instantly - click here..."
> 
> *[Click "Try Demo" button]*
> 
> "Here you see a complete analysis of a 3-minute conversation. We detected 3 speakers, transcribed from Kannada to English, and our AI flagged one speaker with atypical speech patterns for clinical review. All features visible immediately - no upload, no waiting."

**Time**: < 30 seconds to impress judges! ⚡

---

## Still Having Issues?

Tell me:
1. **What you're running**: Docker or Local?
2. **What URL you visited**: (copy-paste it)
3. **What error you see**: (screenshot or error message)
4. **Backend logs**: 
   - Docker: `docker compose logs backend --tail=20`
   - Local: Copy last 10 lines from terminal

I'll help you fix it! 🚀
