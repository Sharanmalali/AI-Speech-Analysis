# Demo Mode Quick Start Guide

## 🎯 Goal
Get the demo working with **real data from Sample1C.wav** in under 10 minutes.

## ⚡ Quick Setup (4 Steps)

### Step 1: Start Your Services (2 min)
```bash
# Start everything
docker compose up

# Or if already running, just ensure all services are healthy
docker compose ps
```

**Verify**: All services should be "healthy" or "running"

### Step 2: Create Demo User (1 min)
```bash
# Create user for generator script
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@ablepro.com","password":"demo123456","full_name":"Demo User"}'
```

**Expected**: `{"user": {...}, "tokens": {...}}`

### Step 3: Generate Demo Data (3-5 min)
```bash
cd backend

# Edit credentials first (if needed)
# Open generate_demo_data.py and verify lines 20-21:
#   EMAIL = "demo@ablepro.com"
#   PASSWORD = "demo123456"

# Run generator
python generate_demo_data.py
```

**Expected Output**:
```
🎬 Starting demo data generation...
🔐 Step 1: Authenticating...
✅ Authenticated as: demo@ablepro.com
📤 Step 2: Uploading Sample1C.wav...
✅ Upload successful! Job ID: abc123...
⏳ Step 3: Waiting for processing to complete...
   📊 Stage: diarization (15%)
   📊 Stage: transcription (40%)
   ...
✅ Processing complete! (127s)
💾 Step 5: Saving demo data to demo_data.json...
✅ Demo data saved! (45.2 KB)
🎉 Demo data generation complete!
```

### Step 4: Restart & Test (1 min)
```bash
# Restart backend to load new data
docker compose restart backend

# Test the demo endpoint
curl http://localhost:8000/api/v1/demo/sample-result

# Test the frontend
# Open: http://localhost:3000/dashboard/demo
```

**Expected**: Demo page loads instantly with real analysis data!

## ✅ Verification

Visit these URLs:

1. **Backend API**: http://localhost:8000/api/v1/demo/sample-result
   - Should return JSON with speakers, transcriptions, predictions

2. **Frontend Demo**: http://localhost:3000/dashboard/demo
   - Should show complete analysis dashboard
   - No login required
   - Data from Sample1C.wav

3. **Landing Page**: http://localhost:3000
   - Should have "Try Demo" buttons
   - Click to go to demo page

## 🚨 Common Issues

### Issue: "Authentication failed"
```bash
# Solution: User doesn't exist yet
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@ablepro.com","password":"demo123456"}'
```

### Issue: "Audio file not found"
```bash
# Solution: Verify Sample1C.wav exists
ls Sample1C.wav  # Should be in project root
```

### Issue: "Timeout: Processing took longer than 600s"
```bash
# Solution: Check Celery worker is running
docker compose logs celery

# Restart if needed
docker compose restart celery
```

### Issue: "Demo data not available" when accessing demo endpoint
```bash
# Solution: Run the generator first
cd backend
python generate_demo_data.py
docker compose restart backend
```

### Issue: Generator script fails with "module not found"
```bash
# Solution: Install httpx
pip install httpx
```

## 📋 Files Changed/Created

### Created
- ✅ `backend/app/routers/demo.py` - Demo API endpoint
- ✅ `backend/generate_demo_data.py` - Data generator script
- ✅ `frontend/src/app/dashboard/demo/page.tsx` - Demo page
- ✅ `frontend/src/app/dashboard/demo/layout.tsx` - Demo layout

### Generated (after running script)
- ✅ `backend/app/routers/demo_data.json` - Real analysis data

### Modified
- ✅ `backend/app/main.py` - Added demo router
- ✅ `frontend/src/lib/services.ts` - Added demoService
- ✅ `frontend/src/app/page.tsx` - Added "Try Demo" buttons

## 🎬 For Hackathon Presentation

**Before Demo Day**:
1. ✅ Generate demo data from Sample1C.wav (done once)
2. ✅ Test that `/dashboard/demo` loads instantly
3. ✅ Verify all features display correctly
4. ✅ Ensure no authentication required

**During Presentation**:
1. Start on landing page
2. Say: "Let me show you our analysis instantly..."
3. Click "Try Demo" button
4. → **Boom! Instant results** (no waiting)
5. Show speakers, charts, timeline, transcript
6. Explain: "This is real data from our ML pipeline"

**Timing**: < 30 seconds to see complete product

## 🔗 Additional Resources

- **Detailed Setup**: `GENERATE_DEMO_DATA_GUIDE.md`
- **Implementation Details**: `DEMO_MODE_IMPLEMENTATION.md`
- **Full Testing Guide**: `DEMO_TESTING_GUIDE.md`

## 💡 Pro Tips

1. **Test Before Demo**: Run generator the day before presentation
2. **Verify Content**: Check demo shows good representative data
3. **Backup Plan**: Have live upload ready if demo link fails
4. **Practice Flow**: Know which tabs to click through
5. **Highlight Features**: Point out atypical detection, translations, etc.

## ✨ What Judges See

- ✅ **No Login** - Click and see results immediately
- ✅ **Real Data** - Actual ML pipeline output (not fake)
- ✅ **All Features** - Diarization, transcription, classification, charts
- ✅ **Fast** - Loads in < 1 second
- ✅ **Professional** - Production-quality dashboard

**Perfect for impressing hackathon judges in limited time!** 🚀

---

**Need Help?** See detailed troubleshooting in `GENERATE_DEMO_DATA_GUIDE.md`
