# Django Application Analysis: unlock-videos

## Executive Summary

This document contains a comprehensive analysis of the `unlock-videos` Django application, identifying security vulnerabilities, performance bottlenecks, data model issues, and code quality improvements. This analysis serves as context for future development work.

---

## Application Overview

**Purpose:** A REST API for managing audio/video files with AI-powered transcription and chat capabilities.

**Tech Stack:**
- Django 5.1.6 with Django REST Framework 3.15.2
- OpenAI Whisper for speech-to-text transcription
- OpenAI GPT-4o-mini for summaries and chat
- JWT authentication (SimpleJWT)
- SQLite database
- Docker deployment with Gunicorn

**Core Features:**
1. User registration and JWT authentication
2. Audio/video file upload and management
3. Automatic transcription using Whisper
4. AI-generated summaries from transcripts
5. Interactive Q&A chat about transcript content

---

## Project Structure

```
unlock-videos/
├── unlock_videos/           # Main Django app
│   ├── views.py             # API endpoints (215 lines)
│   ├── models.py            # MediaFile model (60 lines)
│   ├── serializers.py       # DRF serializers (25 lines)
│   ├── urls.py              # URL routing
│   ├── utils.py             # OpenAI helper functions
│   ├── whisper_utils.py     # Whisper model loading
│   ├── admin.py             # Admin configuration
│   ├── settings.py          # Django settings
│   └── migrations/          # 10 database migrations
├── media/                   # Uploaded files
├── static/                  # Static assets
├── requirements.txt         # 109 packages
├── Dockerfile
├── docker-compose.yml
└── db.sqlite3               # SQLite database
```

---

## API Endpoints

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/api/register/` | None | User registration |
| POST | `/api/token/` | None | JWT token obtain |
| POST | `/api/token/refresh/` | JWT | Refresh access token |
| GET | `/api/files/` | JWT | List user's files |
| POST | `/api/files/` | JWT | Upload media file |
| GET | `/api/files/{id}/` | JWT | Get file details |
| PATCH | `/api/files/{id}/` | JWT | Update file metadata |
| DELETE | `/api/files/{id}/` | JWT | Delete file |
| POST | `/api/files/transcribe/{id}/` | JWT | Transcribe media |
| POST | `/api/files/summary/{id}/` | JWT | Generate summary |
| GET | `/api/files/download/{id}/` | JWT | Download file |
| GET | `/api/start/` | **None** | Start conversation thread |
| POST | `/api/chat/` | **None** | Send chat message |

---

## FINDINGS

### 1. CRITICAL SECURITY ISSUES

#### 1.1 Unauthenticated Chat Endpoints

**Location:** `unlock_videos/views.py` lines 168-215

**Problem:** The `/api/start/` and `/api/chat/` endpoints lack `@permission_classes([IsAuthenticated])`. Any unauthenticated user can:
- Start conversation threads
- Send chat messages
- Access transcript data through the shared cache

**Current Code:**
```python
@api_view(['GET'])
def start_conversation(request):  # Missing @permission_classes
    ...

@api_view(['POST'])
def chat(request):  # Missing @permission_classes
    ...
```

**Required Fix:**
```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def start_conversation(request):
    ...

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat(request):
    ...
```

---

#### 1.2 Shared Cache Key - Data Leakage Between Users

**Location:** `unlock_videos/views.py` lines 60-61 and 184-185

**Problem:** All users share the same hardcoded cache key `'7878'`. This means:
- User A's transcript is visible to User B
- Concurrent requests overwrite each other's data
- Complete lack of data isolation

**Current Code:**
```python
# In file() view (line 60-61):
unique_key = '7878'
cache.set(unique_key, data.transcript, timeout=3600)

# In chat() view (line 184-185):
unique_key = '7878'
transcript = cache.get(unique_key)
```

**Required Fix:**
```python
# Use user-specific and file-specific cache key:
unique_key = f'transcript_{request.user.id}_{file_id}'
cache.set(unique_key, data.transcript, timeout=3600)

