import os
import ffmpeg
from pathlib import Path
import logging
from typing import Optional, Tuple
from src.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioProcessor:
    def __init__(self):
        self.temp_dir = Config.TEMP_DIR
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def process_audio(self, input_path: str, speed_factor: float = 1.0) -> str:
        """
        Process audio file with specified speed factor.
        
        Args:
            input_path: Path to input audio file
            speed_factor: Speed multiplication factor (1.0 = normal, 2.0 = 2x speed)
        
        Returns:
            Path to processed audio file
        """
        input_path = Path(input_path)
        
        output_filename = f"{input_path.stem}_speed_{speed_factor}x.mp3"
        output_path = os.path.join(self.temp_dir, output_filename)
        
        logger.info(f"Processing {input_path.name} at {speed_factor}x speed")
        
        try:
            stream = ffmpeg.input(str(input_path))
            
            if speed_factor != 1.0:
                stream = ffmpeg.filter(stream, 'atempo', speed_factor)
            
            stream = ffmpeg.output(
                stream,
                output_path,
                acodec='libmp3lame',
                audio_bitrate=Config.AUDIO_BITRATE,
                ac=Config.AUDIO_CHANNELS,
                ar=Config.AUDIO_SAMPLE_RATE
            )
            
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            logger.info(f"Successfully processed audio to: {output_path}")
            return output_path
            
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error: {e.stderr.decode()}")
            raise
        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            raise
    
    def get_audio_info(self, audio_path: str) -> Tuple[float, int]:
        """
        Get audio duration and file size.
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Tuple of (duration_seconds, file_size_bytes)
        """
        try:
            probe = ffmpeg.probe(audio_path)
            duration = float(probe['format']['duration'])
            size = int(probe['format']['size'])
            return duration, size
        except Exception as e:
            logger.error(f"Error getting audio info: {str(e)}")
            raise
    
    def cleanup_temp_files(self):
        """Remove all temporary files."""
        temp_path = Path(self.temp_dir)
        if temp_path.exists():
            for file in temp_path.glob("*"):
                try:
                    file.unlink()
                except Exception as e:
                    logger.warning(f"Could not delete {file}: {e}")