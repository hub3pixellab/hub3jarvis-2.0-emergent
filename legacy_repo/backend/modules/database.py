from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.client = None
        self.db = None

    async def connect(self):
        mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        db_name = os.getenv("MONGO_DB", "hub3_jarvis")
        self.client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
        self.db = self.client[db_name]
        self.users = self.db["users"]
        self.conversations = self.db["conversations"]
        self.memory = self.db["memory"]
        self.whitelist = self.db["whitelist"]
        self.creative_assets = self.db["creative_assets"]
        self.learning_logs = self.db["learning_logs"]
        await self.users.create_index("email", unique=True)
        await self.whitelist.create_index("phone", unique=True)
        try:
            await self.client.admin.command("ping")
            print(f"  MongoDB: {db_name} conectado")
        except Exception as e:
            print(f"  ERRO MongoDB: {e}")
            raise

    async def disconnect(self):
        if self.client:
            self.client.close()

db_manager = DatabaseManager()
