# UnlockVideos - Video Q&A with OpenAI RAG

**Live Demo:** [aljanjic.com](https://aljanjic.com)  
**Context:** Personal learning project (2024) exploring OpenAI API integration, deployed to production

## Overview
End-to-end full-stack application that enables Q&A over video transcripts using RAG (Retrieval-Augmented Generation).

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/unlock-videos.git
cd unlock-videos

# Set up environment variables
cp .env.example .env
# Edit .env with your OpenAI API key

# Run with Docker
docker-compose up --build

# Or run locally
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8002
```

The application will be available at `http://localhost:8002`.

## Tech Stack

**Backend:**
- Django 5.1.6 with Django REST Framework 3.15.2
- OpenAI Whisper for speech-to-text transcription
- OpenAI GPT-4o-mini for summaries and chat
- JWT authentication (SimpleJWT)
- SQLite database

**Frontend:**
- React SPA

**Infrastructure:**
- Docker deployment with Gunicorn
- Self-hosted on €8.36/month Ubuntu VPS

**Core Features:**
- User registration and JWT authentication
- Audio/video file upload and management
- Automatic transcription using Whisper
- AI-generated summaries from transcripts
- Interactive Q&A chat about transcript content

## Architecture

**Data Flow:**
1. Video upload → ffmpeg processing
2. Whisper API transcription
3. Content summarization (GPT-4o-mini)
4. VoiceFlow chat interface for Q&A

**Technical Stack:**
- Django REST API (function-based views)
- SQLite database
- React frontend
- Docker + Gunicorn deployment

## What I Learned
- OpenAI API integration and prompt engineering
- Full-stack ownership (backend, frontend, infrastructure)
- Trade-offs between MVP speed and production-ready code

## What I'd Do Differently in a Team Environment
- Class-based views or ViewSets for better DRF patterns
- Migrate from SQLite to PostgreSQL for production scalability
- Create a FastAPI service layer for async processing and task queue (TranscriptionService, SummarizationService, ChatService)
- Comprehensive test coverage (pytest)
- Security hardening (rate limiting, input validation)
- CI/CD pipeline vs manual deployment
- Code review process before merging to production

## Note on Code Quality
This was built solo as a learning exercise, prioritizing experimentation over production best practices. I'm sharing it as requested to demonstrate end-to-end capability. Happy to discuss what I'd improve with proper team processes.
