# SWAGGYMUSIC

Telegram Music Player Bot built with Python, Pyrogram/Kurigram and Py-TGCALLS.

Powered by **Team SpicyXNetwork**.

## 🚀 One-Click Heroku Hosting

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/Yuki77394/ADVSWAGGYMUSIC)

### Required variables

Heroku will ask for these automatically during deployment:

- `API_ID` — Telegram API ID from https://my.telegram.org/apps
- `API_HASH` — Telegram API hash
- `BOT_TOKEN` — Bot token from @BotFather
- `MONGO_URL` — MongoDB connection URI
- `LOGGER_ID` — Telegram log group ID
- `OWNER_ID` — Owner Telegram user ID
- `SESSION` — Pyrogram string session for the assistant/userbot

### Optional variables

You can add these later in **Heroku → Settings → Config Vars**:

`SESSION2`, `SESSION3`, `DURATION_LIMIT`, `QUEUE_LIMIT`, `PLAYLIST_LIMIT`, `SUPPORT_CHANNEL`, `SUPPORT_CHAT`, `SHRUTI_API_URL`, `SHRUTI_API_KEY`, `AUTO_LEAVE`, `AUTO_END`, `THUMB_GEN`, `VIDEO_PLAY`, `LANG_CODE`, `COOKIES_URL`, `DEFAULT_THUMB`, `PING_IMG`, `START_VIDEO`.

> **Note on `SHRUTI_API_KEY`:** This must be provided through the environment (Heroku Config Var). There is **no hardcoded fallback** in the repository — if it is not set, the ShrutiBots fallback downloader will simply be unavailable, but the bot will still run normally using the primary YouTube extractor.

## Local development

1. Copy `.env.example` to `.env` and fill in your credentials.
2. Install dependencies: `pip install -r requirements.txt`
3. Make sure `ffmpeg` and `deno` are installed and available on your `PATH`.
4. Start the bot: `python3 -m SWAGGYMUSIC`

> `.env` is gitignored — never commit a real `.env` file. Use `.env.example` as the template.

## Manual Heroku deployment

1. Fork this repository.
2. Open the **Deploy to Heroku** button above.
3. Enter the required variables.
4. Click **Deploy app**.
5. After deployment, make sure the `worker` dyno is enabled.

> The project uses Heroku's container stack through `heroku.yml` and `Dockerfile`.
