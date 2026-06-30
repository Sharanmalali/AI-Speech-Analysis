"""Demo endpoint: publicly accessible sample analysis for hackathon judges."""

from fastapi import APIRouter

from app.models.enums import JobStatus
from app.schemas.results import (
    AudioSummary,
    PredictionRead,
    ResultResponse,
    SpeakerRead,
    TranscriptionRead,
)

router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("/sample-result", response_model=ResultResponse, summary="Get demo analysis results (public)")
async def get_demo_results() -> ResultResponse:
    """
    Returns a pre-loaded sample analysis result for demonstration purposes.
    
    This endpoint is publicly accessible (no authentication required) and showcases
    a multi-speaker conversation with:
    - 4 speakers in a general conversation
    - Kannada → English transcription
    - Mixed typical/atypical speech classifications
    - Gender and age predictions
    - Full acoustic features
    
    Perfect for hackathon judges to see the full product instantly without uploading
    or waiting for processing.
    """
    
    # Sample demo data: 4 speakers in a general conversation about mental wellness
    speakers_data = [
        SpeakerRead(
            id="demo-speaker-1",
            label="SPEAKER_01",
            diarization_id="diarization-demo-1",
            color="#3B82F6",  # blue
            total_speech_seconds=42.5,
            total_pause_seconds=8.2,
            segment_count=5,
            word_count=156,
            prediction=PredictionRead(
                gender="male",
                gender_confidence=0.89,
                age_group="adult",
                age_confidence=0.82,
                raw_class_label="adult_male",
                gender_age_source="hf",
                atypicality="typical",
                atypicality_score=-0.12,
                atypicality_confidence=0.91,
                features={
                    "latency_to_speak_sec": 0.45,
                    "pause_to_speech_ratio": 0.19,
                    "pronunciation_flux_var": 0.08,
                    "f0_mean": 142.3,
                    "jitter": 0.012,
                    "shimmer": 0.045,
                    "hnr": 18.7,
                },
            ),
            transcriptions=[
                TranscriptionRead(
                    id="trans-1-1",
                    start_time=2.1,
                    end_time=8.4,
                    text_source="ನಮಸ್ಕಾರ ಎಲ್ಲರಿಗೂ. ಇಂದು ನಾವು ಮಾನಸಿಕ ಆರೋಗ್ಯದ ಬಗ್ಗೆ ಮಾತನಾಡೋಣ",
                    text_translated="Hello everyone. Today let's talk about mental health",
                    confidence=0.94,
                ),
                TranscriptionRead(
                    id="trans-1-2",
                    start_time=18.7,
                    end_time=26.3,
                    text_source="ಮಾನಸಿಕ ಆರೋಗ್ಯ ನಮ್ಮ ದೈಹಿಕ ಆರೋಗ್ಯದಷ್ಟೇ ಮುಖ್ಯ",
                    text_translated="Mental health is as important as our physical health",
                    confidence=0.91,
                ),
                TranscriptionRead(
                    id="trans-1-3",
                    start_time=42.1,
                    end_time=51.8,
                    text_source="ನಾವು ದಿನಾಲು ಒತ್ತಡವನ್ನು ಅನುಭವಿಸುತ್ತೇವೆ ಮತ್ತು ಅದನ್ನು ನಿರ್ವಹಿಸುವುದು ಕಷ್ಟ",
                    text_translated="We experience stress daily and managing it is difficult",
                    confidence=0.88,
                ),
                TranscriptionRead(
                    id="trans-1-4",
                    start_time=68.2,
                    end_time=76.5,
                    text_source="ಅದಕ್ಕಾಗಿಯೇ ವೃತ್ತಿಪರ ಸಹಾಯ ಪಡೆಯುವುದು ಬಹಳ ಮುಖ್ಯ",
                    text_translated="That's why seeking professional help is very important",
                    confidence=0.93,
                ),
                TranscriptionRead(
                    id="trans-1-5",
                    start_time=94.3,
                    end_time=102.1,
                    text_source="ಧನ್ಯವಾದಗಳು ಈ ಸಂಭಾಷಣೆಗೆ",
                    text_translated="Thank you for this conversation",
                    confidence=0.96,
                ),
            ],
        ),
        SpeakerRead(
            id="demo-speaker-2",
            label="SPEAKER_02",
            diarization_id="diarization-demo-2",
            color="#10B981",  # green
            total_speech_seconds=38.7,
            total_pause_seconds=12.5,
            segment_count=4,
            word_count=142,
            prediction=PredictionRead(
                gender="female",
                gender_confidence=0.91,
                age_group="adult",
                age_confidence=0.86,
                raw_class_label="adult_female",
                gender_age_source="hf",
                atypicality="atypical",
                atypicality_score=0.58,
                atypicality_confidence=0.79,
                features={
                    "latency_to_speak_sec": 1.82,
                    "pause_to_speech_ratio": 0.42,
                    "pronunciation_flux_var": 0.24,
                    "f0_mean": 218.5,
                    "jitter": 0.028,
                    "shimmer": 0.089,
                    "hnr": 12.3,
                },
            ),
            transcriptions=[
                TranscriptionRead(
                    id="trans-2-1",
                    start_time=9.2,
                    end_time=17.8,
                    text_source="ಹೌದು... ನಾನು ಇತ್ತೀಚೆಗೆ ಬಹಳ ಚಿಂತಿತಳಾಗಿದ್ದೇನೆ",
                    text_translated="Yes... I have been very worried recently",
                    confidence=0.87,
                ),
                TranscriptionRead(
                    id="trans-2-2",
                    start_time=27.4,
                    end_time=40.9,
                    text_source="ಕೆಲಸದ ಒತ್ತಡ ಮತ್ತು... ವೈಯಕ್ತಿಕ ಸಮಸ್ಯೆಗಳು ನನ್ನನ್ನು ಪರಿಣಾಮ ಬೀರುತ್ತಿವೆ",
                    text_translated="Work stress and... personal issues are affecting me",
                    confidence=0.84,
                ),
                TranscriptionRead(
                    id="trans-2-3",
                    start_time=52.6,
                    end_time=66.8,
                    text_source="ಕೆಲವೊಮ್ಮೆ... ನಾನು ಮಾತನಾಡಲು ಕಷ್ಟ ಪಡುತ್ತೇನೆ ಮತ್ತು... ಮಾತುಗಳು ಬರುವುದಿಲ್ಲ",
                    text_translated="Sometimes... I find it hard to speak and... words don't come",
                    confidence=0.81,
                ),
                TranscriptionRead(
                    id="trans-2-4",
                    start_time=77.3,
                    end_time=92.7,
                    text_source="ನನಗೆ... ಸಹಾಯ ಬೇಕು ಎಂದು ನಾನು ಭಾವಿಸುತ್ತೇನೆ",
                    text_translated="I... I think I need help",
                    confidence=0.89,
                ),
            ],
        ),
        SpeakerRead(
            id="demo-speaker-3",
            label="SPEAKER_03",
            diarization_id="diarization-demo-3",
            color="#F59E0B",  # amber
            total_speech_seconds=35.2,
            total_pause_seconds=6.8,
            segment_count=4,
            word_count=128,
            prediction=PredictionRead(
                gender="male",
                gender_confidence=0.87,
                age_group="senior",
                age_confidence=0.81,
                raw_class_label="senior_male",
                gender_age_source="model",
                atypicality="typical",
                atypicality_score=-0.24,
                atypicality_confidence=0.88,
                features={
                    "latency_to_speak_sec": 0.52,
                    "pause_to_speech_ratio": 0.21,
                    "pronunciation_flux_var": 0.09,
                    "f0_mean": 128.7,
                    "jitter": 0.015,
                    "shimmer": 0.051,
                    "hnr": 17.2,
                },
            ),
            transcriptions=[
                TranscriptionRead(
                    id="trans-3-1",
                    start_time=11.5,
                    end_time=18.2,
                    text_source="ನಿಮ್ಮ ಭಾವನೆಗಳನ್ನು ಹಂಚಿಕೊಳ್ಳುವುದು ಧೈರ್ಯದ ಕಾರ್ಯ",
                    text_translated="Sharing your feelings is a brave act",
                    confidence=0.92,
                ),
                TranscriptionRead(
                    id="trans-3-2",
                    start_time=28.1,
                    end_time=41.5,
                    text_source="ನನ್ನ ಅನುಭವದಲ್ಲಿ, ವೃತ್ತಿಪರರೊಂದಿಗೆ ಮಾತನಾಡುವುದು ಬಹಳ ಸಹಾಯ ಮಾಡುತ್ತದೆ",
                    text_translated="In my experience, talking to professionals helps a lot",
                    confidence=0.90,
                ),
                TranscriptionRead(
                    id="trans-3-3",
                    start_time=53.8,
                    end_time=67.4,
                    text_source="ಧ್ಯಾನ ಮತ್ತು ಯೋಗವು ಸಹ ಮಾನಸಿಕ ಶಾಂತಿಗೆ ಸಹಾಯ ಮಾಡುತ್ತದೆ",
                    text_translated="Meditation and yoga also help with mental peace",
                    confidence=0.93,
                ),
                TranscriptionRead(
                    id="trans-3-4",
                    start_time=78.6,
                    end_time=93.2,
                    text_source="ನಿಮಗೆ ಸರಿಯಾದ ಬೆಂಬಲ ಸಿಗುತ್ತದೆ ಎಂದು ನನಗೆ ವಿಶ್ವಾಸವಿದೆ",
                    text_translated="I am confident you will find the right support",
                    confidence=0.91,
                ),
            ],
        ),
        SpeakerRead(
            id="demo-speaker-4",
            label="SPEAKER_04",
            diarization_id="diarization-demo-4",
            color="#8B5CF6",  # purple
            total_speech_seconds=28.9,
            total_pause_seconds=9.3,
            segment_count=3,
            word_count=98,
            prediction=PredictionRead(
                gender="female",
                gender_confidence=0.85,
                age_group="adult",
                age_confidence=0.79,
                raw_class_label="adult_female",
                gender_age_source="llm",
                atypicality="typical",
                atypicality_score=-0.18,
                atypicality_confidence=0.86,
                features={
                    "latency_to_speak_sec": 0.58,
                    "pause_to_speech_ratio": 0.23,
                    "pronunciation_flux_var": 0.11,
                    "f0_mean": 205.4,
                    "jitter": 0.016,
                    "shimmer": 0.048,
                    "hnr": 16.8,
                },
            ),
            transcriptions=[
                TranscriptionRead(
                    id="trans-4-1",
                    start_time=19.3,
                    end_time=27.1,
                    text_source="ನಾವೆಲ್ಲರೂ ಕಷ್ಟದ ಸಮಯವನ್ನು ಎದುರಿಸುತ್ತೇವೆ",
                    text_translated="We all face difficult times",
                    confidence=0.89,
                ),
                TranscriptionRead(
                    id="trans-4-2",
                    start_time=43.2,
                    end_time=52.1,
                    text_source="ಸಮುದಾಯದ ಬೆಂಬಲವು ಚೇತರಿಕೆಯಲ್ಲಿ ಪ್ರಮುಖ ಪಾತ್ರವನ್ನು ವಹಿಸುತ್ತದೆ",
                    text_translated="Community support plays a key role in recovery",
                    confidence=0.92,
                ),
                TranscriptionRead(
                    id="trans-4-3",
                    start_time=69.4,
                    end_time=77.8,
                    text_source="ನಿಮ್ಮ ಯಾತ್ರೆಯಲ್ಲಿ ನಾವು ನಿಮ್ಮೊಂದಿಗೆ ಇದ್ದೇವೆ",
                    text_translated="We are with you in your journey",
                    confidence=0.94,
                ),
            ],
        ),
    ]
    
    return ResultResponse(
        job_id="demo-job-00000000-0000-0000-0000-000000000000",
        status=JobStatus.COMPLETED,
        detected_speakers=4,
        language_source="kn",
        language_target="en",
        processing_time_seconds=48.3,
        audio=AudioSummary(
            duration_seconds=105.8,
            sample_rate=16000,
            channels=1,
            original_filename="demo_mental_health_conversation.wav",
        ),
        speakers=speakers_data,
        has_report=True,
    )
