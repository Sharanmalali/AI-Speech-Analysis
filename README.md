# 🎙️ AblePro Solutions

### AI-Powered Multi-Speaker Mental Health Audio Analytics Platform

<div align="center">

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)

**[🚀 Try Demo](http://localhost:3000/demo)** • **[📖 Documentation](docs/)** • **[🔧 API Docs](http://localhost:8000/docs)**

</div>

---

## 🌟 Overview

AblePro is a comprehensive voice diagnostic and demographic analysis system that transforms raw audio recordings into actionable clinical insights. The platform processes multi-speaker conversations end-to-end, delivering:

- 🗣️ **Speaker Diarization** — Isolates "who spoke when" in multi-party conversations
- 🌐 **Kannada → English Transcription** — Real-time speech-to-text with precise timestamps
- 👤 **Demographic Analysis** — Per-speaker gender and age-group prediction
- 🧠 **Clinical Screening** — Typical vs. atypical speech pattern detection
- 📊 **Interactive Dashboard** — Real-time visualizations with charts, timelines, and transcripts
- 📄 **Clinical PDF Reports** — Professional, downloadable diagnostic summaries

---
## 🎥 Demo Videos

- **📌 Full Project Walkthrough:**  
  https://drive.google.com/file/d/1_A6MIu-8MsdVj5JagKJeLnhBrNlc2Noq/view?usp=drive_link

- **🧠 ML Model Working:**  
  https://drive.google.com/file/d/1f8J3FUyhAcTKho-Zz1fCN0dFj4yjYeBB/view?usp=drive_link

## 🎯 Key Features

### 🔬 Advanced Audio Analysis
- **Multi-speaker isolation** using state-of-the-art pyannote.audio diarization
- **Acoustic feature extraction**: Jitter, Shimmer, HNR, F0 pitch, spectral flux, pause ratios
- **Unsupervised anomaly detection** via Isolation Forest for clinical typicality screening
- **Deep learning transformers** for demographic classification (wav2vec2-based models)

### 🏗️ Production-Ready Architecture
- **Containerized deployment** with Docker Compose for seamless scaling
- **Asynchronous processing** via Celery + Redis for heavy ML workloads
- **Real-time progress tracking** with WebSocket-ready job status updates
- **Enterprise security**: JWT auth, RBAC, rate limiting, audit logs

### 🎨 Modern User Experience
- **Responsive dashboard** built with Next.js 15 and Tailwind CSS
- **Real-time charts** using Recharts for data visualization
- **Dark/light theme** support with next-themes
- **Accessible design** following WCAG guidelines

---

## 🧠 Model Architecture

AblePro uses a hybrid, 3-stage ML pipeline that balances performance, interpretability, and accuracy:

<div align="center">
  <img src="resources/model_architecture.png" alt="Model Architecture" width="800"/>
  <p><i>Sequential hybrid pipeline combining pre-trained transformers with custom classifiers</i></p>
</div>

### 🔄 Processing Pipeline

1. **Segmentation Engine** (pyannote.audio)
   - Pre-trained speaker diarization
   - Isolates speaker segments with timestamps
   - Handles overlapping speech and multi-party conversations

2. **Typicality Engine** (Custom Scikit-Learn)
   - Extracts 7 acoustic biomarkers (latency, pause ratio, pitch, jitter, shimmer, HNR)
   - StandardScaler normalization
   - IsolationForest (200 trees) for anomaly detection
   - Detects atypical speech patterns for clinical review

3. **Demographic Engine** (Hugging Face Transformers)
   - **Gender**: `wav2vec2-large-xlsr-53-gender-recognition-librispeech`
   - **Age Group**: `wav2vec2-xls-r-300m-adult-child-cls`
   - Transfer learning from massive pre-trained datasets

### 🎯 Design Rationale

**Why Hybrid?** Instead of training a monolithic neural network from scratch (requiring terabytes of data), this system:
- ✅ Leverages state-of-the-art pre-trained transformers for standard demographics
- ✅ Uses lightweight, interpretable scikit-learn for custom clinical tasks
- ✅ Provides explainable AI with clear acoustic feature contributions
- ✅ Requires minimal training data for deployment

**Optimized Deployment**: Docker volume caching prevents re-downloading 1.5GB+ of model weights on every restart, ensuring rapid deployment and low bandwidth consumption.

---

## 📊 Visualization Examples

### Mel-Spectrograms
High-resolution frequency-domain representations showing phonetic patterns, pauses, and vocal intensity:

<div align="center">
  <img src="resources/spectogram1.png" alt="Spectrogram Example 1" width="400"/>
  <img src="resources/spectogram2.png" alt="Spectrogram Example 2" width="400"/>
  <p><i>Magma-mapped spectrograms revealing frequency distribution over time</i></p>
</div>

<div align="center">
  <img src="resources/spectogram3.png" alt="Spectrogram Example 3" width="400"/>
  <img src="resources/spectogram4.png" alt="Spectrogram Example 4" width="400"/>
  <p><i>Visual representation of vocal cord vibrations and acoustic biomarkers</i></p>
</div>


### Dashboard Insights
The frontend translates complex ML outputs into intuitive visualizations:
- 📈 **Speaking time distribution** (pie charts)
- 📊 **Speech vs. pause analysis** (bar charts)
- ⏱️ **Conversation timeline** (interactive timeline)
- 🎤 **Speaker cards** with confidence scores
- 💬 **Bilingual transcripts** (Kannada + English)

---

## 🏛️ System Architecture

```
                        ┌─────────────┐
   Browser  ───────────▶│    NGINX    │  reverse proxy (:80)
                        └──────┬──────┘
                  /            │            /api
          ┌───────────────┐    │    ┌──────────────────┐
          │  Next.js 15   │◀───┴───▶│   FastAPI (API)  │
          │  (frontend)   │         └────────┬─────────┘
          └───────────────┘                  │ enqueue
                                             ▼
                                   ┌───────────────────┐
                                   │  Redis (broker +  │
                                   │  result + limits) │
                                   └─────────┬─────────┘
                                             ▼
                                   ┌───────────────────┐
                                   │  Celery worker    │
                                   │  (ML pipeline)    │
                                   └─────────┬─────────┘
        ┌───────────────┬──────────┬─────────┴───────────┬───────────────┐
        ▼               ▼          ▼                     ▼               ▼
  Diarization    Transcription   Feature           Gender/Age      Atypicality
  (pyannote)     (Whisper)       extraction        (wav2vec2)      (IForest)
                                 (librosa/praat)
```

**Persistence**: Supabase PostgreSQL + Supabase Storage (with local filesystem fallback)  
**ML Layer**: Service-oriented, lazily-loaded singletons warmed at worker startup

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Hugging Face account (for model access tokens)

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/yourusername/AI-Speech-Analysis.git
cd AI-Speech-Analysis
```

### 2️⃣ Configure Environment
```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and set:
```env
JWT_SECRET_KEY=your_secret_key_here
HUGGINGFACE_TOKEN=your_hf_token_here
DATABASE_URL=postgresql://user:password@localhost:5432/ablepro
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_key
```

### 3️⃣ Launch with Docker
```bash
# Production (NGINX on port 80)
docker compose up -d --build

# Development (hot reload, API :8000, web :3000, flower :5555)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

> ⚠️ **First boot takes 5-10 minutes** as models download. Subsequent starts: ~10 seconds.

### 4️⃣ Access the Application
- **Web Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Demo Mode**: http://localhost:3000/demo *(no login required)*

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** — High-performance async API framework
- **Celery** — Distributed task queue for ML processing
- **Redis** — Message broker + caching layer
- **SQLAlchemy** — Database ORM with Alembic migrations
- **Pydantic** — Data validation and settings management

### ML & Audio Processing
- **pyannote.audio** — Speaker diarization
- **OpenAI Whisper** — Speech-to-text transcription
- **librosa** — Audio feature extraction
- **Parselmouth (Praat)** — Acoustic analysis (jitter, shimmer, HNR)
- **scikit-learn** — IsolationForest, StandardScaler
- **Hugging Face Transformers** — wav2vec2 models

### Frontend
- **Next.js 15** — React framework with App Router
- **TypeScript** — Type-safe development
- **Tailwind CSS** — Utility-first styling
- **Recharts** — Data visualization
- **Framer Motion** — Smooth animations
- **Zustand** — State management

### DevOps
- **Docker & Docker Compose** — Containerization
- **NGINX** — Reverse proxy and load balancing
- **PostgreSQL** — Relational database
- **Supabase** — BaaS for storage and auth

---

## 📁 Project Structure

```
.
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── config/          # Pydantic settings
│   │   ├── core/            # Security, logging, exceptions
│   │   ├── database/        # SQLAlchemy setup
│   │   ├── models/          # ORM models
│   │   ├── schemas/         # Pydantic request/response models
│   │   ├── routers/         # API endpoints
│   │   │   ├── auth.py      # Authentication
│   │   │   ├── upload.py    # Audio upload
│   │   │   ├── jobs.py      # Job management
│   │   │   ├── results.py   # Analysis results
│   │   │   ├── reports.py   # PDF generation
│   │   │   └── demo.py      # Public demo endpoint
│   │   ├── services/        # Business logic
│   │   │   └── ml/          # ML pipeline
│   │   ├── tasks/           # Celery tasks
│   │   └── utils/           # Helper functions
│   ├── alembic/             # Database migrations
│   └── tests/               # Pytest suite
│
├── frontend/                # Next.js application
│   └── src/
│       ├── app/             # App Router pages
│       │   ├── (auth)/      # Auth pages
│       │   ├── dashboard/   # Protected dashboard
│       │   └── demo/        # Public demo (no auth)
│       ├── components/      # React components
│       │   ├── ui/          # Reusable UI components
│       │   ├── dashboard/   # Dashboard-specific
│       │   ├── results/     # Charts, timeline, transcript
│       │   └── marketing/   # Landing page
│       ├── lib/             # Utilities, API client
│       └── hooks/           # Custom React hooks
│
├── models/                  # Pre-trained ML artifacts
│   ├── atypicality_scaler.pkl
│   ├── atypicality_iforest.pkl
│   └── gender_age_clf.pkl
│
├── docker/                  # Docker configurations
│   └── nginx/               # NGINX configs
│
├── docs/                    # Documentation
│   ├── ARCHITECTURE.md      # System design
│   └── API.md               # API reference
│
├── docker-compose.yml       # Production stack
└── docker-compose.dev.yml   # Development overrides
```

---

## 🔧 Local Development (No Docker)

### Backend Setup
```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

# System dependencies (macOS)
brew install ffmpeg libsndfile

# Configure and run
cp .env.example .env
uvicorn app.main:app --reload  # API on http://localhost:8000

# Start Celery worker (separate terminal)
celery -A app.tasks.celery_app worker --loglevel=info
```

### Frontend Setup
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev  # App on http://localhost:3000
```

---

## ⚙️ Configuration

Key environment variables (see `backend/.env.example`):

| Variable | Description | Required |
|----------|-------------|----------|
| `JWT_SECRET_KEY` | Signs access/refresh tokens | ✅ Production |
| `HUGGINGFACE_TOKEN` | Access gated pyannote models | ✅ Always |
| `DATABASE_URL` | PostgreSQL connection string | Optional (defaults to SQLite) |
| `SUPABASE_URL` | Supabase project URL | Optional |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase admin key | Optional |
| `REDIS_URL` | Redis connection string | Auto-configured in Docker |
| `WHISPER_MODEL_SIZE` | `tiny`, `small`, `medium`, `large` | Optional (default: `small`) |
| `MAX_UPLOAD_SIZE_MB` | Upload file size limit | Optional (default: 100) |

---

## 🧪 Testing

```bash
cd backend
pip install -r requirements-dev.txt
pytest  # Runs unit + integration tests
```

**Test suite features**:
- ✅ Hermetic (SQLite, local storage, stubbed tasks)
- ✅ No external dependencies required
- ✅ ML artifact validation included

---

## 🔒 Security Features

- 🔐 **JWT Authentication** with refresh token rotation
- 👥 **RBAC** (Admin, Doctor, User roles)
- 🚦 **Rate Limiting** via SlowAPI + Redis
- 🛡️ **Input Validation** (extension, MIME type, size, magic bytes)
- 📝 **Audit Trails** for sensitive operations
- 🔒 **Secure Storage** with signed URLs
- 🌐 **CORS** allow-listing
- 🐳 **Hardened Containers** (non-root, health checks)

---

## 🎭 Demo Mode

Try the platform instantly without signup:

### Features
- 🌍 **Public access** — No authentication required
- ⚡ **Instant loading** — Pre-computed results (< 1 second)
- 🎯 **Full functionality** — All features visible
- 📊 **Real data** — Actual ML pipeline output

### Access
```
http://localhost:3000/demo
```

Perfect for hackathon judges, stakeholders, or quick demonstrations!

---

## 📚 Documentation

- **[Architecture Guide](docs/ARCHITECTURE.md)** — System design and component interaction
- **[API Reference](docs/API.md)** — Complete REST API documentation
- **[API Playground](http://localhost:8000/docs)** — Interactive Swagger UI

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---


## 🙏 Acknowledgments

- **pyannote.audio** team for speaker diarization
- **OpenAI** for Whisper ASR
- **Hugging Face** for transformer models
- **Praat/Parselmouth** for acoustic analysis tools

---

##  Support

- 📖 Docs: [Documentation](docs/)

---
