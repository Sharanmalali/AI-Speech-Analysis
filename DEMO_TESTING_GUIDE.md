# Demo Mode Testing Guide

## Quick Start Testing

### 1. Start the Application

#### Option A: Docker (Production-like)
```bash
# Start full stack
docker compose up --build

# Or for development with hot reload
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

#### Option B: Local Development
```bash
# Terminal 1 - Backend
cd backend
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 2. Access Demo Mode

#### Direct Demo Access (No Login)
```
http://localhost:3000/dashboard/demo
```
**Expected**: Demo page loads instantly with sample analysis

#### Via Landing Page
1. Go to `http://localhost:3000`
2. Click "Try Demo" button in hero section
3. Should redirect to demo page

### 3. Test Backend API

#### Test Demo Endpoint
```bash
# Should work without authentication
curl http://localhost:8000/api/v1/demo/sample-result
```

**Expected Response**:
```json
{
  "job_id": "demo-job-00000000-0000-0000-0000-000000000000",
  "status": "completed",
  "detected_speakers": 4,
  "language_source": "kn",
  "language_target": "en",
  "processing_time_seconds": 48.3,
  "audio": {
    "duration_seconds": 105.8,
    "sample_rate": 16000,
    "channels": 1,
    "original_filename": "demo_mental_health_conversation.wav"
  },
  "speakers": [...]
}
```

#### Check API Documentation
```
http://localhost:8000/docs
```
Look for `/api/v1/demo/sample-result` endpoint in the "demo" section

## Feature Testing Checklist

### Landing Page
- [ ] "Try Demo" button appears in hero section (between "Start analysing" and "Sign in")
- [ ] "Try Demo" button has Sparkles icon
- [ ] "Try Demo" button appears in bottom CTA section
- [ ] Clicking button navigates to `/dashboard/demo`
- [ ] No authentication prompt appears

### Demo Page Layout
- [ ] Page loads without requiring login
- [ ] Top bar shows "AblePro / Demo Analysis"
- [ ] "Demo Mode" badge displays in top right
- [ ] "Back to Home" button is visible
- [ ] Theme toggle works
- [ ] Background and styling match dashboard aesthetic

### Demo Banner
- [ ] Prominent banner at top of content
- [ ] Shows Sparkles icon
- [ ] Contains "Demo Mode" title
- [ ] Contains descriptive text about sample analysis
- [ ] Styled with gradient border and background

### Analysis Results Display

#### KPI Cards
- [ ] Shows 4 speakers
- [ ] Duration: "01:45" (105.8 seconds)
- [ ] Atypical speakers: 1
- [ ] Processing time: "48.3s"
- [ ] Animated counters work
- [ ] Icons display correctly

#### Overview Tab (Default)
- [ ] Speaking Time Chart renders
  - [ ] Shows 4 speakers
  - [ ] Displays speech duration for each
  - [ ] Uses bar chart
- [ ] Speech/Pause Chart renders
  - [ ] Shows speech vs pause ratio
  - [ ] Uses bar chart
- [ ] Timeline renders
  - [ ] Shows speaker segments over time
  - [ ] Colored segments for each speaker
  - [ ] Interactive tooltips

#### Speakers Tab
- [ ] Shows 4 speaker cards in grid
- [ ] Each card displays:
  - [ ] Speaker label (SPEAKER_01, etc.)
  - [ ] Colored avatar/indicator
  - [ ] Gender and age prediction
  - [ ] Atypicality status (typical/atypical)
  - [ ] Acoustic features
  - [ ] Speaking statistics
- [ ] SPEAKER_02 shows "atypical" status
- [ ] Others show "typical" status

#### Transcript Tab
- [ ] Chronological conversation flow
- [ ] Shows both Kannada and English text
- [ ] Timestamps for each segment
- [ ] Speaker identification
- [ ] Proper formatting and spacing
- [ ] Scrollable content

### Interactions
- [ ] Tabs switch smoothly
- [ ] Charts are responsive
- [ ] No loading errors in console
- [ ] No authentication errors
- [ ] Clicking "Download PDF" shows info toast
  - [ ] Message: "Demo PDF download is not available in demo mode"
  - [ ] Description mentions signing up

