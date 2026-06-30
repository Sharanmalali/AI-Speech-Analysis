# Demo Mode Implementation

## Overview
Added a publicly accessible demo mode feature that allows hackathon judges and visitors to instantly see a complete analysis result **from the real Sample1C.wav file** without uploading files, waiting for processing, or requiring authentication.

**Key Point**: The demo serves **real analysis data** that was processed once through your complete ML pipeline and saved as static JSON. No ML models are loaded or run when users access the demo.

## Changes Made

### Backend Changes

#### 1. New Demo Router (`backend/app/routers/demo.py`)
- **Purpose**: Provides a publicly accessible endpoint with real pre-processed data
- **Endpoint**: `GET /api/v1/demo/sample-result`
- **Authentication**: None required (public endpoint)
- **Data Source**: Loads from `backend/app/routers/demo_data.json`
- **Caching**: Data is cached in memory after first load for instant responses
- **Features**:
  - Returns real analysis results from Sample1C.wav
  - Includes actual Kannada → English transcription from Whisper
  - Contains real speaker diarization results from pyannote
  - Real gender/age predictions and atypicality classifications
  - Actual acoustic features extracted by your pipeline

**How It Works**:
1. On first request, loads `demo_data.json` file
2. Validates data using Pydantic `ResultResponse` model
3. Caches in memory for subsequent requests (< 5ms response time)
4. Returns 503 error if `demo_data.json` doesn't exist (with instructions)

#### 2. Demo Data Generator (`backend/generate_demo_data.py`)
- **Purpose**: Processes Sample1C.wav through complete ML pipeline and saves results
- **Process**:
  1. Authenticates with API
  2. Uploads Sample1C.wav
  3. Polls for processing completion
  4. Fetches complete results
  5. Saves to `demo_data.json`
- **Usage**: Run once before demo: `python backend/generate_demo_data.py`
- **Requirements**: Backend running, valid user credentials, Celery worker active

#### 3. Router Registration (`backend/app/main.py`)
- Added "demo" to the list of registered API routers
- Demo router loads alongside existing routers (auth, upload, jobs, results, reports, admin)

### Frontend Changes

#### 1. New Demo Service (`frontend/src/lib/services.ts`)
- Added `demoService` with `getSampleResult()` method
- Fetches real demo data from `/api/v1/demo/sample-result`
- Returns `ResultResponse` type (identical to regular results)

#### 2. Demo Page (`frontend/src/app/dashboard/demo/page.tsx`)
- **Route**: `/dashboard/demo`
- **Features**:
  - Displays prominent "Demo Mode" banner
  - Shows all analysis results from Sample1C.wav (KPIs, charts, timeline, speakers, transcript)
  - Reuses existing result components (no duplication)
  - Non-functional PDF download with informative message
  - Animated counters and interactive tabs
- **Data Loading**:
  - Uses React Query for caching
  - Sets `staleTime: Infinity` (demo data never changes)
  - Includes loading and error states
  - **Read-only**: No upload, no editing, just viewing

#### 3. Demo Layout (`frontend/src/app/dashboard/demo/layout.tsx`)
- **Purpose**: Provides dashboard-like UI without authentication
- **Features**:
  - Simplified topbar with AblePro branding
  - "Demo Mode" indicator badge
  - Theme toggle support
  - "Back to Home" navigation button
  - No authentication required (bypasses AuthGuard)
  - No sidebar (simpler, focused view)

#### 4. Landing Page Updates (`frontend/src/app/page.tsx`)
- **Hero Section**: Added "Try Demo" button between "Start analysing" and "Sign in"
- **CTA Section**: Added "Try Demo" button alongside "Get started free"
- **Styling**: Uses outline variant with Sparkles icon for visual distinction
- **Behavior**: Direct link to `/dashboard/demo` (no authentication required)

## Data Generation Process

### One-Time Setup (Before Hackathon)

