import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    GPT4O_MODEL = "gpt-4o-audio-preview"
    
    SPEED_FACTORS = [1.0, 2.0, 3.0]
    
    AUDIO_SAMPLE_RATE = 16000
    AUDIO_CHANNELS = 1
    AUDIO_BITRATE = "64k"
    
    DEFAULT_LANGUAGE = "en"
    
    RESULTS_DIR = "results"
    DATA_DIR = "data"
    AUDIO_DIR = os.path.join(DATA_DIR, "audio")
    TRANSCRIPT_DIR = os.path.join(DATA_DIR, "transcripts")
    
    TEMP_DIR = "temp"
    
    MAX_FILE_SIZE_MB = 25
    
    # GPT-4o pricing (per million tokens)
    GPT4O_INPUT_COST_PER_M = 100.0  # $100 per 1M input tokens
    GPT4O_OUTPUT_COST_PER_M = 200.0  # $200 per 1M output tokens