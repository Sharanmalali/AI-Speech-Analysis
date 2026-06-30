AblePro: Comprehensive Voice Diagnostic & Demographic System
An end-to-end, containerized web application that processes raw audio to isolate individual speakers and performs multi-dimensional acoustic analysis. The system predicts the clinical typicality, gender, and age group of each speaker using a hybrid pipeline of custom machine learning models and state-of-the-art deep learning transformers.

🧠 Core Topics & Technologies
This project integrates several advanced audio processing and machine learning domains:

Speaker Diarization: Isolating "who spoke when" in multi-speaker audio files.

Acoustic Feature Extraction: Parsing raw PCM audio into mathematical vocal markers (Jitter, Shimmer, Harmonics-to-Noise Ratio, F0 Pitch, Spectral Flux).

Unsupervised Anomaly Detection: Classifying voices as Typical vs. Atypical using an Isolation Forest algorithm.

Deep Learning Audio Classification: Utilizing Transformer-based neural networks for demographic predictions (Age and Gender).

Containerized Full-Stack Development: Linking a responsive frontend dashboard to a heavy-compute Python backend via Docker.

Tech Stack: Python | FastAPI / Flask | React / HTML/JS | Docker | PyAnnote | Hugging Face Transformers | Scikit-Learn | Librosa | Parselmouth (Praat)

🏗️ Technical Documentation & System Design
1. Model Architecture
The processing engine relies on a sequential, 3-stage hybrid pipeline:

Segmentation Engine (pyannote.audio): A pre-trained diarization pipeline that maps timestamps for distinct speakers, allowing the system to slice the master audio file into clean, speaker-specific arrays.

Typicality Engine (Custom Scikit-Learn): Extracts custom acoustic features (latency, pause ratio, pitch, jitter, shimmer) and scales them. An IsolationForest model evaluates these features to detect clinical atypicality based on vocal biomarkers.

Demographic Engine (Hugging Face Transformers): * Gender: wav2vec2-large-xlsr-53-gender-recognition-librispeech (Predicts Male/Female).

Age Group: wav2vec2-xls-r-300m-adult-child-cls (Predicts Adult/Child).

2. System Design & Justification
Modular Hybrid Approach: Instead of training a massive, monolithic neural network from scratch (which requires terabytes of data), this system uses a hybrid approach. It leverages state-of-the-art pre-trained Transformer models for standard demographics (Age/Gender) while using a lightweight, highly interpretable scikit-learn model for the custom clinical Typicality task.

Dockerized Caching: The backend container mounts a persistent volume for the Hugging Face HF_HOME cache. This design choice prevents the system from re-downloading over 1.5GB of model weights on every server restart, ensuring rapid deployment and low bandwidth consumption.

📊 Visualization & Dashboard Insights
The frontend of this application acts as a comprehensive diagnostic dashboard, translating complex backend arrays into readable, graphical insights:

Master Diagnostics Table: A clean, scannable grid displaying Speaker ID, Total Speech Duration, Typicality Status, Predicted Gender, and Predicted Age Group.

Mel-Spectrograms: High-resolution, magma-mapped visual representations of the audio frequencies, allowing users to physically see phonetic pauses, vocal intensity, and frequency distribution over time.

Acoustic Feature Visualizations: * Pitch (F0) Contours: Tracking vocal cord vibration frequencies across the speaker's timeline.

Intensity Graphs: Visualizing the amplitude/loudness of the speech segments.

Biomarker Radars: (Optional) Visualizing Jitter, Shimmer, and HNR deviations to justify the "Atypical" classification to the end-user.

🚀 Installation & Setup
Because the application is fully containerized, deployment is highly streamlined.

1. Clone the repository

Bash
git clone https://github.com/yourusername/AblePro.git
cd AblePro
2. Configure Environment Variables
Create a .env file in the root directory and add your Hugging Face token (required for PyAnnote and the Transformer models):

Code snippet
HF_TOKEN=your_huggingface_token_here
3. Build and Run via Docker

Bash
docker-compose up --build
Note: The first boot will take several minutes as the backend downloads the deep learning models into the persistent Docker volume. Subsequent boots will take seconds.

4. Access the Dashboard
Open your browser and navigate to http://localhost:3000 (or your configured frontend port) to upload your first audio file!