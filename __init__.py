# ava_gen/__init__.py

from dotenv import load_dotenv

# Load .env file at module import time
# This makes OPENAI_API_KEY and others available everywhere
load_dotenv()