# In chat view, require file_id and validate ownership:
file_id = request.data.get('file_id')
media_file = get_object_or_404(MediaFile, pk=file_id, user=request.user)
unique_key = f'transcript_{request.user.id}_{file_id}'
transcript = cache.get(unique_key) or media_file.transcript
```

---

#### 1.3 Hardcoded Secrets in Source Code

**Location:** `unlock_videos/views.py` line 166

**Problem:** OpenAI assistant ID is hardcoded in source code.

**Current Code:**
```python
assistant_id = 'asst_A9w4GjniGj2Q1c4SSrmEhERg'
```

**Required Fix:**
```python
from decouple import config
assistant_id = config('OPENAI_ASSISTANT_ID')
```

Add to `.env`:
```
OPENAI_ASSISTANT_ID=asst_A9w4GjniGj2Q1c4SSrmEhERg
```

---

#### 1.4 No File Upload Validation

**Location:** `unlock_videos/serializers.py` and `unlock_videos/views.py`

**Problem:** No validation for:
- Maximum file size (users can upload unlimited sizes)
- File content type verification
- Filename sanitization (path traversal risk)

**Required Fix in serializers.py:**
```python
MAX_FILE_SIZE_MB = 500
ALLOWED_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mp3', '.wav', '.aac'}

class MediaFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaFile
        fields = ['id', 'file_name', 'length', 'size', 'upload_timestamp',
                  'file', 'file_type', 'transcript', 'summary']
        read_only_fields = ['id', 'upload_timestamp', 'size', 'file_type',
                            'transcript', 'summary', 'length']

    def validate_file(self, value):
        # Size validation
        if value.size > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise serializers.ValidationError(f"File exceeds {MAX_FILE_SIZE_MB}MB limit")

        # Extension validation
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(f"Unsupported file type: {ext}")

        # Path traversal prevention
        if '..' in value.name or '/' in value.name:
            raise serializers.ValidationError("Invalid filename")

        return value
```

---

### 2. PERFORMANCE ISSUES

#### 2.1 Synchronous Heavy Processing

**Location:** `unlock_videos/views.py` lines 101-133 (transcribe) and 135-152 (summary)

**Problem:** Whisper transcription and OpenAI API calls block the request thread:
- Transcription of long files can take minutes
- Gunicorn timeout is 300 seconds but may not be enough
- No async processing or task queue

**Impact:** Server becomes unresponsive during transcription. Multiple concurrent requests will exhaust worker threads.

**Required Fix:** Implement Celery with Redis for async task processing:

1. Create `unlock_videos/tasks.py`:
```python
from celery import shared_task
from .models import MediaFile
from .whisper_utils import get_whisper_model

@shared_task(bind=True, max_retries=3)
def transcribe_media_task(self, file_id, user_id):
    media_file = MediaFile.objects.get(pk=file_id, user_id=user_id)
    whisper_model = get_whisper_model()
    result = whisper_model.transcribe(media_file.file.path)
    media_file.transcript = result['text']
    media_file.save(update_fields=['transcript'])
    return {"status": "completed", "file_id": file_id}
```

2. Update views to return task_id immediately:
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transcribe(request, file_id):
    media_file = get_object_or_404(MediaFile, pk=file_id, user=request.user)
    task = transcribe_media_task.delay(file_id, request.user.id)
    return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)
```

---

#### 2.2 Whisper Model Loaded at Import Time

**Location:** `unlock_videos/whisper_utils.py` line 7

**Problem:** The Whisper model (~3GB) is loaded when the module is imported:
```python
whisper_model = whisper.load_model('base')
```

**Impact:**
- Application startup blocked until model loads
- 3GB memory consumed even if transcription never used
- Every Gunicorn worker loads the model separately

**Required Fix - Lazy Loading:**
```python
_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = whisper.load_model('base')
    return _whisper_model
```

---

#### 2.3 No Pagination

**Location:** `unlock_videos/views.py` lines 37-51

**Problem:** The `files()` endpoint loads all user files into memory:
```python
data = request.user.media_owner.all()
serializer = MediaFileSerializer(data, many=True)
```

**Impact:** Performance degrades linearly with number of files.

**Required Fix:**
```python
from rest_framework.pagination import PageNumberPagination

class MediaFilePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def files(request):
    if request.method == 'GET':
        data = request.user.media_owner.all().order_by('-upload_timestamp')
        paginator = MediaFilePagination()
        page = paginator.paginate_queryset(data, request)
        serializer = MediaFileSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
```

---

### 3. DATA MODEL ISSUES

#### 3.1 Double save() Call in Model

**Location:** `unlock_videos/models.py` lines 28-60

**Problem:** The `save()` method calls `super().save()` twice:
```python
def save(self, *args, **kwargs):
    if self.file:
        # ... type detection ...
        super(MediaFile, self).save(*args, **kwargs)  # First save (line 39)
        if self.file:
            self.size = round(self.file.size / (1024 * 1024), 2)

    super(MediaFile, self).save(*args, **kwargs)  # Second save (line 60)
```

