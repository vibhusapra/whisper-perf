# Dataset Requirements

## Audio Files

Place your audio files in the `data/audio/` directory. 

**Requirements:**
- Duration: 30-60 minutes per file (recommended)
- Formats: MP3, WAV, or M4A
- Quality: Clear speech with minimal background noise
- Size: Less than 25MB per file (Whisper API limit)

**Recommended sources:**
- Podcasts with published transcripts
- TED Talks with subtitles
- Academic lectures with transcriptions
- Audiobooks with text versions

## Reference Transcripts

Place reference transcripts in the `data/transcripts/` directory.

**Requirements:**
- Must have the same base filename as the audio file
- Should be accurate, human-verified transcripts
- Format: Plain text (.txt) or JSON (.json)

**Text format example (`podcast_ep1.txt`):**
```
Welcome to today's episode. Today we'll be discussing the importance of
software testing in modern development practices. Testing is crucial for
ensuring code quality and preventing bugs from reaching production.
```

**JSON format example (`podcast_ep1.json`):**
```json
{
  "text": "Welcome to today's episode. Today we'll be discussing the importance of software testing in modern development practices. Testing is crucial for ensuring code quality and preventing bugs from reaching production.",
  "metadata": {
    "source": "Official podcast transcript",
    "date": "2024-01-15",
    "speaker": "John Doe"
  }
}
```

## Obtaining Test Data

### Option 1: YouTube Videos with Subtitles
1. Find long-form YouTube videos with accurate subtitles
2. Use yt-dlp to download audio and subtitles:
   ```bash
   yt-dlp -x --audio-format mp3 -o "data/audio/%(title)s.%(ext)s" VIDEO_URL
   yt-dlp --write-sub --sub-lang en --skip-download -o "data/transcripts/%(title)s.%(ext)s" VIDEO_URL
   ```

### Option 2: Podcasts
1. Find podcasts that provide official transcripts
2. Download the audio files
3. Copy the transcript text to a .txt file

### Option 3: LibriVox
1. Visit [LibriVox](https://librivox.org/)
2. Download public domain audiobooks
3. Get the corresponding text from [Project Gutenberg](https://www.gutenberg.org/)

## Validation

Before running tests, ensure:
1. Each audio file has a corresponding transcript
2. Audio files are in supported formats
3. File sizes are under 25MB
4. Filenames match between audio and transcript

Run validation:
```python
from src.dataset_manager import DatasetManager
dm = DatasetManager()
is_valid, issues = dm.validate_dataset()
if not is_valid:
    for issue in issues:
        print(f"Issue: {issue}")
```