#!/usr/bin/env python3
"""
Download YouTube samples with verified manual captions for testing.
Focuses on videos with professional, human-created captions.
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path
import yt_dlp
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeDatasetDownloader:
    def __init__(self):
        self.data_dir = Path("data")
        self.audio_dir = self.data_dir / "audio"
        self.transcript_dir = self.data_dir / "transcripts"
        
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.transcript_dir.mkdir(parents=True, exist_ok=True)
        
        # Curated list of YouTube videos with professional captions
        self.samples = {
            "clean": [
                {
                    "name": "mit_algorithm_lecture",
                    "url": "https://www.youtube.com/watch?v=HtSuA80QTyo",
                    "description": "MIT Algorithms Lecture - Clear academic speech",
                    "start": "00:00:00",
                    "duration": "00:45:00"
                },
                {
                    "name": "google_io_keynote",
                    "url": "https://www.youtube.com/watch?v=lBYyAQ99ZFI",
                    "description": "Google I/O Keynote - Professional presentation",
                    "start": "00:05:00",
                    "duration": "00:40:00"
                },
                {
                    "name": "harvard_cs50_lecture",
                    "url": "https://www.youtube.com/watch?v=8mAITcNt710",
                    "description": "Harvard CS50 - Clear educational content",
                    "start": "00:00:00",
                    "duration": "00:45:00"
                },
                {
                    "name": "tedx_clear_speaker",
                    "url": "https://www.youtube.com/watch?v=Unzc731iCUY",
                    "description": "TEDx Talk - Professional speaking",
                    "start": "00:00:00",
                    "duration": "00:35:00"
                },
                {
                    "name": "stanford_lecture_clean",
                    "url": "https://www.youtube.com/watch?v=NP9AIUT9nos",
                    "description": "Stanford Lecture - Academic presentation",
                    "start": "00:00:00",
                    "duration": "00:40:00"
                }
            ],
            "challenging": [
                {
                    "name": "tech_panel_discussion",
                    "url": "https://www.youtube.com/watch?v=nc0RhqeRezU",
                    "description": "Tech Panel - Multiple speakers, crosstalk",
                    "start": "00:02:00",
                    "duration": "00:35:00"
                },
                {
                    "name": "conference_q_and_a",
                    "url": "https://www.youtube.com/watch?v=cdZZpaB2kDM",
                    "description": "Conference Q&A - Audience questions, varied audio",
                    "start": "00:45:00",
                    "duration": "00:30:00"
                },
                {
                    "name": "international_conference",
                    "url": "https://www.youtube.com/watch?v=7xzfnRRi4VA",
                    "description": "International Speaker - Non-native accent",
                    "start": "00:00:00",
                    "duration": "00:35:00"
                },
                {
                    "name": "workshop_with_demos",
                    "url": "https://www.youtube.com/watch?v=MnrJzXM7a6o",
                    "description": "Workshop - Background noise, movement",
                    "start": "00:05:00",
                    "duration": "00:40:00"
                },
                {
                    "name": "debate_multiple_speakers",
                    "url": "https://www.youtube.com/watch?v=QuR969uMICM",
                    "description": "Debate - Fast speech, interruptions",
                    "start": "00:10:00",
                    "duration": "00:35:00"
                }
            ]
        }
    
    def check_manual_captions(self, url: str) -> bool:
        """Check if video has manual (not auto-generated) captions."""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Check for manual subtitles
                if 'subtitles' in info and 'en' in info['subtitles']:
                    # Manual subtitles are in 'subtitles'
                    # Auto-generated are in 'automatic_captions'
                    return True
                    
                return False
                
        except Exception as e:
            logger.error(f"Error checking captions: {str(e)}")
            return False
    
    def download_sample(self, sample: dict, category: str) -> bool:
        """Download a single sample with audio and captions."""
        try:
            logger.info(f"\nDownloading: {sample['name']}")
            logger.info(f"Description: {sample['description']}")
            
            # First check if manual captions exist
            if not self.check_manual_captions(sample['url']):
                logger.warning(f"⚠️  No manual captions found for {sample['name']}")
                logger.warning("   This video may only have auto-generated captions")
            
            # Download audio with specific time range
            audio_output = str(self.audio_dir / f"{sample['name']}.mp3")
            
            # Build ffmpeg command for trimming
            ss_param = ['-ss', sample['start']] if sample['start'] != "00:00:00" else []
            t_param = ['-t', sample['duration']]
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': str(self.audio_dir / f"{sample['name']}_temp.%(ext)s"),
                'quiet': True,
                'no_warnings': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'external_downloader': 'ffmpeg',
                'external_downloader_args': {
                    'ffmpeg_i': ss_param,
                    'ffmpeg': t_param
                }
            }
            
            # Download audio
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([sample['url']])
            
            # Download captions
            caption_opts = {
                'writesubtitles': True,
                'writeautomaticsub': False,  # Only manual subs
                'subtitleslangs': ['en'],
                'skip_download': True,
                'outtmpl': str(self.transcript_dir / f"{sample['name']}_temp.%(ext)s"),
                'quiet': True,
            }
            
            with yt_dlp.YoutubeDL(caption_opts) as ydl:
                info = ydl.extract_info(sample['url'], download=True)
            
            # Convert VTT to plain text
            vtt_files = list(self.transcript_dir.glob(f"{sample['name']}_temp*.vtt"))
            if vtt_files:
                self.convert_vtt_to_text(vtt_files[0], sample['start'], sample['duration'])
                # Clean up temp files
                for vtt in vtt_files:
                    vtt.unlink()
            else:
                logger.warning(f"No caption file found for {sample['name']}")
            
            # Rename temp audio file
            temp_audio = self.audio_dir / f"{sample['name']}_temp.mp3"
            if temp_audio.exists():
                temp_audio.rename(audio_output)
            
            logger.info(f"✓ Successfully downloaded: {sample['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading {sample['name']}: {str(e)}")
            return False
    
    def convert_vtt_to_text(self, vtt_path: Path, start_time: str, duration: str):
        """Convert VTT captions to plain text, extracting only the specified time range."""
        try:
            with open(vtt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse start time and duration
            def time_to_seconds(time_str):
                parts = time_str.split(':')
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
            
            start_sec = time_to_seconds(start_time)
            duration_sec = time_to_seconds(duration)
            end_sec = start_sec + duration_sec
            
            # Extract captions within time range
            lines = content.split('\n')
            transcript_lines = []
            current_time = 0
            in_time_range = False
            
            for i, line in enumerate(lines):
                if '-->' in line:
                    # Parse timestamp
                    time_match = re.match(r'(\d{2}:\d{2}:\d{2}\.\d{3})', line)
                    if time_match:
                        current_time = time_to_seconds(time_match.group(1).replace('.', ':'))
                        in_time_range = start_sec <= current_time <= end_sec
                elif in_time_range and line.strip() and not line.startswith('WEBVTT'):
                    # Clean and add caption text
                    clean_line = re.sub(r'<.*?>', '', line)  # Remove HTML tags
                    clean_line = re.sub(r'\[.*?\]', '', clean_line)  # Remove speaker labels
                    if clean_line.strip():
                        transcript_lines.append(clean_line.strip())
            
            # Join and clean transcript
            transcript = ' '.join(transcript_lines)
            transcript = re.sub(r'\s+', ' ', transcript)
            
            # Save transcript
            output_path = self.transcript_dir / f"{vtt_path.stem.replace('_temp', '')}.txt"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(transcript.strip())
                
        except Exception as e:
            logger.error(f"Error converting VTT: {str(e)}")
    
    def download_all_samples(self):
        """Download all configured samples."""
        logger.info("Starting YouTube dataset download...")
        logger.info("This will download samples with professional captions.\n")
        
        successful = 0
        total = len(self.samples['clean']) + len(self.samples['challenging'])
        
        # Download clean samples
        logger.info("=== Downloading Clean Audio Samples ===")
        for sample in self.samples['clean']:
            if self.download_sample(sample, 'clean'):
                successful += 1
        
        # Download challenging samples
        logger.info("\n=== Downloading Challenging Audio Samples ===")
        for sample in self.samples['challenging']:
            if self.download_sample(sample, 'challenging'):
                successful += 1
        
        # Create metadata
        metadata = {
            "dataset": "YouTube Samples with Professional Captions",
            "total_samples": total,
            "successful": successful,
            "categories": {
                "clean": [s['name'] for s in self.samples['clean']],
                "challenging": [s['name'] for s in self.samples['challenging']]
            },
            "notes": "All samples trimmed to 30-45 minutes with manual captions"
        }
        
        with open(self.data_dir / 'youtube_dataset_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"\n✓ Successfully downloaded {successful}/{total} samples")
        logger.info(f"Audio files: {self.audio_dir}")
        logger.info(f"Transcripts: {self.transcript_dir}")
        
        if successful < total:
            logger.warning("\n⚠️  Some downloads failed. Check error messages above.")
            logger.warning("You may need to find alternative sources for those samples.")


def main():
    # Check dependencies
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("ffmpeg is required. Please install: brew install ffmpeg")
        sys.exit(1)
    
    downloader = YouTubeDatasetDownloader()
    downloader.download_all_samples()


if __name__ == "__main__":
    main()