from pyrogram import filters, types
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from SWAGGYMUSIC import app, db, lang
from SWAGGYMUSIC.helpers import admin_check


def _thumb_markup(thumb_state: bool) -> InlineKeyboardMarkup:
    """Build the Thumbnail settings panel markup.

    Adapts the reference KURIGRAMSWAG thumb.py button layout:
      - Row 1: ENABLE / DISABLE toggle (callback_data = THUMBNAILCHANGE)
        Dynamic style: when thumb is OFF (button says ENABLE) → Green (SUCCESS);
        when thumb is ON (button says DISABLE) → Blue (PRIMARY).
      - Row 2: CLOSE (callback_data = close) — DANGER style.
    """
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="⌯ Eɴᴀʙʟᴇ ⌯" if not thumb_state else "⌯ Dɪsᴀʙʟᴇ ⌯",
                    callback_data="THUMBNAILCHANGE",
                    style=ButtonStyle.SUCCESS
                    if not thumb_state
                    else ButtonStyle.PRIMARY,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⌯ Cʟᴏsᴇ ⌯",
                    callback_data="close",
                    style=ButtonStyle.DANGER,
                ),
            ],
        ]
    )


@app.on_message(
    filters.command(["thumb", "thumbnail"]) & filters.group & ~app.bl_users
)
@lang.language()
@admin_check
async def _thumb_hndlr(_, m: types.Message):
    """Thumbnail settings panel — adapted from the reference KURIGRAMSWAG
    repository's ``/thumb`` command.

    Shows a button-based settings panel (ENABLE/DISABLE toggle + CLOSE)
    instead of the old text-only ``/thumb enable|disable`` interface.
    The actual toggle is performed by the ``THUMBNAILCHANGE`` callback
    handler in ``callbacks.py``.
    """
    thumb_state = await db.get_thumb_mode(m.chat.id)
    await m.reply_text(
        text=m.lang["thumb_1"],
        reply_markup=_thumb_markup(thumb_state),
        quote=True,
    )
