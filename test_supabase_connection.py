#!/usr/bin/env python3
"""
Simple test script to verify Supabase connection
Run: python test_supabase_connection.py
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client


def test_connection():
    # Load environment variables
    load_dotenv()

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env file")
        return False

    try:
        # Create Supabase client
        supabase: Client = create_client(url, key)

        # Test connection by listing tables
        print("🔄 Testing Supabase connection...")
        print(f"📡 URL: {url}")

        # Try to query public schema
        result = supabase.rpc("version").execute()
        print("✅ Connection successful!")

        # Check if our tables exist
        tables_to_check = ["companies", "positions", "candidates"]
        for table in tables_to_check:
            try:
                result = supabase.table(table).select("*").limit(0).execute()
                print(f"✅ Table '{table}' exists and is accessible")
            except Exception as e:
                print(f"⚠️  Table '{table}' not found or not accessible: {e}")

        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    success = test_connection()
    if success:
        print("\n🎉 Supabase integration is working!")
    else:
        print("\n💡 Next steps:")
        print("1. Update .env file with correct SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
        print("2. Run the SQL schema in Supabase Dashboard SQL Editor")
        print("3. Re-run this test")
