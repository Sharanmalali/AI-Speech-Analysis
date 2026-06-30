# How to Generate Real Demo Data from Sample1C.wav

This guide will help you process the `Sample1C.wav` audio file through your complete ML pipeline and save the results as static demo data.

## Overview

Instead of hardcoded fake data, the demo will now show **real analysis results** from `Sample1C.wav`. The process:

1. ✅ Upload `Sample1C.wav` to your API
2. ✅ Wait for complete processing (diarization → transcription → classification)
3. ✅ Fetch the complete results
4. ✅ Save to `backend/app/routers/demo_data.json`
5. ✅ Demo endpoint loads this static JSON (no ML models run per request)

## Prerequisites

Before running the demo data generator:

### 1. Backend Must Be Running
```bash
# Option A: Docker
docker compose up

# Option B: Local development
cd backend
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uvicorn app.main:app --reload
```

### 2. You Need Valid User Credentials

Create a test user first (if you don't have one):

```bash
# Option A: Via API (use /docs at http://localhost:8000/docs)
# Go to POST /auth/register and register a user

# Option B: Via Python script
python -c "
import requests
response = requests.post(
    'http://localhost:8000/api/v1/auth/register',
    json={
        'email': 'demo@ablepro.com',
        'password': 'demo123456',
        'full_name': 'Demo User'
    }
)
print(response.json())
"
```

### 3. Required Services Running

- ✅ Backend API (FastAPI)
- ✅ Redis (for Celery broker)
- ✅ Celery worker (for ML pipeline processing)
- ✅ Database (PostgreSQL or SQLite)

**Quick check**:
```bash
# Check health endpoint
curl http://localhost:8000/health
# Should return: {"status": "ok", ...}
```

## Step-by-Step: Generate Demo Data

### Step 1: Update Credentials in Generator Script

Open `backend/generate_demo_data.py` and update the credentials:

```python
# Line 20-21
EMAIL = "demo@ablepro.com"      # Your test user email
PASSWORD = "demo123456"          # Your test user password
```

### Step 2: Run the Generator Script

```bash
cd backend

# Activate virtual environment if needed
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install httpx if not already installed
pip install httpx

# Run the generator
python generate_demo_data.py
```

### Step 3: Monitor the Process

You'll see output like:

```
╔═══════════════════════════════════════════════════════════╗
║          AblePro Demo Data Generator                      ║
║  Processes Sample1C.wav and creates static demo data     ║
╚═══════════════════════════════════════════════════════════╝

🎬 Starting demo data generation...
📁 Audio file: c:\Projects\AI-Speech-Analysis\Sample1C.wav
💾 Output will be saved to: backend\app\routers\demo_data.json

🔐 Step 1: Authenticating...
✅ Authenticated as: demo@ablepro.com

📤 Step 2: Uploading Sample1C.wav...
✅ Upload successful! Job ID: abc123...

⏳ Step 3: Waiting for processing to complete...
   This may take several minutes depending on audio length...
   📊 Stage: diarization (15%)
   📊 Stage: transcription (40%)
   📊 Stage: feature_extraction (65%)
   📊 Stage: atypicality_classification (85%)
   📊 Stage: report_generation (95%)
✅ Processing complete! (127s)

📥 Step 4: Fetching complete analysis results...
✅ Results fetched successfully!
   📊 Detected speakers: 3
   ⏱️  Processing time: 127.4s

💾 Step 5: Saving demo data to demo_data.json...
✅ Demo data saved! (45.2 KB)

============================================================
🎉 Demo data generation complete!
============================================================

📋 Summary:
   Audio file: Sample1C.wav
   Job ID: abc123-def456-...
   Speakers: 3
   Duration: 180.5s
   Atypical speakers: 1

✅ The demo endpoint will now serve real analysis data from Sample1C.wav!

🔄 Next step: Restart your backend server to load the new demo data.
```

### Step 4: Verify the Generated File

Check that the file was created:

```bash
# Should exist
ls backend/app/routers/demo_data.json

# Quick preview (first 50 lines)
head -n 50 backend/app/routers/demo_data.json
```

### Step 5: Restart Backend to Load New Data

```bash
# If using Docker
docker compose restart backend

# If running locally
# Stop the uvicorn process (Ctrl+C) and restart:
uvicorn app.main:app --reload
```

### Step 6: Test the Demo Endpoint

```bash
# Should return real data from Sample1C.wav
curl http://localhost:8000/api/v1/demo/sample-result | python -m json.tool
```

## What the Generator Does

1. **Authenticates** with your API using provided credentials
2. **Uploads** `Sample1C.wav` (located in project root)
3. **Polls** job status every 2 seconds until completion
4. **Fetches** the complete analysis results (speakers, transcriptions, predictions)
5. **Saves** everything to `demo_data.json` with pretty formatting
6. **Caches** the data in memory on backend startup (fast response times)

## Troubleshooting

### Error: "Audio file not found"
```
❌ Error: Audio file not found at c:\Projects\AI-Speech-Analysis\Sample1C.wav
```

**Solution**: Verify the file exists:
```bash
ls Sample1C.wav  # Should be in project root
```

### Error: "Authentication failed: 401"
```
❌ Authentication failed: 401
   Response: {"error": {"code": "invalid_credentials", ...}}
```

**Solutions**:
- Verify the email/password in `generate_demo_data.py`
- Create the user first (see Prerequisites)
- Check the user is active and verified

### Error: "Upload failed: 413"
```
❌ Upload failed: 413
   Response: Payload too large
```

**Solution**: The audio file is too large. Check `MAX_UPLOAD_SIZE_MB` in backend settings:
```bash
# In backend/.env
MAX_UPLOAD_SIZE_MB=200  # Increase if needed
```

### Error: "Timeout: Processing took longer than 600s"
```
❌ Timeout: Processing took longer than 600s
```

**Solutions**:
- Check if Celery worker is running: `celery -A app.tasks.celery_app worker --loglevel=info`
- Check worker logs for errors
- Increase timeout in script (line 15): `max_wait = 1200  # 20 minutes`
- Verify ML models are loaded correctly

### Error: "Demo data file not found" when accessing /demo/sample-result
```
503 Service Unavailable
"demo_data_not_available"
```

**Solution**: The `demo_data.json` file hasn't been generated yet. Run the generator script first.

### Processing Fails During ML Pipeline
```
❌ Processing failed: Model loading error
```

**Solutions**:
- Check Celery worker logs: `docker compose logs celery` (if using Docker)
- Verify ML models exist in `models/` directory
- Check HuggingFace token is set (for pyannote): `HUGGINGFACE_TOKEN` in `.env`
- Ensure sufficient system resources (RAM, GPU if applicable)

## Advanced: Regenerating Demo Data

If you want to update the demo with new data:

1. **Delete old data**:
   ```bash
   rm backend/app/routers/demo_data.json
   ```

2. **Process different audio** (optional):
   - Update `AUDIO_FILE_PATH` in `generate_demo_data.py` to point to different file
   - Or replace `Sample1C.wav` with new audio file (keep same name)

3. **Run generator again**:
   ```bash
   python backend/generate_demo_data.py
   ```

4. **Restart backend** to load new data

## File Structure After Generation

```
backend/
├── app/
│   └── routers/
│       ├── demo.py              # Demo endpoint (loads from JSON)
│       └── demo_data.json       # ✅ Generated real data
├── generate_demo_data.py        # Generator script
└── ...

Sample1C.wav                      # Source audio file
```

## Benefits of This Approach

✅ **Real Data**: Shows actual analysis from your ML pipeline  
✅ **No ML Processing**: Demo loads instantly (pre-computed results)  
✅ **No Authentication**: Publicly accessible for judges  
✅ **Static & Fast**: JSON file cached in memory  
✅ **Easy Updates**: Regenerate anytime with new audio  
✅ **Reliable**: Never fails due to ML model issues during demo  

## Next Steps

After generating demo data:

1. ✅ Test the demo endpoint: `curl http://localhost:8000/api/v1/demo/sample-result`
2. ✅ Test the frontend demo page: `http://localhost:3000/dashboard/demo`
3. ✅ Verify all speakers, transcriptions, and predictions are correct
4. ✅ Check that the data reflects Sample1C.wav content accurately

## For Hackathon Demo

**Before the presentation**:
1. Generate demo data from Sample1C.wav
2. Verify it loads in < 1 second
3. Ensure frontend displays correctly
4. Have backup plan (live upload) ready

**During presentation**:
- Say: "Let me show you our complete analysis instantly..."
- Click "Try Demo" button
- Data loads immediately (no wait!)
- Walk through all features using real results

**Perfect for time-limited hackathon demos!** 🚀
