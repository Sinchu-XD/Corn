# Telegram @Itz_Your_4Bhi
# Copyright ©️ 2025

from datetime import datetime
from Config import Config
from pymongo import MongoClient
from bson import ObjectId


db = MongoClient(Config.MONGO_URI).RichBot
sudo_col = db.sudo_users
settings_collection = db["settings"]
users_col = db.users
config_col = db["config"]

# ✅ Add user to DB
async def add_user(user_id: int, first_name: str, username: str = None):
    if not users_col.find_one({"user_id": user_id}):
        users_col.insert_one({
            "user_id": user_id,
            "first_name": first_name,
            "username": username,
            "joined_on": datetime.utcnow()
        })
        
async def add_sudo(user_id: int):
    if not sudo_col.find_one({"user_id": user_id}):
        sudo_col.insert_one({"user_id": user_id})

async def remove_sudo(user_id: int):
    sudo_col.delete_one({"user_id": user_id})

async def get_sudo_list():
    return [x["user_id"] for x in sudo_col.find().to_list(length=1000)]

# Add below existing sudo functions in helpers/db.py

channel_col = db.required_channels

async def add_channel(username: str):
    if not channel_col.find_one({"username": username}):
        channel_col.insert_one({"username": username})

async def remove_channel(username: str):
    channel_col.delete_one({"username": username})

async def get_channels():
    return [x["username"] for x in channel_col.find().to_list(length=1000)]

files_col = db.files

async def save_file(user_id: int, file_id: str, file_type: str):
    doc = {
        "user_id": user_id,
        "file_id": file_id,
        "file_type": file_type,
        "time": datetime.utcnow()
    }
    insert = files_col.insert_one(doc)
    return str(insert.inserted_id)

async def get_file_by_id(file_id: str):
    return files_col.find_one({"_id": ObjectId(file_id)})
    
async def set_force_check(value: bool):
    settings_collection.update_one({"_id": "force_check"}, {"$set": {"value": True}}, upsert=True)

async def get_force_check():
    setting = settings_collection.find_one({"_id": "force_check"})
    return setting["value"] if setting else False

async def set_main_channel(channel: str):
    await config_col.update_one(
        {"_id": "main_channel"},
        {"$set": {"value": channel}},
        upsert=True
    )

# ✅ Get Main Channel
async def get_main_channel() -> str:
    data = config_col.find_one({"_id": "main_channel"})
    return data["value"] if data else None
