"""
Thumbnail generator for SWAGGYMUSIC.

This implementation is adapted from the REFERENCE repository
(KURIGRAMSWAG-main / SWAGGYMUSIC/utils/thumbnails.py) so that the
actual generated song thumbnail matches the reference design:

  - 1280x720 canvas
  - blurred full-screen cover art as background
  - centered frosted-glass panel (763x545, rounded corners r=50)
  - inner cover art (542x273, rounded corners r=20) pasted on the panel
  - title (font2.ttf, 32px) and "YouTube | <views>" meta (font.ttf, 18px)
  - red/gray progress bar with elapsed "00:00" and duration end label
  - play_icons.png strip pasted at the bottom of the panel
  - cached at cache/<videoid>_v4.png

The TARGET's runtime caller (SWAGGYMUSIC/core/calls.py) invokes:

    _thumb = await thumb.generate(media, user_avatar=None)

so this module preserves the ``Thumbnail`` class with the same
``generate(media, output_path=None, user_avatar=None) -> str`` entrypoint
signature, while internally using the reference's 1280x720 design.

The ``user_avatar`` parameter is accepted for backward-compatibility with
the existing caller but is not used by the reference design (the reference
panel does not include a user avatar).
"""

import asyncio
import os
import re
import uuid

import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from SWAGGYMUSIC import config


# ─── Reference layout constants (1280x720 design) ────────────────────────
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

PANEL_W, PANEL_H = 763, 545
PANEL_X = (1280 - PANEL_W) // 2
PANEL_Y = 88
TRANSPARENCY = 170
INNER_OFFSET = 36

THUMB_W, THUMB_H = 542, 273
THUMB_X = PANEL_X + (PANEL_W - THUMB_W) // 2
THUMB_Y = PANEL_Y + INNER_OFFSET

TITLE_X = 377
META_X = 377
TITLE_Y = THUMB_Y + THUMB_H + 10
META_Y = TITLE_Y + 45

BAR_X, BAR_Y = 388, META_Y + 45
BAR_RED_LEN = 280
BAR_TOTAL_LEN = 480

ICONS_W, ICONS_H = 415, 45
ICONS_X = PANEL_X + (PANEL_W - ICONS_W) // 2
ICONS_Y = BAR_Y + 48

MAX_TITLE_WIDTH = 580

# Bundled asset paths (copied from the reference repository).
_FONT_REGULAR = "SWAGGYMUSIC/assets/font.ttf"
_FONT_TITLE = "SWAGGYMUSIC/assets/font2.ttf"
_ICONS_PATH = "SWAGGYMUSIC/assets/play_icons.png"


def _trim_to_width(text: str, font, max_w: int) -> str:
    """Truncate ``text`` to ``max_w`` pixels using an ellipsis.
    Replicates the reference ``trim_to_width`` helper exactly."""
    ellipsis = "…"
    if font.getlength(text) <= max_w:
        return text
    for i in range(len(text) - 1, 0, -1):
        if font.getlength(text[:i] + ellipsis) <= max_w:
            return text[:i] + ellipsis
    return ellipsis


def _load_fonts():
    """Load the reference fonts.  Falls back to PIL's default bitmap font
    if the bundled TTF files are not available (matches the reference's
    OSError fallback)."""
    try:
        title_font = ImageFont.truetype(_FONT_TITLE, 32)
        regular_font = ImageFont.truetype(_FONT_REGULAR, 18)
    except OSError:
        title_font = regular_font = ImageFont.load_default()
    return title_font, regular_font


