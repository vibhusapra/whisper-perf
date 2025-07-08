# GPT-4o Audio Performance Testing

This project tests OpenAI's GPT-4o audio model transcription accuracy at different playback speeds (1x, 2x, 3x) to evaluate the cost-accuracy tradeoff described in [this blog post](https://george.mand.is/2025/06/openai-charges-by-the-minute-so-make-the-minutes-shorter/).

## Overview

The test suite:
- Speeds up audio files using ffmpeg (1x, 2x, 3x)
- Transcribes each version using OpenAI's GPT-4o audio model
- Calculates Word Error Rate (WER) against reference transcripts
- Analyzes cost savings and accuracy tradeoffs
- Generates comprehensive reports and visualizations

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install ffmpeg:**
   - macOS: `brew install ffmpeg`
   - Ubuntu: `sudo apt install ffmpeg`
   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

3. **Set up OpenAI API key:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

4. **Prepare your dataset:**
   - Place audio files (30-60 min each) in `data/audio/`
   - Place corresponding transcripts in `data/transcripts/`
   - Transcript files should have the same base name as audio files
   - Supported formats: `.txt` or `.json`

## Dataset Structure

```
data/
├── audio/
│   ├── podcast_ep1.mp3
│   ├── podcast_ep2.mp3
│   └── ...
└── transcripts/
    ├── podcast_ep1.txt
    ├── podcast_ep2.txt
    └── ...
```

### Transcript Formats

**Text format (.txt):**
```
This is the complete transcript of the audio file.
It should contain the exact spoken words.
```

**JSON format (.json):**
```json
{
  "text": "This is the complete transcript of the audio file."
}
```

## Usage

**Run full test suite:**
```bash
python main.py
```

**Test specific speeds:**
```bash
python main.py --speeds 1.0 2.0 3.0 4.0
```

**Skip visualizations:**
```bash
python main.py --no-viz
```

## Output

Results are saved in the `results/` directory:
- `test_results_TIMESTAMP.csv` - Detailed test data
- `test_results_TIMESTAMP.json` - JSON format results
- `test_report_TIMESTAMP.md` - Comprehensive markdown report
- `performance_analysis_TIMESTAMP.png` - Visualization plots

## Metrics

- **WER (Word Error Rate)**: Percentage of words incorrectly transcribed
- **CER (Character Error Rate)**: Percentage of characters incorrectly transcribed
- **Cost Savings**: Percentage reduction in API costs
- **Processing Time**: Time taken for transcription

## Example Report

The generated report includes:
- Summary statistics for each speed factor
- Recommendations based on WER threshold
- Detailed results for each file
- Cost-accuracy tradeoff analysis

## Notes

- Audio files are temporarily sped up using ffmpeg with the `atempo` filter
- Files larger than 25MB are rejected (API limit)
- Transcripts are normalized (lowercase, punctuation removed) for WER calculation
- Temporary files are automatically cleaned up after testing
- GPT-4o uses token-based pricing (~$100/1M input tokens, $200/1M output tokens)
- Cost is typically higher than the older Whisper API but offers more flexibility