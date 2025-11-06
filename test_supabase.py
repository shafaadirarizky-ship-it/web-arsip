from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")

print("🔍 Testing connection to Supabase...")
print("URL:", SUPABASE_URL)

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    buckets = supabase.storage.list_buckets()
    print("✅ Connected to Supabase!")
    print("📦 Buckets found:")
    for b in buckets:
        print(" -", b["name"])
except Exception as e:
    print("❌ Connection failed:", e)