def _compose_reference_thumbnail(
    cover_img: Image.Image,
    title: str,
    views: str,
    duration_text: str,
    is_live: bool,
) -> Image.Image:
    """Pure-CPU PIL composition.  Replicates the reference
    ``get_thumb`` image-processing pipeline exactly, except that the cover
    art is passed in directly (already downloaded) instead of being
    re-fetched from a YouTube thumbnail URL.
    """
    base = cover_img.resize((1280, 720)).convert("RGBA")
    bg = ImageEnhance.Brightness(base.filter(ImageFilter.BoxBlur(10))).enhance(0.6)

    # Frosted glass panel
    panel_area = bg.crop((PANEL_X, PANEL_Y, PANEL_X + PANEL_W, PANEL_Y + PANEL_H))
    overlay = Image.new("RGBA", (PANEL_W, PANEL_H), (255, 255, 255, TRANSPARENCY))
    frosted = Image.alpha_composite(panel_area, overlay)
    mask = Image.new("L", (PANEL_W, PANEL_H), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, PANEL_W, PANEL_H), 50, fill=255)
    bg.paste(frosted, (PANEL_X, PANEL_Y), mask)

    # Draw details
    draw = ImageDraw.Draw(bg)
    title_font, regular_font = _load_fonts()

    thumb = base.resize((THUMB_W, THUMB_H))
    tmask = Image.new("L", thumb.size, 0)
    ImageDraw.Draw(tmask).rounded_rectangle((0, 0, THUMB_W, THUMB_H), 20, fill=255)
    bg.paste(thumb, (THUMB_X, THUMB_Y), tmask)

    draw.text(
        (TITLE_X, TITLE_Y),
        _trim_to_width(title, title_font, MAX_TITLE_WIDTH),
        fill="black",
        font=title_font,
    )
    draw.text(
        (META_X, META_Y),
        f"YouTube | {views}",
        fill="black",
        font=regular_font,
    )

    # Progress bar
    draw.line([(BAR_X, BAR_Y), (BAR_X + BAR_RED_LEN, BAR_Y)], fill="red", width=6)
    draw.line(
        [(BAR_X + BAR_RED_LEN, BAR_Y), (BAR_X + BAR_TOTAL_LEN, BAR_Y)],
        fill="gray",
        width=5,
    )
    draw.ellipse(
        [
            (BAR_X + BAR_RED_LEN - 7, BAR_Y - 7),
            (BAR_X + BAR_RED_LEN + 7, BAR_Y + 7),
        ],
        fill="red",
    )

    draw.text((BAR_X, BAR_Y + 15), "00:00", fill="black", font=regular_font)
    end_text = "Live" if is_live else duration_text
    draw.text(
        (
            BAR_X + BAR_TOTAL_LEN - (90 if is_live else 60),
            BAR_Y + 15,
        ),
        end_text,
        fill="red" if is_live else "black",
        font=regular_font,
    )

    # Icons strip (play_icons.png)
    if os.path.isfile(_ICONS_PATH):
        ic = Image.open(_ICONS_PATH).resize((ICONS_W, ICONS_H)).convert("RGBA")
        r, g, b, a = ic.split()
        black_ic = Image.merge(
            "RGBA",
            (
                r.point(lambda *_: 0),
                g.point(lambda *_: 0),
                b.point(lambda *_: 0),
                a,
            ),
        )
        bg.paste(black_ic, (ICONS_X, ICONS_Y), black_ic)

    return bg


