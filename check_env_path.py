"""Check which .env file is being used"""
import os
from dotenv import load_dotenv

print("=" * 60)
print("Checking .env file location")
print("=" * 60)

# Get current directory
current_dir = os.getcwd()
print(f"\n1. Current working directory:")
print(f"   {current_dir}")

# Check for .env in current directory
env_path = os.path.join(current_dir, '.env')
print(f"\n2. .env file path (default):")
print(f"   {env_path}")
print(f"   Exists: {os.path.exists(env_path)}")

# Check the user's specified path
user_path = r"C:\Users\storage\OneDrive - O'Brien's Demolition\Desktop\Chat assistant\.env"
print(f"\n3. User specified path:")
print(f"   {user_path}")
print(f"   Exists: {os.path.exists(user_path)}")

# Try loading from current directory
print(f"\n4. Loading .env from current directory...")
result1 = load_dotenv()
print(f"   Result: {result1}")
token1 = os.getenv("STORMAN_API_TOKEN")
print(f"   STORMAN_API_TOKEN found: {'YES' if token1 else 'NO'}")

# Try loading from explicit path
print(f"\n5. Loading .env from explicit path...")
result2 = load_dotenv(user_path)
print(f"   Result: {result2}")
token2 = os.getenv("STORMAN_API_TOKEN")
print(f"   STORMAN_API_TOKEN found: {'YES' if token2 else 'NO'}")

# Check what's actually in the .env file
if os.path.exists(env_path):
    print(f"\n6. Contents of .env file (first 10 lines):")
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()[:10]
            for i, line in enumerate(lines, 1):
                # Don't show full token, just first few chars
                if 'TOKEN' in line or 'KEY' in line:
                    parts = line.split('=')
                    if len(parts) == 2:
                        print(f"   Line {i}: {parts[0]}={parts[1][:20]}...")
                    else:
                        print(f"   Line {i}: {line.strip()}")
                else:
                    print(f"   Line {i}: {line.strip()}")
    except Exception as e:
        print(f"   Error reading file: {e}")

print("\n" + "=" * 60)

