import os
import requests
import hashlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

SLACK_TOKEN = os.getenv("SLACK_TOKEN")
PINEAPPLE_CHANNEL_ID = os.getenv("PINEAPPLE_CHANNEL_ID")
FIELD_TRIP_CHANNEL_ID = os.getenv("FIELD_TRIP_CHANNEL_ID")
AUTOMATIONS_CHANNEL_ID = os.getenv("AUTOMATIONS_CHANNEL_ID")
PINEAPPLE_DOWNLOAD_FOLDER = os.getenv("PINEAPPLE_DOWNLOAD_FOLDER")
FIELD_TRIP_DOWNLOAD_FOLDER = os.getenv("FIELD_TRIP_DOWNLOAD_FOLDER")

print(f"🔧 Creating base folder: {PINEAPPLE_DOWNLOAD_FOLDER}")
os.makedirs(PINEAPPLE_DOWNLOAD_FOLDER, exist_ok=True)

# Thread lock for hash_index access
hash_lock = Lock()

def build_hash_index(base_folder):
    """Build index of all existing file hashes"""
    print(f"\n📂 Building hash index from: {base_folder}")
    hash_index = {}
    file_count = 0
    
    for root, dirs, files in os.walk(base_folder):
        for file in files:
            filepath = os.path.join(root, file)
            try:
                with open(filepath, "rb") as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                    hash_index[file_hash] = filepath
                    file_count += 1
            except Exception as e:
                print(f"⚠️  Error hashing {file}: {e}")
                continue
    
    print(f"✅ Hash index built: {file_count} existing files indexed")
    return hash_index

def download_file(file_data, headers, hash_index):
    """Download single file"""
    file_url = file_data.get("url_private")
    file_name = file_data.get("name", "unnamed_file")
    file_id = file_data.get("id")
    
    print(f"⬇️  Downloading: {file_name}")
    
    timestamp = file_data.get("timestamp") or file_data.get("created")
    if timestamp:
        file_date = datetime.fromtimestamp(int(timestamp))
        month_folder = file_date.strftime("%Y-%m")
        print(f"   📅 Date: {file_date.strftime('%Y-%m-%d')}")
    else:
        month_folder = "unknown_date"
        file_date = None
        print(f"   ⚠️  No timestamp found")
    
    month_path = os.path.join(PINEAPPLE_DOWNLOAD_FOLDER, month_folder)
    os.makedirs(month_path, exist_ok=True)
    
    # Download file
    print(f"   🌐 Fetching from Slack...")
    file_resp = requests.get(file_url, headers=headers)
    if file_resp.status_code != 200:
        print(f"   ❌ Download failed: HTTP {file_resp.status_code}")
        return None
    
    content = file_resp.content
    print(f"   📦 Size: {len(content)} bytes")
    
    content_hash = hashlib.md5(content).hexdigest()
    print(f"   🔑 Hash: {content_hash[:8]}...")
    
    # Thread-safe duplicate check and insertion
    with hash_lock:
        if content_hash in hash_index:
            existing_path = hash_index[content_hash]
            print(f"   ⏭️  Duplicate skipped (exists at: {existing_path})")
            return None
        
        # Reserve this hash immediately to prevent other threads from downloading
        hash_index[content_hash] = "downloading..."
    
    # Handle filename conflicts
    filepath = os.path.join(month_path, file_name)
    base_name, extension = os.path.splitext(file_name)
    counter = 1
    while os.path.exists(filepath):
        filepath = os.path.join(month_path, f"{base_name}_{counter}{extension}")
        counter += 1
    
    if counter > 1:
        print(f"   📝 Filename conflict resolved: {os.path.basename(filepath)}")
    
    with open(filepath, "wb") as f:
        f.write(content)
    
    # Update hash index with actual filepath
    with hash_lock:
        hash_index[content_hash] = filepath
    
    print(f"   ✅ Saved to: {month_folder}/{os.path.basename(filepath)}")
    return file_date

# Build hash index once
print("\n" + "="*60)
hash_index = build_hash_index(PINEAPPLE_DOWNLOAD_FOLDER)

# List files
print("\n" + "="*60)
print("🔍 Fetching file list from Slack...")
url = "https://slack.com/api/files.list"
params = {"channel": PINEAPPLE_CHANNEL_ID, "count": 1000}
headers = {"Authorization": f"Bearer {SLACK_TOKEN}"}

response = requests.get(url, headers=headers, params=params).json()

if response.get("ok"):
    files = response.get("files", [])
    print(f"✅ Found {len(files)} files in Slack channel")
    
    dates = []
    
    print("\n" + "="*60)
    print("⚡ Starting parallel downloads (10 workers)...\n")
    
    # Download files in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(download_file, file, headers, hash_index) for file in files]
        for future in as_completed(futures):
            result = future.result()
            if result:
                dates.append(result)
    
    print("\n" + "="*60)
    print("📊 DOWNLOAD COMPLETE")
    print("="*60)
    
    # Send simple summary
    if dates:
        dates.sort()
        msg = f"Downloaded {len(dates)} photos ({dates[0].strftime('%d-%m-%y')} to {dates[-1].strftime('%d-%m-%y')})"
        print(f"✅ {msg}")
    else:
        msg = "No new photos to download"
        print(f"ℹ️  {msg}")
    
    print(f"\n📤 Sending summary to Slack channel...")
    try:
        slack_response = requests.post("https://slack.com/api/chat.postMessage", 
                      headers=headers, 
                      json={"channel": AUTOMATIONS_CHANNEL_ID, "text": msg})
        
        response_data = slack_response.json()
        if response_data.get("ok"):
            print(f"✅ Slack message sent")
        else:
            error = response_data.get('error')
            if error == 'missing_scope':
                print(f"⚠️  Slack message skipped: Token needs 'chat:write' scope")
                print(f"   To fix: Go to Slack App settings → OAuth & Permissions → Add 'chat:write' scope → Reinstall app")
            else:
                print(f"❌ Slack message failed: {error}")
    except Exception as e:
        print(f"❌ Error sending Slack message: {e}")
        
else:
    print(f"❌ Error fetching files: {response.get('error')}")

print("\n" + "="*60)
print("🏁 Script finished")
print("="*60)