class Thumbnail:
    """Thumbnail generator used by the TARGET's playback system.

    The runtime caller (``SWAGGYMUSIC/core/calls.py``) invokes::

        _thumb = await thumb.generate(media, user_avatar=None)

    This class preserves that entrypoint signature while internally
    using the REFERENCE repository's 1280x720 frosted-glass-panel design.
    """

    def __init__(self):
        self._session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """Cleanup hook called from SWAGGYMUSIC/__init__.py:stop()."""
        if self._session and not self._session.closed:
            try:
                await self._session.close()
            except Exception:
                pass
        self._session = None

    # ── helpers tolerant of Track / Media field-name differences ──
    @staticmethod
    def _first_attr(obj, *names, default=None):
        for name in names:
            val = getattr(obj, name, None)
            if val:
                return val
        return default

    @staticmethod
    def _parse_duration(value):
        """Accepts a duration as numeric seconds OR as a formatted string
        like "6:47" or "1:06:47" and returns a float number of seconds,
        or None if it can't be parsed."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            text = value.strip()
            if ":" in text:
                parts = text.split(":")
                try:
                    parts = [int(p) for p in parts]
                except ValueError:
                    return None
                seconds = 0
                for p in parts:
                    seconds = seconds * 60 + p
                return float(seconds)
            try:
                return float(text)
            except ValueError:
                return None
        return None

    async def _download_cover(self, url: str, dest_path: str) -> bool:
        """Download the cover art to ``dest_path``.  Returns True on
        success, False otherwise."""
        try:
            session = await self._get_session()
            async with session.get(url) as resp:
                if resp.status != 200:
                    return False
                async with aiofiles.open(dest_path, "wb") as f:
                    await f.write(await resp.read())
                return True
        except Exception:
            return False

    async def generate(
        self,
        media,
        output_path: str = None,
        user_avatar=None,
    ) -> str:
        """Entrypoint used by the bot (SWAGGYMUSIC/core/calls.py):

            _thumb = await thumb.generate(media)

        Pulls the cover URL / title / views / duration off of ``media``,
        downloads the cover art, composes the reference 1280x720
        frosted-glass-panel thumbnail, saves it to the cache directory
        and returns the local file path.

        ``user_avatar`` is accepted for backward-compatibility with the
        existing caller but is not used by the reference design.
        """
        cover_url = self._first_attr(
            media, "thumb", "thumbnail", "cover", "cover_url",
            "image", "photo", "photo_url", "art", "artwork",
        )
        if not cover_url:
            raise ValueError(
                "generate(): could not find a cover/thumbnail URL on the "
                f"given media object ({type(media).__name__!r}); expected "
                "one of: thumb, thumbnail, cover, cover_url, image, photo, "
                "photo_url, art, artwork"
            )

        title = self._first_attr(
            media, "title", "name", default="Unsupported Title"
        )
        # Match the reference's title normalization (re.sub \W+ -> space, .title())
        title = re.sub(r"\W+", " ", str(title)).title()

        views = self._first_attr(
            media, "view_count", "views", "viewCount", default="Unknown Views"
        )

        duration_raw = self._first_attr(
            media, "duration", "duration_seconds", "length", "track_duration",
            "seconds", default=None,
        )
        duration_seconds = self._parse_duration(duration_raw)

        # Live-detection matches the reference: no duration OR duration
        # string in {"", "live", "live now"} → treated as live.
        is_live = not duration_raw or str(duration_raw).strip().lower() in {
            "", "live", "live now",
        }
        if is_live:
            duration_text = "Live"
        elif duration_seconds is not None:
            # Format as M:SS or H:MM:SS for the end-of-bar label.
            total = int(duration_seconds)
            if total >= 3600:
                duration_text = f"{total // 3600}:{(total % 3600) // 60:02d}:{total % 60:02d}"
            else:
                duration_text = f"{total // 60}:{total % 60:02d}"
        else:
            duration_text = str(duration_raw) or "Unknown Mins"

        # Cache path keyed on the media id (matches reference cache naming).
        media_id = self._first_attr(media, "id", default=uuid.uuid4().hex)
        cache_path = os.path.join(CACHE_DIR, f"{media_id}_v4.png")
        if os.path.exists(cache_path):
            return cache_path

        # Download cover art to a temporary file.
        tmp_cover = os.path.join(CACHE_DIR, f"thumb{media_id}.png")
        try:
            downloaded = await self._download_cover(cover_url, tmp_cover)
            if not downloaded:
                # Fallback to the project's DEFAULT_THUMB URL if the cover
                # art download fails (mirrors the reference's behavior of
                # returning YOUTUBE_IMG_URL on failure).
                default_thumb = getattr(config, "DEFAULT_THUMB", None)
                if default_thumb:
                    downloaded = await self._download_cover(default_thumb, tmp_cover)
                if not downloaded:
                    raise ValueError(f"Failed to download cover image from {cover_url}")

            cover_img = await asyncio.to_thread(lambda: Image.open(tmp_cover))

            final_img = await asyncio.to_thread(
                _compose_reference_thumbnail,
                cover_img,
                title,
                str(views),
                duration_text,
                is_live,
            )
            await asyncio.to_thread(final_img.save, cache_path)
            return cache_path
        finally:
            try:
                if os.path.exists(tmp_cover):
                    os.remove(tmp_cover)
            except Exception:
                pass
            import gc
            gc.collect()
