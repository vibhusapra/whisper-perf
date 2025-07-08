# Quick Start Guide

## Fastest Way to Test

### 1. Install Dependencies
```bash
pip install -r requirements.txt
brew install ffmpeg  # macOS
# or: sudo apt install ffmpeg  # Linux
```

### 2. Set Up API Key
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 3. Download Test Samples

**Option A: LibriVox Samples (Recommended for quick testing)**
```bash
python download_librivox_samples.py
```
This downloads 5 public domain audiobook samples with transcripts.

**Option B: Custom Samples**
Use the guide in `prepare_dataset_simple.py` to download your own samples.

### 4. Run Tests
```bash
python main.py
```

## Expected Output

After running, you'll find in the `results/` directory:
- **test_results_*.csv** - Detailed metrics for each test
- **test_report_*.md** - Human-readable report with recommendations
- **performance_analysis_*.png** - Visualization charts

## Sample Results Preview

The report will show:
- WER (Word Error Rate) at 1x, 2x, and 3x speeds
- Cost savings percentages
- Processing times
- Recommended speed based on accuracy/cost tradeoff

## Tips

1. **Start Small**: Test with 1-2 files first to verify setup
2. **Check Transcripts**: Ensure transcripts match audio before running
3. **Monitor Costs**: Each 30-min file costs ~$0.18 at 1x speed
4. **Speed Testing**: Start with 1x and 2x before trying 3x

## Troubleshooting

- **No audio files found**: Check files are in `data/audio/`
- **No transcripts found**: Ensure matching filenames in `data/transcripts/`
- **API errors**: Verify your OpenAI API key in `.env`
- **FFmpeg errors**: Ensure ffmpeg is installed and in PATH