**Impact:**
- Doubles database writes
- Can cause race conditions
- Inefficient

**Required Fix:**
```python
def save(self, *args, **kwargs):
    if self.file:
        extension = os.path.splitext(self.file.name)[1].lower()
        if extension in ['.mp4', '.avi', '.mov']:
            self.file_type = 'video'
        elif extension in ['.mp3', '.wav', '.aac']:
            self.file_type = 'audio'
        else:
            raise ValueError(f"Unsupported file type: {extension}")

    super().save(*args, **kwargs)  # Single save

    # Update size after save (file now exists on disk)
    if self.file and not self.size:
        MediaFile.objects.filter(pk=self.pk).update(
            size=round(self.file.size / (1024 * 1024), 2)
        )
```

---

#### 3.2 Size Field Type Mismatch

**Location:** `unlock_videos/models.py` line 15

**Problem:** Size is calculated as float with 2 decimals but stored in IntegerField:
```python
size = models.IntegerField(blank=True, null=True)
# ...
self.size = round(self.file.size / (1024 * 1024), 2)  # Returns float like 12.34
```

**Impact:** Decimal precision is lost (12.34 MB stored as 12 MB).

**Required Fix:** Create migration to change field type:
```python
migrations.AlterField(
    model_name='mediafile',
    name='size',
    field=models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True),
)
```

---

#### 3.3 No File Cleanup on Delete

**Location:** `unlock_videos/models.py`

**Problem:** When a MediaFile record is deleted, the physical file remains on disk.

**Impact:** Orphaned files accumulate, consuming storage.

**Required Fix - Add signal:**
```python
from django.db.models.signals import post_delete
from django.dispatch import receiver

@receiver(post_delete, sender=MediaFile)
def delete_media_file(sender, instance, **kwargs):
    if instance.file and os.path.isfile(instance.file.path):
        os.remove(instance.file.path)
```

---

#### 3.4 Flat File Storage

**Location:** `unlock_videos/models.py` line 19

**Problem:** Files stored directly in MEDIA_ROOT without organization:
```python
file = models.FileField(null=True)  # No upload_to specified
```

**Impact:** All files in one directory, difficult to manage, no user isolation.

**Required Fix:**
```python
def media_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    safe_filename = f"{uuid.uuid4().hex}{ext}"
    now = datetime.now()
    return f"user_{instance.user_id}/{now.year}/{now.month:02d}/{safe_filename}"

file = models.FileField(upload_to=media_upload_path, null=True)
```

---

#### 3.5 Length Field Never Populated

**Location:** `unlock_videos/models.py` lines 43-57

**Problem:** The code to calculate audio/video length is commented out:
```python
# if self.file_type == 'video':
#     video = VideoFileClip(self.file.path)
#     self.length = timedelta(seconds=int(video.duration))
# elif self.file_type == 'audio':
#     audio = AudioSegment.from_file(self.file.path)
#     self.length = timedelta(milliseconds=len(audio))
```

**Impact:** The `length` DurationField is always NULL.

**Root Cause:** Comment says "doesn't work (file is not yet uploaded when save() is called)"

**Required Fix:** Calculate length in a post-save signal or Celery task after file is written.

---

### 4. CODE QUALITY ISSUES

#### 4.1 Serializer Exposes All Fields

**Location:** `unlock_videos/serializers.py` lines 5-8

**Problem:**
```python
class MediaFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaFile
        fields = '__all__'  # Exposes everything including user_id
```

**Impact:** Potentially exposes sensitive data, no control over read/write fields.

**Required Fix:** Explicit field list with read_only_fields (see section 1.4).

---

#### 4.2 No Error Handling for OpenAI API

**Location:** `unlock_videos/utils.py` and `unlock_videos/views.py`

**Problem:** OpenAI API calls have no error handling:
- Rate limits not handled
- API errors not caught
- No retry logic

**Required Fix:**
```python
from openai import OpenAIError, RateLimitError, APIError
import logging

logger = logging.getLogger(__name__)

def create_summary_from_transcript(transcript, client):
    try:
        # ... API calls ...
    except RateLimitError as e:
        logger.warning(f"Rate limit hit: {e}")
        raise Exception("Service temporarily unavailable")
    except APIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise Exception("Failed to generate summary")
```

