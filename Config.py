# Config.py

import os

class Config:
    API_ID = int(os.getenv("API_ID", 6067591))
    API_HASH = os.getenv("API_HASH", "94e17044c2393f43fda31d3afe77b26b")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "7443259882:AAE8tgZbbhKVaYbWdfwCe6rwJt7ADSRicYM")
    MONGO_URI = os.getenv("MONGO_URL", "mongodb+srv://Sinchu:Sinchu@sinchu.qwijj.mongodb.net/?retryWrites=true&w=majority&appName=Sinchu")

    OWNER_ID = int(os.environ.get("OWNER_ID", "7862043458"))  # Your Telegram user ID
    LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", -1002362380968))
    
    BOT_USERNAME = "StreeStuffBot"
