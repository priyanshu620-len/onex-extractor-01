import os
from os import getenv



# -----------------------------------------------

# --- Telegram API Credentials ---
API_ID = int(os.environ.get("API_ID", "30574823"))
API_HASH = os.environ.get("API_HASH", "2815bb996f64421716844acaf2d51493")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8802388796:AAEueYIXHBUxUKpD4hOx-5ed9e1JAqXq4BA")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "@OnexExtractorGbot")
BOT_TEXT = "Extractor Bot"
ADMIN_BOT_USERNAME = os.environ.get("ADMIN_BOT_USERNAME", "OnexExtractorGbot")

# --- User & Channel IDs ---
OWNER_ID = int(os.environ.get("OWNER_ID", "8549673687"))
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1004476834501"))       # Log Channel
CHANNEL_ID2 = int(os.environ.get("CHANNEL_ID2", "-1004476834501"))     # Force Sub Channel
PREMIUM_LOGS = int(os.environ.get("PREMIUM_LOGS", "-1004476834501"))

# --- Database (Fixed) ---
MONGO_URL = os.environ.get(
    "MONGO_URL", 
    "mongodb+srv://ONeX_db_user:onexvartikuu142062@cluster0.ga3zort.mongodb.net/?appName=Cluster0"
)

# --- External APIs & Assets ---
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "RabDRmuXXBobanmwwbvpP5LwoG4J8ox34y5Sstz-9jk")
UNSPLASH_QUERY = os.environ.get("UNSPLASH_QUERY", "animal baby")
THUMB_URL = os.environ.get("THUMB_URL", "https://i.ibb.co/DPCmWSKV/1000003297-3.jpg")
join = '<a href="https://t.me/ITSGOLU0">✳️ Bᴀᴄᴋᴜᴘ</a>'


# # Bot configuration
# API_ID = int(os.environ.get("API_ID", "22746239"))
# API_HASH = os.environ.get("API_HASH", "a98ec8cfd8572a3a7c936cf828fe6215")
# BOT_TOKEN = os.environ.get("BOT_TOKEN", "7547829346:AAGyfvOu47EciNhC7NUGSDEDFuBaetYYusw")
# BOT_USERNAME = os.environ.get("BOT_USERNAME", "MassRPBot")
# OWNER_ID = int(os.environ.get("OWNER_ID", "7463601722"))
# SUDO_USERS = list(map(int, getenv("SUDO_USERS", "7463601722").split()))
# CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1002601604234"))
# MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://wadiro6523:08AwfhhKRdQaS1i6@cluster0.krzxuop.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
# PREMIUM_LOGS = int(os.environ.get("PREMIUM_LOGS", "-1002601604234"))
# THUMB_URL = os.environ.get("THUMB_URL", "https://i.fbcd.co/products/original/ug-circle-logo-design-2-e84695ca2ab9a697d2b2d7c928b0bf5f12bf18e076da241815e0372c8d617915.jpg")
