import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from src.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatasetManager:
    def __init__(self):
        self.audio_dir = Config.AUDIO_DIR
        self.transcript_dir = Config.TRANSCRIPT_DIR
        self._validate_directories()
    
    def _validate_directories(self):
        """Ensure required directories exist."""
        os.makedirs(self.audio_dir, exist_ok=True)
        os.makedirs(self.transcript_dir, exist_ok=True)
    
    def get_dataset_items(self) -> List[Dict[str, str]]:
        """
        Get all dataset items with their audio and transcript paths.
        
        Returns:
            List of dictionaries with 'name', 'audio_path', and 'transcript_path'
        """
        items = []
        
        audio_files = list(Path(self.audio_dir).glob("*.mp3")) + \
                     list(Path(self.audio_dir).glob("*.wav")) + \
                     list(Path(self.audio_dir).glob("*.m4a"))
        
        for audio_path in audio_files:
            base_name = audio_path.stem
            
            transcript_txt = Path(self.transcript_dir) / f"{base_name}.txt"
            transcript_json = Path(self.transcript_dir) / f"{base_name}.json"
            
            transcript_path = None
            if transcript_txt.exists():
                transcript_path = str(transcript_txt)
            elif transcript_json.exists():
                transcript_path = str(transcript_json)
            
            if transcript_path:
                items.append({
                    'name': base_name,
                    'audio_path': str(audio_path),
                    'transcript_path': transcript_path
                })
            else:
                logger.warning(f"No transcript found for {audio_path.name}")
        
        logger.info(f"Found {len(items)} complete dataset items")
        return items
    
    def load_transcript(self, transcript_path: str) -> str:
        """
        Load transcript from file (supports .txt and .json formats).
        
        Args:
            transcript_path: Path to transcript file
        
        Returns:
            Transcript text
        """
        path = Path(transcript_path)
        
        if path.suffix == '.txt':
            with open(path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        
        elif path.suffix == '.json':
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, str):
                    return data
                elif isinstance(data, dict):
                    return data.get('text', data.get('transcript', ''))
                else:
                    raise ValueError(f"Unexpected JSON format in {transcript_path}")
        
        else:
            raise ValueError(f"Unsupported transcript format: {path.suffix}")
    
    def save_dataset_metadata(self, metadata: Dict):
        """Save dataset metadata to JSON file."""
        metadata_path = os.path.join(Config.DATA_DIR, 'dataset_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved metadata to {metadata_path}")
    
    def validate_dataset(self) -> Tuple[bool, List[str]]:
        """
        Validate dataset completeness and return any issues.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        items = self.get_dataset_items()
        
        if len(items) == 0:
            issues.append("No dataset items found")
            return False, issues
        
        for item in items:
            audio_path = Path(item['audio_path'])
            if not audio_path.exists():
                issues.append(f"Audio file missing: {audio_path}")
            
            try:
                transcript = self.load_transcript(item['transcript_path'])
                if len(transcript.strip()) == 0:
                    issues.append(f"Empty transcript: {item['transcript_path']}")
            except Exception as e:
                issues.append(f"Error loading transcript {item['transcript_path']}: {str(e)}")
        
        is_valid = len(issues) == 0
        return is_valid, issues