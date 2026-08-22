# Chowdeck Voucher Agent

🚨 **Automated monitoring agent for Chowdeck voucher codes on X (Twitter)**

A production-ready, cloud-deployable Python application that monitors the public X account `@lordbinary_` for Chowdeck voucher/promotional codes and sends instant Telegram notifications.

## Features

✅ **X API Monitoring**
- Official X API v2 integration (no scraping)
- Monitors only `@lordbinary_` (configurable username)
- Respects rate limits and authentication
- Recent tweets polling

✅ **Intelligent Voucher Detection**
- Smart extraction module that identifies likely voucher codes
- Filters out URLs, handles, hashtags, and common words
- Configurable patterns for different voucher formats
- Comprehensive unit tests

✅ **Database Deduplication**
- SQLite for local state tracking
- Prevents duplicate tweet processing
- Prevents duplicate voucher notifications
- Complete audit trail

✅ **Scheduled Monitoring**
- Timezone-aware scheduling (e.g., only 6 PM - 11 PM Lagos time)
- Configurable polling intervals
- Efficient sleep during non-monitoring hours
- Never runs 24/7 unless configured

✅ **Telegram Notifications**
- Immediate alerts with voucher codes
- Tweet text and URL included
- Detection timestamp
- Secure token handling (never logged)

✅ **Playwright Browser Automation**
- Persistent browser profile for Chowdeck
- Manual login on first run (no password storage)
- OTP verification support
- Session caching and reuse

✅ **Cloud Ready**
- GitHub Actions scheduled workflow
- Docker & docker-compose support
- Environment variable configuration
- Clean startup/shutdown

✅ **Security**
- No credentials in source code
- `.gitignore` for sensitive files
- `.env.example` template
- GitHub Secrets integration
- HTTPS-only communication

✅ **Testing**
- Comprehensive test suite
- Voucher extraction tests
- Database deduplication tests
- Scheduler/timezone tests
- Mock mode (no external API calls)

---

## Project Structure

```
chowdeck-voucher-agent/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Application entry point
│   ├── config.py                  # Environment configuration
│   ├── x_monitor.py               # X API integration
│   ├── voucher_extractor.py       # Smart voucher detection
│   ├── database.py                # SQLite operations
│   ├── notifications.py           # Telegram notifications
│   ├── scheduler.py               # Time window scheduling
│   └── chowdeck.py                # Playwright browser automation
├── tests/
│   ├── conftest.py                # Pytest configuration
│   ├── test_extractor.py          # Voucher extraction tests
│   ├── test_database.py           # Database operation tests
│   └── test_scheduler.py          # Scheduling logic tests
├── monitor.yml                    # GitHub Actions workflow
├── .gitignore
├── .env.example                   # Configuration template
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Container image
├── docker-compose.yml             # Local development setup
└── README.md                      # This file
```

---

## Environment Variables

### Required

```bash
# X API
X_BEARER_TOKEN=your_x_bearer_token_here
X_USERNAME=lordbinary_                    # Default value, configurable

# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
```

### Optional (with defaults)

```bash
# Scheduler Configuration
MONITOR_TIMEZONE=Africa/Lagos             # Default timezone
MONITOR_START=18:00                       # Start monitoring at 6 PM
MONITOR_END=23:00                         # Stop monitoring at 11 PM
MONITOR_INTERVAL_SECONDS=60               # Poll every 60 seconds

# Application Configuration
APP_MODE=production                       # production or test
LOG_LEVEL=INFO                            # DEBUG, INFO, WARNING, ERROR
DATABASE_PATH=chowdeck_monitor.db         # SQLite database location

# Playwright/Chowdeck Configuration
CHOWDECK_BROWSER_HEADLESS=false           # false = visible browser for auth
CHOWDECK_PROFILE_PATH=./browser_profiles/chowdeck
CHOWDECK_TIMEOUT_MS=30000                 # 30 second timeout

# Voucher Extraction Configuration
VOUCHER_MIN_LENGTH=3                      # Minimum code length
VOUCHER_MAX_LENGTH=20                     # Maximum code length
VOUCHER_PATTERN=^[A-Z0-9]+$               # Regex for valid codes
```

Create a `.env` file in the project root:

```bash
cp .env.example .env
# Edit .env and add your actual tokens
```

**Never commit `.env` to Git.**

---

## Setup & Installation

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/bussycooks/chowdeck-voucher-agent.git
   cd chowdeck-voucher-agent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file**
   ```bash
   cp .env.example .env
   # Edit .env and add your credentials
   ```

5. **Run tests**
   ```bash
   pytest tests/ -v
   ```

6. **Run the application**
   ```bash
   python -m app.main
   ```

### Docker