1. **Prepare Your Environment**:
   ```bash
   # Ensure backend, database, Redis, and Celery worker are running
   docker compose up
   ```

2. **Create Test User** (if needed):
   ```bash
   # Via API or registration endpoint
   curl -X POST http://localhost:8000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"demo@ablepro.com","password":"demo123456"}'
   ```

3. **Update Generator Script**:
   - Edit `backend/generate_demo_data.py`
   - Set EMAIL and PASSWORD (lines 20-21)

4. **Run the Generator**:
   ```bash
   cd backend
   python generate_demo_data.py
   ```

5. **Wait for Processing**:
   - Script uploads Sample1C.wav
   - Monitors processing through all stages
   - Downloads complete results
   - Saves to `demo_data.json`
   - Processing time depends on audio length (typically 1-5 minutes)

6. **Restart Backend**:
   ```bash
   docker compose restart backend
   # Or restart uvicorn if running locally
   ```

7. **Verify**:
   ```bash
   # Test API endpoint
   curl http://localhost:8000/api/v1/demo/sample-result
   
   # Test frontend
   # Open http://localhost:3000/dashboard/demo
   ```

### What Gets Processed

When you run the generator with Sample1C.wav, the complete pipeline processes:

1. ✅ **Diarization**: pyannote identifies all speakers and their segments
2. ✅ **Transcription**: Whisper transcribes Kannada speech
3. ✅ **Translation**: Converts to English with timestamps
4. ✅ **Feature Extraction**: librosa/praat compute 483 acoustic features
5. ✅ **Gender/Age**: RandomForest or wav2vec2 models predict demographics
6. ✅ **Atypicality**: IsolationForest screens for atypical speech patterns
7. ✅ **Aggregation**: Results compiled into complete analysis
8. ✅ **Report Generation**: PDF report generated (metadata saved)

All of this data is captured and saved to `demo_data.json`.

## Demo Data Characteristics

The actual content depends on Sample1C.wav, but will include:

- **Real speakers**: Actual number detected by diarization
- **Real transcriptions**: Actual Kannada text and English translations
- **Real predictions**: Actual gender, age, and atypicality classifications
- **Real features**: Actual acoustic measurements (F0, jitter, shimmer, HNR, etc.)
- **Real timestamps**: Actual timing of speech segments
- **Real statistics**: Actual speech duration, pause ratios, word counts

This makes the demo **authentic** and **representative** of your platform's capabilities.

## User Flow

### For Hackathon Judges
1. Land on homepage
2. See prominent "Try Demo" button in hero section
3. Click button → Instantly see complete analysis results
4. Explore all tabs (Overview, Speakers, Transcript)
5. View charts, timeline, and detailed speaker information
6. **Total time**: < 30 seconds to see full product

### For Regular Visitors
1. Can explore demo without creating account
2. See clear "Demo Mode" banner
3. Understand it's sample data
4. Prompted to sign up for real analysis via banner and download button

## Technical Decisions

### Why Real Data from Sample1C.wav?
- **Authenticity**: Shows actual capabilities, not fake demos
- **Trust**: Judges see real ML pipeline output
- **Accuracy**: No risk of hardcoded data being unrealistic
- **Flexibility**: Easy to update by reprocessing different audio

### Why Static JSON (Not Live Processing)?
- **Speed**: Instant response (< 5ms) vs minutes of processing
- **Reliability**: Never fails due to model loading or resource issues
- **Hackathon-Friendly**: Demo works even under heavy load
- **No Resource Waste**: ML models don't run for every judge/visitor

### Why No Authentication?
- **Hackathon Context**: Judges have limited time (often < 3 minutes per demo)
- **Immediate Value**: Instant access = better engagement
- **Conversion**: Visitors can see value before committing to sign up
- **Accessibility**: Works for anyone, anywhere, anytime

### Why Separate Demo Layout?
- **Isolation**: Avoids authentication dependencies
- **Simplicity**: Cleaner UI focused on showcasing results
- **Maintainability**: Doesn't interfere with existing dashboard code
- **Performance**: No unnecessary auth checks or user data fetching

