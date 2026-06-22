import os

from motor.motor_asyncio import AsyncIOMotorClient

# `app/__init__.py` has already loaded the .env file by the time this imports.
mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]
