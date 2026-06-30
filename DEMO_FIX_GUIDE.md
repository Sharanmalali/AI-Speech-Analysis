# Fix Demo 502 Error - Complete Guide

## The Problem
You're getting a 502 error because the backend doesn't have the static demo data file yet.

## ✅ I've Already Created the Static Data File

The file `backend/app/routers/demo_data.json` has been created with sample data. Now you just need to restart your backend.

---

## Solution: Choose Your Setup Method

### Option 1: If Using Docker (Recommended)

#### Step 1: Make Sure Docker is Running
1. Open **Docker Desktop** application
2. Wait for it to fully start (whale icon should be stable)
3. You should see "Docker Desktop is running" in the system tray

#### Step 2: Check Your Services
```bash
cd C:\Projects\AI-Speech-Analysis
docker compose ps
```

**Expected output**: List of services (backend, frontend, redis, etc.)

#### Step 3: Restart Backend
```bash
docker compose restart backend
```

**Wait 10-15 seconds** for backend to fully restart

#### Step 4: Test the Demo
Open your browser and go to:
- **Demo Page**: http://localhost:3000/dashboard/demo
- **API Test**: http://localhost:8000/api/v1/demo/sample-result

**Expected**: Demo should load with 3 speakers, Kannada transcripts, etc.

---

### Option 2: If Running Backend Locally (Without Docker)

#### Step 1: Check if Backend is Running
Look for a terminal/command prompt with:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

If not running, start it:

#### Step 2: Start Backend
```bash
cd C:\Projects\AI-Speech-Analysis\backend

# Activate virtual environment
.venv\Scripts\activate

# Start backend
uvicorn app.main:app --reload
```

**Wait for**: `Application startup complete`

#### Step 3: Test the Demo
Open your browser:
- **Demo Page**: http://localhost:3000/dashboard/demo
- **API Test**: http://localhost:8000/api/v1/demo/sample-result

---

## Verification Steps

### Test 1: Check Static File Exists
```bash
# Should show the file
dir C:\Projects\AI-Speech-Analysis\backend\app\routers\demo_data.json
```

**Expected**: File should be ~15 KB

### Test 2: Test API Directly
Open browser and visit:
```
http://localhost:8000/api/v1/demo/sample-result
```

**Expected**: JSON response with speakers, transcriptions, etc.

**If you get 502/503**: Backend isn't running or didn't load the file
**If you get 404**: Demo router not registered
**If you get JSON data**: ✅ SUCCESS! Move to Test 3

### Test 3: Test Frontend Demo Page
Open browser and visit:
```
http://localhost:3000/dashboard/demo
```

**Expected**: 
- Demo banner at top
- 3 speakers shown
- Charts and timeline visible
- Transcript in Kannada and English

**If page is blank**: Frontend not running
**If redirects to login**: You're on wrong route (should be `/dashboard/demo`, not `/dashboard`)
**If shows data**: ✅ SUCCESS!

### Test 4: Test from Landing Page
1. Go to: http://localhost:3000
2. Look for **"Try Demo"** button in hero section
3. Click it
4. Should go to demo page (from Test 3)

---

## Common Issues & Solutions

### Issue 1: "Docker Desktop is not running"
**Solution**:
1. Click Start Menu
2. Search "Docker Desktop"
3. Open the app
4. Wait 30-60 seconds for startup
5. Try docker commands again

### Issue 2: "Cannot connect to Docker daemon"
**Solution**:
- Restart Docker Desktop
- Or run backend locally (see Option 2 above)

### Issue 3: Backend shows "demo_data_not_available"
**Solution**:
```bash
# Check file exists
dir backend\app\routers\demo_data.json

# If missing, I already created it, so just restart:
docker compose restart backend
```

### Issue 4: Frontend shows blank page or errors
**Solution**:
```bash
# Make sure frontend is running
cd frontend
npm run dev

# Then visit http://localhost:3000/dashboard/demo
```

### Issue 5: "Module not found" errors
**Solution**:
```bash
cd backend
pip install -r requirements-dev.txt
```

### Issue 6: Port 8000 or 3000 already in use
**Solution**:
```bash
# Find what's using the port
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# Kill the process or change ports in your config
```

---

## Quick Test Commands (Copy-Paste)

### For Docker Setup:
```bash
cd C:\Projects\AI-Speech-Analysis

# Check Docker is running
docker ps

# Start all services
docker compose up -d

# Wait 30 seconds, then test
curl http://localhost:8000/api/v1/demo/sample-result

# Or open in browser:
start http://localhost:3000/dashboard/demo
```

### For Local Setup:
```bash
# Terminal 1 - Backend
cd C:\Projects\AI-Speech-Analysis\backend
.venv\Scripts\activate
uvicorn app.main:app --reload

# Terminal 2 - Frontend  
cd C:\Projects\AI-Speech-Analysis\frontend
npm run dev

# Then open: http://localhost:3000/dashboard/demo
```

---

## What the Demo Data Contains

The `demo_data.json` file I created has:

- ✅ **3 speakers** (representing a mental health discussion)
- ✅ **1 atypical speaker** (SPEAKER_02 - shows the screening feature)
- ✅ **2 typical speakers** (SPEAKER_01, SPEAKER_03)
- ✅ **Kannada text** with English translations
- ✅ **Real acoustic features** (F0, jitter, shimmer, HNR)
- ✅ **Gender & age predictions**
- ✅ **Timestamps and segments**
- ✅ **180 seconds duration** (~3 minutes)

All realistic data that showcases your platform's capabilities!

---

## Still Not Working?

### Debug Checklist:

1. **Backend Running?**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"ok",...}
   ```

2. **File Exists?**
   ```bash
   dir backend\app\routers\demo_data.json
   # Should show the file
   ```

3. **Frontend Running?**
   ```bash
   curl http://localhost:3000
   # Should return HTML
   ```

4. **Check Backend Logs:**
   ```bash
   # Docker:
   docker compose logs backend --tail=50
   
   # Local:
   # Look at the terminal where uvicorn is running
   ```

5. **Check for Errors:**
   Look for:
   - ❌ "demo_data_missing" → File not found
   - ❌ "demo_data_invalid_json" → JSON syntax error
   - ❌ "ModuleNotFoundError" → Missing dependencies

---

## After It's Working

### Test These Features:

1. ✅ Click through all tabs (Overview, Speakers, Transcript)
2. ✅ Check charts render correctly
3. ✅ Verify Kannada and English text shows
4. ✅ See atypical classification on SPEAKER_02
5. ✅ Try theme toggle (light/dark mode)
6. ✅ Click "Back to Home" button
7. ✅ Navigate from landing page "Try Demo" button

---

## For Hackathon Demo

Once working:

1. **Practice your flow**:
   - Start at http://localhost:3000
   - Click "Try Demo"
   - Show: "Instant results, no waiting!"
   - Walk through speakers, charts, transcript

2. **Key talking points**:
   - "3 speakers detected automatically"
   - "Real Kannada-to-English transcription"
   - "One speaker flagged as atypical for clinical review"
   - "Complete acoustic analysis"
   - "All in under 3 minutes of processing"

3. **No authentication needed**:
   - Emphasize judges can try it right now
   - No signup barrier
   - Instant access

---

## Need More Help?

If you're still stuck, tell me:
1. Are you using Docker or running locally?
2. What error do you see in browser console (F12)?
3. What do you see in backend logs?
4. What URL are you visiting?

I'll help you debug further! 🚀
