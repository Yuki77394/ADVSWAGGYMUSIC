from pyrogram import filters, types
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from SWAGGYMUSIC import app, db, lang
from SWAGGYMUSIC.helpers import can_manage_vc


def _autoplay_markup(autoplay_state: bool) -> InlineKeyboardMarkup:
    """Build the Autoplay settings panel markup.

    Adapted from the reference KURIGRAMSWAG repository's autoplay.py
    button layout:
      - Row 1: ENABLE / DISABLE toggle (callback_data = AUTOPLAYCHANGE).
        When autoplay is OFF (button says ENABLE) or ON (button says
        DISABLE), the button is Blue (PRIMARY) per the project-wide
        button color spec.
      - Row 2: CLOSE (callback_data = close) — Red (DANGER).
    """
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="≡ Eɴᴀʙʟᴇ ≡" if not autoplay_state else "≡ Dɪsᴀʙʟᴇ ≡",
                    callback_data="AUTOPLAYCHANGE",
                    style=ButtonStyle.PRIMARY,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="≡ Cʟᴏsᴇ ≡",
                    callback_data="close",
                    style=ButtonStyle.DANGER,
                ),
            ],
        ]
    )


@app.on_message(filters.command("autoplay") & filters.group & ~app.bl_users)
@lang.language()
@can_manage_vc
async def _autoplay(_, m: types.Message):
    chat_id = m.chat.id

    # /autoplay  (no argument) — show the reference-style button panel.
    if len(m.command) < 2:
        status = await db.get_autoplay(chat_id)

        # Dynamic bot name — resolved at runtime from the live
        # Pyrogram/Kurigram client.  NEVER hardcoded.
        bot_name = getattr(app, "name", None) or "Music"

        text = (
            f"<b>˹{bot_name} ♪</b>\n\n"
            f"<b>≫ Wʜᴇɴ Eɴᴀʙʟᴇᴅ, Tʜᴇ Bᴏᴛ Wɪʟʟ\n"
            f"Aᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ Pʟᴀʏ Rᴇʟᴀᴛᴇᴅ\n"
            f"Sᴏɴɢs Wʜᴇɴ Tʜᴇ Qᴜᴇᴜᴇ Is\n"
            f"Eᴍᴘᴛʏ.</b>"
        )

        return await m.reply_text(
            text=text,
            reply_markup=_autoplay_markup(status),
            quote=True,
        )

    arg = m.command[1].strip().lower()

    # /autoplay on
    if arg in ("on", "enable", "enabled", "yes", "true"):
        await db.set_autoplay(chat_id, True)
        return await m.reply_text(m.lang["autoplay_enabled"])

    # /autoplay off
    if arg in ("off", "disable", "disabled", "no", "false"):
        await db.set_autoplay(chat_id, False)
        return await m.reply_text(m.lang["autoplay_disabled"])

    return await m.reply_text(m.lang["autoplay_usage"])