1. **Build the image**
   ```bash
   docker build -t chowdeck-voucher-agent .
   ```

2. **Run with docker-compose**
   ```bash
   docker-compose up
   ```

3. **Run one-time with Docker**
   ```bash
   docker run --rm -it \
     -e X_BEARER_TOKEN="your_token" \
     -e TELEGRAM_BOT_TOKEN="your_token" \
     -e TELEGRAM_CHAT_ID="your_chat_id" \
     -v $(pwd)/browser_profiles:/app/browser_profiles \
     -v $(pwd)/chowdeck_monitor.db:/app/chowdeck_monitor.db \
     chowdeck-voucher-agent
   ```

---

## Running Tests

### All tests

```bash
pytest tests/ -v
```

### With coverage report

```bash
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

### Specific test file

```bash
pytest tests/test_extractor.py -v
pytest tests/test_database.py -v
pytest tests/test_scheduler.py -v
```

---

## Monitoring Hours Configuration

The agent monitors during a configurable time window. Outside this window, it sleeps and does not make X API requests.

### Example: Lagos time 6 PM - 11 PM

```bash
MONITOR_TIMEZONE=Africa/Lagos
MONITOR_START=18:00
MONITOR_END=23:00
MONITOR_INTERVAL_SECONDS=60
```

### Example: US Eastern time 8 PM - midnight

```bash
MONITOR_TIMEZONE=America/New_York
MONITOR_START=20:00
MONITOR_END=00:00
MONITOR_INTERVAL_SECONDS=30
```

### Example: Across midnight (10 PM - 2 AM)

```bash
MONITOR_TIMEZONE=UTC
MONITOR_START=22:00
MONITOR_END=02:00  # Next day
MONITOR_INTERVAL_SECONDS=60
```

---

## GitHub Actions Setup

### 1. Add Repository Secrets

Go to **Settings → Secrets and variables → Actions → New repository secret**

Add these secrets:

| Secret Name | Value |
|---|---|
| `X_BEARER_TOKEN` | Your X API Bearer token |
| `X_USERNAME` | `lordbinary_` (or target username) |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID |
| `MONITOR_TIMEZONE` | `Africa/Lagos` (or your timezone) |
| `MONITOR_START` | `18:00` |
| `MONITOR_END` | `23:00` |
| `MONITOR_INTERVAL_SECONDS` | `60` |

### 2. Enable the Workflow

The workflow file is at `monitor.yml`

- Runs automatically on a schedule (hourly during monitoring hours)
- Can be triggered manually via "Actions" tab
- Each run has a 10-minute timeout (prevents hanging)
- Cleans up resources after completion

---

## Manual Chowdeck Login (First Time Setup)

The application requires authenticated access to Chowdeck. This is a one-time setup.

### When to Authenticate

The first time you run the application, it will:
1. Check if an authenticated session exists
2. If not, open a visible browser window
3. Prompt you to manually log in to Chowdeck
4. Save your session in `./browser_profiles/chowdeck/auth.json`

### How to Authenticate

1. **Run locally with Playwright visible:**
   ```bash
   CHOWDECK_BROWSER_HEADLESS=false python -m app.main
   ```

2. **Browser will open automatically**
   - Chowdeck login page appears
   - Click "Sign In"

3. **Enter your credentials**
   - Email/phone
   - Password
   - **Do NOT save these anywhere** — they're only for this session

4. **Complete OTP verification**
   - Chowdeck will send a one-time code
   - Enter it in the browser
   - **Do NOT save the OTP** — it's temporary

5. **Browser closes automatically**
   - Session is saved to `browser_profiles/chowdeck/auth.json`
   - Future runs will reuse this session

### If Session Expires

If authentication fails:

1. **Delete the saved session:**
   ```bash
   rm -rf browser_profiles/chowdeck/auth.json
   ```

2. **Re-run the application locally:**
   ```bash
   CHOWDECK_BROWSER_HEADLESS=false python -m app.main
   ```

3. **Complete the login flow again**

---

## Voucher Extraction

The `VoucherExtractor` identifies likely voucher codes using configurable patterns.

### How It Works

1. **Removes URLs** - Excludes links
2. **Filters by length** - Default 3-20 characters
3. **Requires mixed case or uppercase** - Avoids common words
4. **Prefers alphanumeric mix** - Letters + numbers = likely code
5. **Deduplicates** - Returns unique codes

### Example

```python
from app.voucher_extractor import VoucherExtractor

extractor = VoucherExtractor(
    min_length=3,
    max_length=20,
    pattern=r"^[A-Z0-9]+$",
)