### Navigation
- [ ] "Back to Home" button returns to landing page
- [ ] Can navigate back to demo from homepage
- [ ] Browser back/forward buttons work
- [ ] Direct URL access works: `/dashboard/demo`

## Performance Testing

### Load Time
- [ ] Demo page loads in < 2 seconds
- [ ] No unnecessary API calls
- [ ] Data cached properly (React Query)
- [ ] Smooth animations

### API Response
- [ ] Demo endpoint responds in < 100ms
- [ ] No database queries
- [ ] No authentication checks
- [ ] Returns same data on every call

## Browser Compatibility

Test in multiple browsers:
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari
- [ ] Mobile browsers

## Error Scenarios

### API Failure Simulation
Temporarily stop backend and verify:
- [ ] Error message displays
- [ ] No blank/crashed page
- [ ] User can navigate back

### Network Issues
Throttle network in DevTools:
- [ ] Loading skeleton displays
- [ ] Graceful loading state
- [ ] Eventually loads or shows error

## Mobile Responsive Testing

Test at different viewports:
- [ ] Mobile (375px width)
  - [ ] Buttons stack properly
  - [ ] Cards display in single column
  - [ ] Charts are readable
- [ ] Tablet (768px width)
  - [ ] 2-column grid for cards
  - [ ] All content accessible
- [ ] Desktop (1280px width)
  - [ ] Full 3-4 column layouts
  - [ ] Optimal spacing

## Security Testing

### Authentication Bypass Verification
- [ ] Demo route doesn't trigger AuthGuard
- [ ] No redirect to login page
- [ ] No auth tokens required
- [ ] Works in incognito/private mode

### API Security
- [ ] Demo endpoint has no side effects
- [ ] Cannot modify data through demo endpoint
- [ ] No sensitive information exposed
- [ ] Rate limiting still applies (if configured)

## Integration with Existing Features

### Verify No Breakage
- [ ] Login flow still works
- [ ] Upload still works
- [ ] Real results pages still work
- [ ] Dashboard navigation unaffected
- [ ] Admin features unaffected

### Demo Isolation
- [ ] Demo data doesn't appear in job lists
- [ ] Demo doesn't create database records
- [ ] Demo uses separate layout (no sidebar)
- [ ] Demo user profile not required

## Accessibility Testing

- [ ] Keyboard navigation works
- [ ] Screen reader compatibility
- [ ] Proper ARIA labels
- [ ] Sufficient color contrast
- [ ] Focus indicators visible

## Content Validation

### Demo Data Quality
- [ ] Kannada text is realistic
- [ ] English translations make sense
- [ ] Conversation flows naturally
- [ ] Features demonstrate product value
- [ ] One speaker flagged as atypical
- [ ] Gender/age predictions diverse
- [ ] Timestamps are sequential
- [ ] No Lorem Ipsum or placeholder text

## Documentation
- [ ] README updated (if needed)
- [ ] API docs include demo endpoint
- [ ] Implementation guide created
- [ ] Testing guide created (this file)

## Success Criteria

✅ **Demo is successful if**:
1. Loads in < 30 seconds from landing page
2. Displays all analysis features
3. Works without authentication
4. No console errors
5. Responsive on all devices
6. Returns to homepage easily
7. Judges can explore full product instantly

## Troubleshooting

### Demo page shows auth error
- Check demo layout bypasses AuthGuard
- Verify demo endpoint is public
- Clear browser cache

### Charts not rendering
- Check browser console for errors
- Verify Recharts library is installed
- Test in different browser

### Demo endpoint 404
- Verify backend router registered
- Check main.py includes "demo" in router list
- Restart backend server

### Styling issues
- Clear Next.js cache: `rm -rf .next`
- Rebuild: `npm run build`
- Check Tailwind classes are valid

## Reporting Issues

When reporting issues, include:
1. Steps to reproduce
2. Expected vs actual behavior
3. Browser and version
4. Console errors (if any)
5. Screenshots
6. Backend logs (if API related)
