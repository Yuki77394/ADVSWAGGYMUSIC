import random
from os import getenv
from dotenv import load_dotenv

load_dotenv()

# ─── SWAGGYMUSIC branding ────────────────────────────────────────────────────
BOT_NAME = "SWAGGYMUSIC"
TEAM_BRANDING = "Team SpicyXNetwork"
TEAM_BRANDING_URL = "https://t.me/SpicyxNetwork"

# Complete 11-image pool used for the /start welcome image (randomly picked).
# Sourced from the SWAGGYMUSIC reference repository.
START_IMAGES = [
    "https://files.catbox.moe/jf0yqq.jpg",
    "https://files.catbox.moe/7w0ec2.jpg",
    "https://files.catbox.moe/dfj1l8.jpg",
    "https://files.catbox.moe/e7pbwj.jpg",
    "https://files.catbox.moe/bta4qz.jpg",
    "https://files.catbox.moe/1a1pu2.jpg",
    "https://files.catbox.moe/xvirq4.jpg",
    "https://files.catbox.moe/8dyj3u.jpg",
    "https://files.catbox.moe/x63yfj.jpg",
    "https://files.catbox.moe/3rtw9v.jpg",
    "https://files.catbox.moe/0u6db2.jpg",
]

# Celebration / confetti message-effect ID applied to the /start welcome photo.
# Sourced from the SWAGGYMUSIC reference repository.
CELEBRATION_EFFECT_ID = 5046509860389126442


def get_start_image() -> str:
    """Pick a random image from the START_IMAGES pool."""
    return random.choice(START_IMAGES)


class Config:
    def __init__(self):
        self.API_ID = int(getenv("API_ID", 0))
        self.API_HASH = getenv("API_HASH")

        self.BOT_TOKEN = getenv("BOT_TOKEN")
        self.MONGO_URL = getenv("MONGO_URL")

        self.LOGGER_ID = int(getenv("LOGGER_ID", 0))
        self.OWNER_ID = int(getenv("OWNER_ID", 0))

        self.DURATION_LIMIT = int(getenv("DURATION_LIMIT", 99999))
        self.QUEUE_LIMIT = int(getenv("QUEUE_LIMIT", 20))
        self.PLAYLIST_LIMIT = int(getenv("PLAYLIST_LIMIT", 20))

        self.SESSION1 = getenv("SESSION", None)
        self.SESSION2 = getenv("SESSION2", None)
        self.SESSION3 = getenv("SESSION3", None)

        # SWAGGYMUSIC support/channel values (from source KURIGRAMSWAG repo).
        # Still overridable via environment variables.
        self.SUPPORT_CHANNEL = getenv("SUPPORT_CHANNEL", "https://t.me/+sTyS-zKwUIk4YWI1")
        self.SUPPORT_CHAT = getenv("SUPPORT_CHAT", "https://t.me/SpIcYxNeTwOrK")

        self.API_URL = getenv("SHRUTI_API_URL", "https://api.shrutibots.site")
        self.API_KEY = getenv("SHRUTI_API_KEY", "ShrutiBotswFO5UMhbdcYIYaFcC17Y") ## Get This API KEY FROM TELEGRAM BOT USERNAME: @SHRUTIAPIBOT

        self.AUTO_LEAVE: bool = getenv("AUTO_LEAVE", "False").lower() == "true"
        self.AUTO_END: bool = getenv("AUTO_END", "False").lower() == "true"

        self.THUMB_GEN: bool = getenv("THUMB_GEN", "True").lower() == "true"
        self.VIDEO_PLAY: bool = getenv("VIDEO_PLAY", "True").lower() == "true"

        self.LANG_CODE = getenv("LANG_CODE", "en")

        self.COOKIES_URL = [
            url for url in getenv("COOKIES_URL", "").split(" ")
            if url and "batbin.me" in url
        ]
        self.DEFAULT_THUMB = getenv("DEFAULT_THUMB", "https://graph.org/file/a0c719a648b318df230ab-b7a25ab69ad6cec4fc.jpg")
        self.PING_IMG = getenv("PING_IMG", "https://files.catbox.moe/7hr8ah.jpg")
        self.START_VIDEO = getenv("START_VIDEO", "https://d.uguu.se/RHlOgTuP.mp4")

        # SWAGGYMUSIC branding exposed to the rest of the project.
        self.BOT_NAME = BOT_NAME
        self.TEAM_BRANDING = TEAM_BRANDING
        self.TEAM_BRANDING_URL = TEAM_BRANDING_URL
        self.BOT_PHOTO_URL = "https://files.catbox.moe/wta4lx.jpg"

        # Random start-image pool + celebration effect (sourced from SWAGGYMUSIC).
        self.START_IMAGES = START_IMAGES
        self.CELEBRATION_EFFECT_ID = CELEBRATION_EFFECT_ID

    def check(self):
        missing = [
            var
            for var in ["API_ID", "API_HASH", "BOT_TOKEN", "MONGO_URL", "LOGGER_ID", "OWNER_ID", "SESSION1"]
            if not getattr(self, var)
        ]
        if missing:
            raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")
