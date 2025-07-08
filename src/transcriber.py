import os
import time
import logging
import base64
from typing import Dict, Optional, Tuple
from openai import OpenAI
from src.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GPT4OTranscriber:
    def __init__(self):
        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.GPT4O_MODEL
    
    def _encode_audio_to_base64(self, audio_path: str) -> str:
        """Encode audio file to base64 string."""
        with open(audio_path, 'rb') as audio_file:
            audio_data = audio_file.read()
            return base64.b64encode(audio_data).decode('utf-8')
    
    def transcribe(self, audio_path: str, language: Optional[str] = None) -> Tuple[str, Dict]:
        """
        Transcribe audio file using GPT-4o audio model.
        
        Args:
            audio_path: Path to audio file
            language: Optional language code (e.g., 'en')
        
        Returns:
            Tuple of (transcription_text, metadata_dict)
        """
        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        
        if file_size_mb > Config.MAX_FILE_SIZE_MB:
            raise ValueError(f"File size {file_size_mb:.2f}MB exceeds maximum of {Config.MAX_FILE_SIZE_MB}MB")
        
        logger.info(f"Transcribing {os.path.basename(audio_path)} ({file_size_mb:.2f}MB)")
        
        start_time = time.time()
        
        try:
            # Encode audio to base64
            audio_base64 = self._encode_audio_to_base64(audio_path)
            
            # Determine audio format from file extension
            audio_format = os.path.splitext(audio_path)[1].lower().replace('.', '')
            if audio_format == 'mp3':
                audio_format = 'mp3'
            elif audio_format in ['wav', 'wave']:
                audio_format = 'wav'
            elif audio_format == 'm4a':
                audio_format = 'mp4'
            else:
                audio_format = 'mp3'  # Default to mp3
            
            # Prepare the transcription prompt
            prompt = "Please transcribe this audio file accurately. Provide only the transcription without any additional commentary."
            if language:
                prompt += f" The audio is in {language}."
            
            # Call GPT-4o with audio
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": audio_base64,
                                "format": audio_format
                            }
                        }
                    ]
                }
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=16384  # Adjust based on expected transcript length
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Extract transcription from response
            transcription = response.choices[0].message.content
            
            # Calculate token usage and costs
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0
            total_tokens = response.usage.total_tokens if response.usage else 0
            
            input_cost = (input_tokens / 1_000_000) * Config.GPT4O_INPUT_COST_PER_M
            output_cost = (output_tokens / 1_000_000) * Config.GPT4O_OUTPUT_COST_PER_M
            total_cost = input_cost + output_cost
            
            metadata = {
                "processing_time": processing_time,
                "file_size_mb": file_size_mb,
                "model": self.model,
                "language": language,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "input_cost": input_cost,
                "output_cost": output_cost,
                "total_cost": total_cost
            }
            
            logger.info(f"Transcription completed in {processing_time:.2f}s")
            logger.info(f"Tokens used: {input_tokens} input, {output_tokens} output")
            logger.info(f"Cost: ${total_cost:.4f}")
            
            return transcription, metadata
            
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            raise
    
    def estimate_cost(self, audio_size_mb: float, expected_transcript_words: int = 10000) -> float:
        """
        Estimate transcription cost based on file size and expected output.
        
        Args:
            audio_size_mb: Audio file size in MB
            expected_transcript_words: Expected words in transcript
        
        Returns:
            Estimated cost in USD
        """
        # Rough estimation:
        # - Audio input tokens: ~1000-2000 tokens per MB of audio
        # - Output tokens: ~1.5 tokens per word
        
        estimated_input_tokens = audio_size_mb * 1500  # Conservative estimate
        estimated_output_tokens = expected_transcript_words * 1.5
        
        input_cost = (estimated_input_tokens / 1_000_000) * Config.GPT4O_INPUT_COST_PER_M
        output_cost = (estimated_output_tokens / 1_000_000) * Config.GPT4O_OUTPUT_COST_PER_M
        
        return input_cost + output_cost