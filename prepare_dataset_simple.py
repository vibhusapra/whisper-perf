#!/usr/bin/env python3
"""
Simplified dataset preparation focusing on reliable sources with verified transcripts.
"""

import os
import json
import logging
import subprocess
from pathlib import Path
import requests
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleDatasetPreparer:
    def __init__(self):
        self.data_dir = Path("data")
        self.audio_dir = self.data_dir / "audio"
        self.transcript_dir = self.data_dir / "transcripts"
        
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.transcript_dir.mkdir(parents=True, exist_ok=True)
    
    def prepare_samples(self):
        """Prepare a curated list of samples with known good transcripts."""
        
        samples_info = {
            "samples": [
                {
                    "name": "sample_1_podcast_clear",
                    "description": "Clear single speaker podcast",
                    "type": "clean",
                    "source": "Manual download required",
                    "instructions": "Download from podcast with official transcript"
                },
                {
                    "name": "sample_2_interview_multiple",
                    "description": "Interview with multiple speakers",
                    "type": "challenging",
                    "source": "Manual download required",
                    "instructions": "Download interview with transcript"
                },
                {
                    "name": "sample_3_technical_jargon",
                    "description": "Technical presentation with domain-specific terms",
                    "type": "challenging",
                    "source": "Manual download required",
                    "instructions": "Download technical talk with transcript"
                },
                {
                    "name": "sample_4_audiobook_professional",
                    "description": "Professional audiobook narration",
                    "type": "clean",
                    "source": "LibriVox",
                    "instructions": "Download from LibriVox with matching text"
                },
                {
                    "name": "sample_5_accented_english",
                    "description": "Non-native English speaker",
                    "type": "challenging",
                    "source": "Manual download required",
                    "instructions": "Download talk by non-native speaker"
                },
                {
                    "name": "sample_6_ted_talk",
                    "description": "TED talk with clear speech",
                    "type": "clean",
                    "source": "TED.com",
                    "instructions": "Download TED talk with official transcript"
                },
                {
                    "name": "sample_7_panel_discussion",
                    "description": "Panel with overlapping speech",
                    "type": "challenging",
                    "source": "Manual download required",
                    "instructions": "Download panel discussion"
                },
                {
                    "name": "sample_8_news_broadcast",
                    "description": "Professional news narration",
                    "type": "clean",
                    "source": "Manual download required",
                    "instructions": "Download news segment with transcript"
                },
                {
                    "name": "sample_9_phone_quality",
                    "description": "Phone or low quality audio",
                    "type": "challenging",
                    "source": "Manual download required",
                    "instructions": "Download phone interview"
                },
                {
                    "name": "sample_10_lecture_clean",
                    "description": "Academic lecture with good audio",
                    "type": "clean",
                    "source": "Manual download required",
                    "instructions": "Download university lecture"
                }
            ],
            "instructions": """
## Dataset Preparation Instructions

Since automatic downloading of copyrighted content with transcripts can be challenging,
here are recommended sources for obtaining test samples:

### Clean Audio Sources:
1. **TED Talks** (ted.com)
   - Download audio from YouTube using yt-dlp
   - Get official transcripts from TED website
   - Look for talks 30-60 minutes long

2. **LibriVox** (librivox.org)
   - Public domain audiobooks
   - Match with Project Gutenberg texts
   - Great for clean, professional narration

3. **NPR** (npr.org)
   - Many shows provide transcripts
   - High quality audio
   - Various speaking styles

4. **University Lectures**
   - MIT OpenCourseWare
   - Stanford Online
   - Often have transcripts or captions

5. **Podcasts with Transcripts**
   - This American Life
   - Freakonomics
   - The Daily (NY Times)

### Challenging Audio Sources:
1. **Panel Discussions**
   - Conference recordings
   - YouTube debates
   - Multiple speakers, crosstalk

2. **Non-Native Speakers**
   - International conferences
   - Academic presentations
   - Various accents

3. **Technical Content**
   - Programming tutorials
   - Medical lectures
   - Domain-specific jargon

4. **Poor Quality Audio**
   - Phone interviews
   - Outdoor recordings
   - Background noise

5. **Multiple Speakers**
   - Group discussions
   - Interviews
   - Overlapping speech

### How to Prepare Each Sample:

1. **Download Audio** (using yt-dlp):
   ```bash
   yt-dlp -x --audio-format mp3 -o "data/audio/sample_name.%(ext)s" VIDEO_URL
   ```

2. **Get Transcript**:
   - Download official transcript if available
   - Use YouTube's manual captions (not auto-generated)
   - Save as .txt file with same base name

3. **Verify Quality**:
   - Listen to audio to confirm category (clean/challenging)
   - Read transcript to ensure accuracy
   - Check audio is 30-60 minutes long

4. **Trim if Needed** (using ffmpeg):
   ```bash
   ffmpeg -i input.mp3 -ss 00:00:00 -t 00:45:00 -c copy output.mp3
   ```
            """
        }
        
        # Save instructions and sample list
        with open(self.data_dir / 'dataset_preparation_guide.json', 'w') as f:
            json.dump(samples_info, f, indent=2)
        
        # Create example transcript files
        for sample in samples_info['samples']:
            transcript_path = self.transcript_dir / f"{sample['name']}.txt"
            with open(transcript_path, 'w') as f:
                f.write(f"[Placeholder transcript for {sample['name']}]\n")
                f.write(f"Description: {sample['description']}\n")
                f.write(f"Type: {sample['type']}\n")
                f.write(f"Instructions: {sample['instructions']}\n\n")
                f.write("Replace this with the actual transcript content.")
        
        # Create a sample download script
        script_content = '''#!/bin/bash
# Sample download commands for test dataset

# Example 1: Download a TED talk
# yt-dlp -x --audio-format mp3 -o "data/audio/ted_talk_sample.%(ext)s" "https://www.youtube.com/watch?v=VIDEO_ID"

# Example 2: Download with subtitles
# yt-dlp -x --audio-format mp3 --write-sub --sub-lang en -o "data/audio/%(title)s.%(ext)s" "URL"

# Example 3: Trim audio to 45 minutes
# ffmpeg -i input.mp3 -ss 00:00:00 -t 00:45:00 -c copy output.mp3

# Example 4: Convert video to audio only
# ffmpeg -i video.mp4 -vn -acodec mp3 -ab 192k audio.mp3

echo "Add your download commands here"
'''
        
        with open('download_samples.sh', 'w') as f:
            f.write(script_content)
        
        os.chmod('download_samples.sh', 0o755)
        
        logger.info("Dataset preparation guide created!")
        logger.info(f"Instructions saved to: {self.data_dir / 'dataset_preparation_guide.json'}")
        logger.info("Placeholder transcripts created in: data/transcripts/")
        logger.info("Sample download script created: download_samples.sh")
        logger.info("\nNext steps:")
        logger.info("1. Read the preparation guide for recommended sources")
        logger.info("2. Download audio samples (30-60 min each)")
        logger.info("3. Replace placeholder transcripts with actual ones")
        logger.info("4. Run: python main.py")


def main():
    preparer = SimpleDatasetPreparer()
    preparer.prepare_samples()


if __name__ == "__main__":
    main()