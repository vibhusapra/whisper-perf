#!/usr/bin/env python3
"""
Download LibriVox audiobook samples with matching Project Gutenberg texts.
These are public domain and perfect for testing.
"""

import os
import json
import logging
import requests
from pathlib import Path
from tqdm import tqdm
import re
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LibriVoxDownloader:
    def __init__(self):
        self.data_dir = Path("data")
        self.audio_dir = self.data_dir / "audio"
        self.transcript_dir = self.data_dir / "transcripts"
        
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.transcript_dir.mkdir(parents=True, exist_ok=True)
        
        # Curated LibriVox samples with good audio quality
        self.samples = [
            {
                "name": "pride_prejudice_clean",
                "librivox_url": "https://www.archive.org/download/pride_and_prejudice_0801_librivox/prideandprejudice_01_austen_64kb.mp3",
                "gutenberg_url": "https://www.gutenberg.org/files/1342/1342-0.txt",
                "description": "Pride and Prejudice - Chapter 1 (Clean narration)",
                "type": "clean",
                "chapter": 1,
                "duration": "~30 min"
            },
            {
                "name": "sherlock_holmes_clean",
                "librivox_url": "https://www.archive.org/download/adventures_holmes_rg_librivox/adventuresholmes_01_doyle_64kb.mp3",
                "gutenberg_url": "https://www.gutenberg.org/files/1661/1661-0.txt",
                "description": "Adventures of Sherlock Holmes - A Scandal in Bohemia",
                "type": "clean",
                "duration": "~35 min"
            },
            {
                "name": "war_of_worlds_dramatic",
                "librivox_url": "https://www.archive.org/download/war_worlds_0711_librivox/waroftheworlds_01_wells_64kb.mp3",
                "gutenberg_url": "https://www.gutenberg.org/files/36/36-0.txt",
                "description": "War of the Worlds - Chapter 1 (Dramatic reading)",
                "type": "clean",
                "duration": "~30 min"
            },
            {
                "name": "moby_dick_classic",
                "librivox_url": "https://www.archive.org/download/moby_dick_librivox/mobydick_001_melville_64kb.mp3",
                "gutenberg_url": "https://www.gutenberg.org/files/2701/2701-0.txt",
                "description": "Moby Dick - Chapter 1 (Classic narration)",
                "type": "clean",
                "duration": "~40 min"
            },
            {
                "name": "frankenstein_atmospheric",
                "librivox_url": "https://www.archive.org/download/frankenstein_0810_librivox/frankenstein_01_shelley_64kb.mp3",
                "gutenberg_url": "https://www.gutenberg.org/files/84/84-0.txt",
                "description": "Frankenstein - Opening chapters",
                "type": "clean",
                "duration": "~35 min"
            }
        ]
    
    def download_file(self, url: str, output_path: Path, description: str) -> bool:
        """Download a file with progress bar."""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(output_path, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc=description) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        pbar.update(len(chunk))
            
            return True
        except Exception as e:
            logger.error(f"Error downloading {url}: {str(e)}")
            return False
    
    def extract_chapter_text(self, full_text: str, chapter_num: int, title: str) -> str:
        """Extract specific chapter from Gutenberg text."""
        # Clean up Gutenberg header/footer
        start_markers = ["*** START OF", "***START OF", "*** START OF THE PROJECT"]
        end_markers = ["*** END OF", "***END OF", "End of the Project"]
        
        for marker in start_markers:
            if marker in full_text:
                full_text = full_text.split(marker, 1)[1]
                break
        
        for marker in end_markers:
            if marker in full_text:
                full_text = full_text.split(marker, 1)[0]
                break
        
        # Try to extract just the first chapter
        # This is approximate - in practice you'd align with the audio
        chapter_patterns = [
            f"Chapter {chapter_num}",
            f"CHAPTER {chapter_num}",
            f"Chapter {self.to_roman(chapter_num)}",
            f"CHAPTER {self.to_roman(chapter_num)}"
        ]
        
        for pattern in chapter_patterns:
            if pattern in full_text:
                # Get text from this chapter to the next
                parts = full_text.split(pattern, 1)
                if len(parts) > 1:
                    chapter_text = parts[1]
                    # Try to find where next chapter starts
                    next_chapter = chapter_num + 1
                    for next_pattern in [f"Chapter {next_chapter}", f"CHAPTER {next_chapter}"]:
                        if next_pattern in chapter_text:
                            chapter_text = chapter_text.split(next_pattern)[0]
                            break
                    return f"{pattern}\n\n{chapter_text[:50000]}"  # Limit length
        
        # If no chapter found, return beginning of text
        return full_text[:50000]
    
    def to_roman(self, num: int) -> str:
        """Convert number to Roman numeral."""
        values = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        symbols = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
        result = ""
        for i, value in enumerate(values):
            count, num = divmod(num, value)
            result += symbols[i] * count
        return result
    
    def download_samples(self):
        """Download all LibriVox samples."""
        logger.info("Downloading LibriVox samples with transcripts...")
        
        successful = 0
        
        for sample in self.samples:
            logger.info(f"\nProcessing: {sample['name']}")
            logger.info(f"Description: {sample['description']}")
            
            # Download audio
            audio_path = self.audio_dir / f"{sample['name']}.mp3"
            if self.download_file(sample['librivox_url'], audio_path, "Audio"):
                logger.info(f"✓ Downloaded audio: {audio_path.name}")
                
                # Download text
                temp_text_path = self.transcript_dir / f"{sample['name']}_full.txt"
                if self.download_file(sample['gutenberg_url'], temp_text_path, "Text"):
                    # Extract relevant chapter
                    with open(temp_text_path, 'r', encoding='utf-8', errors='ignore') as f:
                        full_text = f.read()
                    
                    chapter_text = self.extract_chapter_text(
                        full_text, 
                        sample.get('chapter', 1),
                        sample['name']
                    )
                    
                    # Save extracted chapter
                    transcript_path = self.transcript_dir / f"{sample['name']}.txt"
                    with open(transcript_path, 'w', encoding='utf-8') as f:
                        f.write(chapter_text)
                    
                    # Remove full text
                    temp_text_path.unlink()
                    
                    logger.info(f"✓ Saved transcript: {transcript_path.name}")
                    successful += 1
        
        # Now let's add some samples that simulate challenging audio
        logger.info("\n\nCreating simulated challenging samples...")
        
        # Create speed-altered versions of clean samples
        challenging_samples = [
            {
                "source": "pride_prejudice_clean",
                "name": "pride_prejudice_fast_speech",
                "speed": 1.3,
                "description": "Fast speech (1.3x speed)"
            },
            {
                "source": "sherlock_holmes_clean",
                "name": "sherlock_holmes_slow_speech",
                "speed": 0.8,
                "description": "Slow speech (0.8x speed)"
            }
        ]
        
        for sample in challenging_samples:
            source_audio = self.audio_dir / f"{sample['source']}.mp3"
            if source_audio.exists():
                output_audio = self.audio_dir / f"{sample['name']}.mp3"
                
                # Use ffmpeg to alter speed
                cmd = [
                    'ffmpeg', '-i', str(source_audio),
                    '-filter:a', f"atempo={sample['speed']}",
                    '-y', str(output_audio)
                ]
                
                try:
                    subprocess.run(cmd, check=True, capture_output=True)
                    logger.info(f"✓ Created {sample['description']}: {sample['name']}.mp3")
                    
                    # Copy transcript
                    source_transcript = self.transcript_dir / f"{sample['source']}.txt"
                    if source_transcript.exists():
                        dest_transcript = self.transcript_dir / f"{sample['name']}.txt"
                        dest_transcript.write_text(source_transcript.read_text())
                    
                    successful += 1
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to create {sample['name']}: {e}")
        
        # Create metadata file
        metadata = {
            "dataset_name": "LibriVox Public Domain Audiobooks",
            "total_samples": len(self.samples) + len(challenging_samples),
            "successful_downloads": successful,
            "samples": {
                "clean": [s['name'] for s in self.samples],
                "challenging": [s['name'] for s in challenging_samples]
            },
            "notes": "Transcripts are extracted from Project Gutenberg texts. "
                    "Some alignment with audio may be needed."
        }
        
        with open(self.data_dir / 'librivox_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"\n✓ Successfully prepared {successful} samples")
        logger.info(f"Audio files in: {self.audio_dir}")
        logger.info(f"Transcripts in: {self.transcript_dir}")
        logger.info("\nNote: LibriVox narrations may not match text exactly.")
        logger.info("Consider these as baseline samples for testing.")


def main():
    # Check if ffmpeg is installed
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("ffmpeg is required but not found. Please install ffmpeg.")
        return
    
    downloader = LibriVoxDownloader()
    downloader.download_samples()


if __name__ == "__main__":
    main()