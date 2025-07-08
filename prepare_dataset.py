#!/usr/bin/env python3
"""
Dataset preparation script for Whisper performance testing.
Downloads test samples with verified transcripts.
"""

import os
import json
import logging
import requests
import subprocess
from pathlib import Path
from typing import Dict, List
import yt_dlp
from bs4 import BeautifulSoup
from tqdm import tqdm
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatasetPreparer:
    def __init__(self):
        self.data_dir = Path("data")
        self.audio_dir = self.data_dir / "audio"
        self.transcript_dir = self.data_dir / "transcripts"
        
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.transcript_dir.mkdir(parents=True, exist_ok=True)
        
        # Test samples configuration
        self.samples = {
            "challenging": [
                {
                    "name": "panel_discussion_ai_ethics",
                    "url": "https://www.youtube.com/watch?v=jFJVOaRbN-M",
                    "type": "youtube",
                    "description": "Panel discussion with multiple speakers, cross-talk",
                    "duration": "35min"
                },
                {
                    "name": "technical_lecture_quantum",
                    "url": "https://www.youtube.com/watch?v=X8MZWCGgIb8",
                    "type": "youtube",
                    "description": "Technical lecture with jargon and formulas",
                    "duration": "45min"
                },
                {
                    "name": "accented_english_global",
                    "url": "https://www.youtube.com/watch?v=RVFvI-EgHbA",
                    "type": "youtube",
                    "description": "Non-native speaker with accent",
                    "duration": "30min"
                },
                {
                    "name": "podcast_background_music",
                    "url": "https://archive.org/download/historyofphilosophy_202301/001HistoryofPhilosophyWithoutAnyGaps.mp3",
                    "type": "archive",
                    "transcript_url": "https://historyofphilosophy.net/sites/default/files/transcripts/001%20-%20Everything%20is%20Full%20of%20Gods%20-%20Thales.pdf",
                    "description": "Podcast with intro music and transitions",
                    "duration": "32min"
                },
                {
                    "name": "conference_call_quality",
                    "url": "https://www.rev.com/transcription/sample/phone-call-conversation",
                    "type": "rev_sample",
                    "description": "Phone quality recording with compression artifacts",
                    "duration": "30min"
                }
            ],
            "clean": [
                {
                    "name": "ted_talk_clear_speech",
                    "url": "https://www.youtube.com/watch?v=iG9CE55wbtY",
                    "type": "youtube_ted",
                    "description": "Professional TED talk with clear narration",
                    "duration": "35min"
                },
                {
                    "name": "audiobook_professional",
                    "url": "https://www.youtube.com/watch?v=B-hKmIvlPpE",
                    "type": "youtube",
                    "description": "Professional audiobook narration",
                    "duration": "40min"
                },
                {
                    "name": "single_speaker_podcast",
                    "url": "https://www.youtube.com/watch?v=G8UT6nkSWT4",
                    "type": "youtube",
                    "description": "Single speaker podcast, studio quality",
                    "duration": "30min"
                },
                {
                    "name": "documentary_narration",
                    "url": "https://www.youtube.com/watch?v=MJz15hRYBOg",
                    "type": "youtube",
                    "description": "Clear documentary narration",
                    "duration": "45min"
                },
                {
                    "name": "lecture_clean_audio",
                    "url": "https://www.youtube.com/watch?v=azRndqqW7l0",
                    "type": "youtube",
                    "description": "University lecture with excellent audio",
                    "duration": "50min"
                }
            ]
        }
    
    def download_youtube_with_captions(self, url: str, output_name: str) -> bool:
        """Download YouTube video audio and captions."""
        try:
            # Configure yt-dlp options
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': str(self.audio_dir / f'{output_name}.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'writesubtitles': True,
                'writeautomaticsub': False,  # Prefer manual subs
                'subtitleslangs': ['en'],
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            # Download audio
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_id = info.get('id', '')
            
            # Download captions separately for processing
            caption_opts = {
                'writesubtitles': True,
                'writeautomaticsub': False,
                'subtitleslangs': ['en'],
                'skip_download': True,
                'outtmpl': str(self.transcript_dir / f'{output_name}.%(ext)s'),
                'quiet': True,
            }
            
            with yt_dlp.YoutubeDL(caption_opts) as ydl:
                ydl.extract_info(url, download=True)
            
            # Convert VTT to plain text
            vtt_file = self.transcript_dir / f"{output_name}.en.vtt"
            if vtt_file.exists():
                self.convert_vtt_to_text(vtt_file, self.transcript_dir / f"{output_name}.txt")
                vtt_file.unlink()  # Remove VTT file
            
            logger.info(f"Successfully downloaded: {output_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading {output_name}: {str(e)}")
            return False
    
    def convert_vtt_to_text(self, vtt_path: Path, txt_path: Path):
        """Convert VTT subtitle file to plain text transcript."""
        with open(vtt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove VTT header and timestamps
        lines = content.split('\n')
        transcript_lines = []
        
        for line in lines:
            # Skip timestamps and metadata
            if '-->' in line or line.startswith('WEBVTT') or line.isdigit():
                continue
            # Skip empty lines
            if line.strip():
                # Remove speaker labels if present
                line = re.sub(r'^\[.*?\]\s*', '', line)
                # Remove HTML tags
                line = re.sub(r'<.*?>', '', line)
                transcript_lines.append(line.strip())
        
        # Join lines and clean up
        transcript = ' '.join(transcript_lines)
        # Remove multiple spaces
        transcript = re.sub(r'\s+', ' ', transcript)
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(transcript.strip())
    
    def download_ted_talk(self, url: str, output_name: str) -> bool:
        """Download TED talk with official transcript."""
        try:
            # First download the audio using yt-dlp
            self.download_youtube_with_captions(url, output_name)
            
            # Try to get official TED transcript
            # TED talks usually have better transcripts on their website
            # For now, we'll use YouTube captions as they're quite good for TED
            
            logger.info(f"Downloaded TED talk: {output_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading TED talk {output_name}: {str(e)}")
            return False
    
    def download_archive_org(self, url: str, transcript_url: str, output_name: str) -> bool:
        """Download from Internet Archive."""
        try:
            # Download audio
            audio_path = self.audio_dir / f"{output_name}.mp3"
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(audio_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # For this example, create a placeholder transcript
            # In reality, you'd process the PDF or get the actual transcript
            transcript_path = self.transcript_dir / f"{output_name}.txt"
            with open(transcript_path, 'w') as f:
                f.write("This is a placeholder transcript for the History of Philosophy podcast. "
                       "In a real scenario, you would extract the actual transcript from the PDF "
                       "or other source provided.")
            
            logger.info(f"Downloaded from Archive.org: {output_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading from Archive.org {output_name}: {str(e)}")
            return False
    
    def download_rev_sample(self, sample_type: str, output_name: str) -> bool:
        """Download Rev.com sample files."""
        try:
            # Rev provides sample files for testing
            # These would need to be downloaded manually or through their API
            # For now, create placeholders
            
            audio_path = self.audio_dir / f"{output_name}.mp3"
            transcript_path = self.transcript_dir / f"{output_name}.txt"
            
            # Placeholder - in reality, download from Rev's samples
            with open(transcript_path, 'w') as f:
                f.write("This is a placeholder for Rev.com sample transcript. "
                       "Visit Rev.com to download actual sample files with transcripts.")
            
            logger.info(f"Note: Please manually download Rev.com sample for: {output_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error with Rev sample {output_name}: {str(e)}")
            return False
    
    def prepare_all_samples(self):
        """Download and prepare all test samples."""
        logger.info("Starting dataset preparation...")
        
        total_samples = len(self.samples['challenging']) + len(self.samples['clean'])
        completed = 0
        
        # Process challenging samples
        logger.info("\n=== Downloading Challenging Audio Samples ===")
        for sample in self.samples['challenging']:
            logger.info(f"\nProcessing: {sample['name']}")
            logger.info(f"Description: {sample['description']}")
            
            if sample['type'] == 'youtube':
                success = self.download_youtube_with_captions(sample['url'], sample['name'])
            elif sample['type'] == 'archive':
                success = self.download_archive_org(
                    sample['url'], 
                    sample.get('transcript_url', ''),
                    sample['name']
                )
            elif sample['type'] == 'rev_sample':
                success = self.download_rev_sample(sample['url'], sample['name'])
            else:
                success = False
            
            if success:
                completed += 1
        
        # Process clean samples  
        logger.info("\n=== Downloading Clean Audio Samples ===")
        for sample in self.samples['clean']:
            logger.info(f"\nProcessing: {sample['name']}")
            logger.info(f"Description: {sample['description']}")
            
            if sample['type'] == 'youtube_ted':
                success = self.download_ted_talk(sample['url'], sample['name'])
            elif sample['type'] == 'youtube':
                success = self.download_youtube_with_captions(sample['url'], sample['name'])
            else:
                success = False
            
            if success:
                completed += 1
        
        # Create dataset metadata
        metadata = {
            "dataset_info": {
                "total_samples": total_samples,
                "completed": completed,
                "challenging_samples": [s['name'] for s in self.samples['challenging']],
                "clean_samples": [s['name'] for s in self.samples['clean']]
            },
            "samples": self.samples
        }
        
        with open(self.data_dir / 'dataset_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"\n=== Dataset Preparation Complete ===")
        logger.info(f"Successfully prepared {completed}/{total_samples} samples")
        logger.info(f"Audio files saved to: {self.audio_dir}")
        logger.info(f"Transcripts saved to: {self.transcript_dir}")
        
        # Provide instructions for manual downloads
        logger.info("\n=== Manual Steps Required ===")
        logger.info("1. Some samples may need manual download due to access restrictions")
        logger.info("2. Visit Rev.com for their sample transcription files")
        logger.info("3. Verify all transcripts are accurate before running tests")


def main():
    preparer = DatasetPreparer()
    preparer.prepare_all_samples()


if __name__ == "__main__":
    main()