text = "Use code CHOW50 for 50% off at https://chowdeck.com"
vouchers = extractor.extract(text)
print(vouchers)  # ['CHOW50']
```

### Updating Patterns

Once you learn the exact voucher format from `@lordbinary_`, update the pattern:

```python
# Example: Only uppercase letters + numbers, exactly 8 characters
extractor.update_pattern(
    pattern=r"^[A-Z0-9]{8}$",
    min_length=8,
    max_length=8,
)
```

---

## Database Schema

### processed_tweets

| Column | Type | Description |
|---|---|---|
| id | INTEGER PRIMARY KEY | |
| tweet_id | TEXT UNIQUE | X tweet ID |
| tweet_text | TEXT | Full tweet content |
| tweet_url | TEXT | Link to tweet |
| author | TEXT | Tweet author |
| discovered_at | TIMESTAMP | When discovered |
| processed_at | TIMESTAMP | When added to DB |
| status | TEXT | pending / voucher_found / no_voucher / error |

### vouchers

| Column | Type | Description |
|---|---|---|
| id | INTEGER PRIMARY KEY | |
| code | TEXT UNIQUE | Voucher code |
| tweet_id | TEXT FK | Source tweet |
| discovered_at | TIMESTAMP | When found |
| created_at | TIMESTAMP | Record creation time |
| notification_sent | BOOLEAN | Was notification sent |
| notification_sent_at | TIMESTAMP | When notification sent |
| redeemed | BOOLEAN | Was voucher used |
| redeemed_at | TIMESTAMP | When redeemed |

### notifications

| Column | Type | Description |
|---|---|---|
| id | INTEGER PRIMARY KEY | |
| voucher_code | TEXT FK | Associated voucher |
| telegram_message_id | TEXT | Telegram message ID |
| status | TEXT | pending / sent / failed |
| sent_at | TIMESTAMP | When sent |
| error_message | TEXT | Error details if failed |
| created_at | TIMESTAMP | Record creation time |

---

## Security Considerations

### Never Committed to Git

- `.env` file with credentials
- `browser_profiles/` with browser sessions
- `*.db` database files
- Authentication state files

### Token Handling

- X Bearer token loaded from environment only
- Telegram bot token never logged
- Chat ID never exposed in logs
- No credentials in config files

### Browser Automation

- Passwords never stored
- OTPs never stored
- Sessions saved securely in `browser_profiles/`
- Manual login required for authentication
- No credential submission automation

### External APIs

- Official X API v2 only (no scraping)
- Respects rate limits
- HTTPS-only communication
- Proper authentication headers
- Error handling and logging

---

## Troubleshooting

### "Missing required configuration"

**Problem:** Error on startup about missing X_BEARER_TOKEN or other secrets

**Solution:**
```bash
cp .env.example .env
# Edit .env with your actual tokens
```

### "Could not find user ID for @lordbinary_"

**Problem:** X API call fails

**Causes:**
- Invalid Bearer token
- Username typo
- X API rate limit reached

**Solution:**
```bash
# Test your token
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.twitter.com/2/users/by/username/lordbinary_"
```

### "Failed to send Telegram notification"

**Problem:** Telegram API error

**Causes:**
- Invalid bot token
- Invalid chat ID
- Network connectivity issue

**Solution:**
```bash
# Test your credentials
curl -X POST https://api.telegram.org/bot<BOT_TOKEN>/sendMessage \
  -d '{"chat_id": "<CHAT_ID>", "text": "Test"}'
```

### "Chowdeck browser session expired"

**Problem:** Authentication failed

**Solution:**
```bash
# Delete the saved session
rm -rf browser_profiles/chowdeck/auth.json

# Re-run locally with visible browser
CHOWDECK_BROWSER_HEADLESS=false python -m app.main

# Complete authentication again
```

### Tests fail with "ModuleNotFoundError"

**Problem:** Dependencies not installed

**Solution:**
```bash
pip install -r requirements.txt
pytest tests/ -v
```

---

## Next Steps

1. **Get X API credentials**
   - Create app at https://developer.twitter.com
   - Generate Bearer token
   - Add to `.env`

2. **Get Telegram credentials**
   - Create bot with @BotFather
   - Get bot token and chat ID
   - Add to `.env`

3. **Run locally**
   ```bash
   python -m app.main
   ```

4. **Run tests**
   ```bash
   pytest tests/ -v
   ```

5. **Set up GitHub Actions**
   - Add repository secrets
   - Workflow will run automatically

6. **Manual Chowdeck login** (if needed)
   ```bash
   CHOWDECK_BROWSER_HEADLESS=false python -m app.main
   ```

---

## License

MIT License

## Support

For issues or questions:
1. Check this README
2. Review test files for examples
3. Check GitHub Issues
4. Open a new issue with details

---

**Ready to monitor for Chowdeck vouchers! 🎉**
