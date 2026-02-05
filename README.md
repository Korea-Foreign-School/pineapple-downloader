# 🍍 Pineapple Downloader

A Python script that automatically downloads files from Slack channels and organizes them by month.

## Features

- 📥 Downloads all files from specified Slack channels
- 📁 Organizes files by year-month folders (e.g., `2024-01`, `2024-02`)
- 🔄 Detects and skips duplicate files using MD5 hashing
- ⚡ Parallel downloads (10 workers) for faster processing
- 📊 Sends summary to Slack automation channel when complete

## Prerequisites

- Python 3.9 or higher
- A Slack Bot Token with the following permissions:
  - `files:read` - to list and download files
  - `chat:write` - to send summary messages (optional)

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Korea-Foreign-School/pineapple-downloader.git
cd pineapple-downloader
```

### 2. Create a virtual environment (recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create your `.env` file

Create a file named `.env` in the project root with the following content:

```env
SLACK_TOKEN=your-slack-bot-token-here
PINEAPPLE_CHANNEL_ID=your-channel-id-here
FIELD_TRIP_CHANNEL_ID=your-field-trip-channel-id
AUTOMATIONS_CHANNEL_ID=your-automations-channel-id
PINEAPPLE_DOWNLOAD_FOLDER=/path/to/your/downloads/folder
FIELD_TRIP_DOWNLOAD_FOLDER=/path/to/your/field-trip/folder
```

**Getting your Slack Bot Token:**
1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Select your app (or create a new one)
3. Go to "OAuth & Permissions"
4. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

**Getting Channel IDs:**
1. Open Slack in your browser
2. Navigate to the channel
3. The channel ID is in the URL: `slack.com/app_redirect?channel=C014REXMRMW`

### 5. Create download folders

The script will create these automatically, but you can create them manually:

```bash
mkdir -p downloads
mkdir -p field-trip
```

## Usage

### Run the script

```bash
python pineapple.py
```

Or if using virtual environment:

```bash
source .venv/bin/activate
python pineapple.py
```

### What happens when you run it:

1. 🔍 Builds a hash index of all existing files (to detect duplicates)
2. 📡 Fetches the list of files from the Slack channel
3. ⬇️ Downloads new files in parallel (skips duplicates)
4. 📁 Organizes files into month folders (e.g., `downloads/2024-01/`)
5. 📤 Sends a summary message to the automations channel

### Output example:

```
============================================================
📂 Building hash index from: /Users/you/Desktop/pineapple/downloads
✅ Hash index built: 45 existing files indexed
============================================================
🔍 Fetching file list from Slack...
✅ Found 120 files in Slack channel
============================================================
⚡ Starting parallel downloads (10 workers)...

⬇️  Downloading: photo1.jpg
   📅 Date: 2024-01-15
   🌐 Fetching from Slack...
   📦 Size: 245678 bytes
   🔑 Hash: a3f5b2c1...
   ✅ Saved to: 2024-01/photo1.jpg

⬇️  Downloading: photo2.jpg
   📅 Date: 2024-01-15
   🌐 Fetching from Slack...
   📦 Size: 189234 bytes
   🔑 Hash: d7e9f4a2...
   ⏭️  Duplicate skipped (exists at: downloads/2024-01/photo2.jpg)

============================================================
📊 DOWNLOAD COMPLETE
============================================================
✅ Downloaded 75 photos (15-01-24 to 05-02-26)

📤 Sending summary to Slack channel...
✅ Slack message sent
============================================================
🏁 Script finished
============================================================
```

## File Organization

Files are organized in the following structure:

```
downloads/
├── 2024-01/
│   ├── photo1.jpg
│   ├── photo2.png
│   └── document1.pdf
├── 2024-02/
│   ├── photo3.jpg
│   └── photo4.png
└── unknown_date/
    └── file_without_timestamp.jpg
```

## Troubleshooting

### "No module named 'dotenv'"

Install the required package:
```bash
pip install python-dotenv
```

### "Error fetching files: invalid_auth"

Your Slack token is invalid or expired. Get a new token from your Slack app settings.

### "Slack message skipped: Token needs 'chat:write' scope"

Your bot token doesn't have permission to send messages. To fix:
1. Go to your Slack App settings → OAuth & Permissions
2. Add the `chat:write` scope
3. Reinstall the app to your workspace

### Files downloading to wrong location

Check that your `.env` file has the correct absolute paths for `PINEAPPLE_DOWNLOAD_FOLDER`.

## Security Notes

⚠️ **IMPORTANT:** Never commit your `.env` file to Git!

The `.env` file contains sensitive credentials. Make sure `.gitignore` includes:
```
.env
```

If you accidentally committed secrets to Git, you should:
1. Regenerate your Slack bot token
2. Remove the commits from history
3. Force push the clean history

## Contributing

Feel free to open issues or submit pull requests!

## License

MIT License