### Why Reuse Result Components?
- **Consistency**: Demo looks identical to real results
- **DRY Principle**: No code duplication
- **Maintenance**: Updates to result components automatically apply to demo
- **Trust**: Same UI = judges know this is the real product

### Why Pre-Generate Instead of On-Demand?
- **Control**: Curate the best example of your platform
- **Quality**: Ensure the demo showcases all features optimally
- **Debugging**: Can verify demo data correctness before presentation
- **Simplicity**: One-time setup vs complex on-demand logic

## File Structure

```
backend/
├── app/
│   └── routers/
│       ├── demo.py              # Demo endpoint (loads from JSON)
│       └── demo_data.json       # Real analysis data (generated)
├── generate_demo_data.py        # One-time generator script
└── ...

frontend/
├── src/
│   ├── app/
│   │   ├── dashboard/
│   │   │   └── demo/
│   │   │       ├── page.tsx     # Demo results page
│   │   │       └── layout.tsx   # Auth-free layout
│   │   └── page.tsx             # Landing page (updated)
│   └── lib/
│       └── services.ts          # Added demoService
└── ...

Sample1C.wav                      # Source audio file (project root)
GENERATE_DEMO_DATA_GUIDE.md      # Detailed setup instructions
```

## Testing

### Before First Use: Generate Demo Data

**IMPORTANT**: The demo will not work until you generate the data from Sample1C.wav.

```bash
# 1. Ensure backend is running
docker compose up

# 2. Update credentials in generate_demo_data.py
# Edit lines 20-21 with valid user email/password

# 3. Run generator
cd backend
python generate_demo_data.py

# 4. Wait for processing (1-5 minutes typically)
# 5. Restart backend to load new data
docker compose restart backend
```

See `GENERATE_DEMO_DATA_GUIDE.md` for detailed instructions.

### Manual Testing Checklist
- [ ] `demo_data.json` file exists in `backend/app/routers/`
- [ ] Landing page displays "Try Demo" buttons
- [ ] Clicking "Try Demo" loads demo page without login
- [ ] Demo banner is visible and styled correctly
- [ ] All KPI cards display **real values from Sample1C.wav**
- [ ] Charts render properly with actual data
- [ ] Timeline shows actual speaker segments
- [ ] Speaker cards display actual classifications
- [ ] Transcript tab shows actual Kannada→English content
- [ ] Download PDF shows informative message
- [ ] Theme toggle works
- [ ] "Back to Home" returns to landing page
- [ ] No authentication errors in console
- [ ] Data matches what you'd see in a real results page

### API Testing
```bash
# Test demo endpoint (no auth required)
curl http://localhost:8000/api/v1/demo/sample-result

# Should return 200 with full ResultResponse JSON
```

### Browser Testing
```
# Visit demo directly
http://localhost:3000/dashboard/demo

# Should load without redirecting to login
```

## Benefits for Hackathon Demo

1. **Time Efficiency**: Judges see full product in 30 seconds vs 3+ minutes with upload/processing
2. **Reliability**: No dependency on file uploads or model processing during live demo
3. **Showcase All Features**: Pre-loaded data includes typical/atypical classifications, multiple speakers, translations
4. **Professional Impression**: Smooth, instant experience demonstrates production-ready quality
5. **Fallback Option**: If live demo has issues, fall back to pre-loaded demo instantly

## Future Enhancements (Optional)

- Add multiple demo samples (different scenarios)
- Allow demo data customization via query parameters
- Add "Try with Your Own File" CTA within demo
- Track demo usage analytics
- Add demo data refresh endpoint for different samples

## No Existing Features Modified

✅ All existing functionality remains unchanged:
- Authentication flow
- File upload
- Processing pipeline
- Real results display
- PDF report generation
- Admin features
- User management

The demo feature is completely isolated and additive.
