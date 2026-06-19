# config.py
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7752488661

PLATEGA_MERCHANT_ID = os.getenv("PLATEGA_MERCHANT_ID")
PLATEGA_SECRET = os.getenv("PLATEGA_SECRET")
PLATEGA_API_URL = os.getenv("PLATEGA_API_URL", "https://app.platega.io")

CRYPTOBOT_TOKEN = os.getenv("CRYPTOBOT_TOKEN")
CRYPTOBOT_API_URL = os.getenv("CRYPTOBOT_API_URL", "https://pay.cryptobot.com/api")