---

#### 4.3 Minimal Logging

**Location:** `unlock_videos/settings.py` lines 200-208

**Problem:** Only WARNING level logging configured:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}
```

**Impact:** Errors and important events not tracked.

**Required Fix:** Configure proper logging with file handlers, rotation, and appropriate levels.

---

#### 4.4 No API Versioning

**Location:** `unlock_videos/urls.py`

**Problem:** API endpoints use `/api/` without version prefix.

**Impact:** Breaking changes affect all clients immediately.

**Required Fix:** Change to `/api/v1/` with backwards-compatible redirect.

---

### 5. ARCHITECTURE ISSUES

#### 5.1 Monolithic Structure

**Problem:** All code in single `unlock_videos` app with:
- Views doing too much (business logic mixed with HTTP handling)
- No service layer
- No separation of concerns

**Recommendation:** Create service layer:
```
unlock_videos/
├── services/
│   ├── __init__.py
│   ├── transcription.py    # TranscriptionService
│   ├── summarization.py    # SummarizationService
│   └── chat.py             # ChatService
```

---

#### 5.2 SQLite in Production

**Location:** `unlock_videos/settings.py` line 102

**Problem:** SQLite used for production:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

**Impact:**
- Poor concurrency (locks entire database on writes)
- Not suitable for production workloads
- Data loss risk

**Recommendation:** Migrate to PostgreSQL for production.

---

#### 5.3 No Test Coverage

**Problem:** No test files found in the project.

**Recommendation:** Add test suite:
```
unlock_videos/
├── tests/
│   ├── __init__.py
│   ├── test_views.py       # API endpoint tests
│   ├── test_models.py      # Model tests
│   ├── test_serializers.py # Validation tests
│   └── test_services.py    # Service layer tests
```

---

## IMPLEMENTATION PRIORITY

### Phase 1: Critical Security (Immediate)
1. Add `@permission_classes([IsAuthenticated])` to chat endpoints
2. Fix hardcoded cache key to use user-specific keys
3. Move assistant_id to environment variable
4. Add file upload validation

### Phase 2: Performance (High Priority)
1. Implement lazy Whisper model loading
2. Set up Celery with Redis for async processing
3. Add pagination to file listing
4. Add file cleanup on delete

### Phase 3: Data Model (Medium Priority)
1. Fix double save() in model
2. Migrate size field to DecimalField
3. Implement organized file storage paths
4. Calculate and store file length

### Phase 4: Code Quality (Lower Priority)
1. Improve serializers with explicit fields
2. Add comprehensive error handling
3. Configure proper logging
4. Add API versioning

### Phase 5: Architecture (Future)
1. Create service layer
2. Migrate to PostgreSQL
3. Add test coverage

---

## FILES REQUIRING MODIFICATION

| File | Priority | Changes Needed |
|------|----------|----------------|
| `unlock_videos/views.py` | Critical | Auth decorators, cache keys, pagination, async tasks |
| `unlock_videos/models.py` | High | Fix save(), file cleanup, upload_to, length calculation |
| `unlock_videos/serializers.py` | Critical | File validation, explicit fields |
| `unlock_videos/settings.py` | Medium | Logging config, Celery config |
| `unlock_videos/whisper_utils.py` | High | Lazy model loading |
| `unlock_videos/utils.py` | Medium | Error handling |
| `unlock_videos/urls.py` | Low | API versioning |

## NEW FILES TO CREATE

| File | Purpose |
|------|---------|
| `unlock_videos/tasks.py` | Celery async tasks |
| `unlock_videos/celery.py` | Celery app configuration |
| `unlock_videos/services/__init__.py` | Service layer |
| `unlock_videos/services/transcription.py` | Transcription service |
| `unlock_videos/tests/test_views.py` | API tests |
| `unlock_videos/tests/test_models.py` | Model tests |

---

## VERIFICATION CHECKLIST

After implementing fixes:

- [ ] Chat endpoints return 401 for unauthenticated requests
- [ ] Different users cannot see each other's transcripts
- [ ] File uploads over size limit are rejected
- [ ] Invalid file types are rejected
- [ ] Transcription returns task_id immediately (async)
- [ ] Pagination works on file listing
- [ ] Deleting MediaFile removes physical file
- [ ] Application starts without loading Whisper model
- [ ] All tests pass

---

*Generated: 2026-01-22*
*Analysis performed on Django 5.1.6 application*
