import asyncio
import html
import json
import random

import aiohttp
from pyrogram import enums, filters, types

from SWAGGYMUSIC import app, config, db, lang
from SWAGGYMUSIC.helpers import admin_check, buttons, utils
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


# Celebration / confetti message-effect ID applied to the private /start
# welcome photo. Sourced from the SWAGGYMUSIC reference repository.
# Kurigram's high-level Message.reply_photo() does not expose
# message_effect_id, while Telegram's Bot API does — so the private welcome
# photo is sent through the Bot API endpoint (see _send_start_photo_with_effect).
CELEBRATION_EFFECT_ID = 5046509860389126442


def _build_start_caption(message: types.Message, template: str) -> str:
    """Build a Bot-API-safe HTML caption from the language template.

    The template uses ``{0}`` for the user mention and ``{1}`` for the bot
    mention. Both display names are HTML-escaped and wrapped in safe anchor
    tags so user-controlled names cannot break the caption markup.
    """
    user = message.from_user
    user_name = (
        " ".join(part for part in (user.first_name, user.last_name) if part).strip()
        or "User"
    )
    safe_user_name = html.escape(user_name, quote=False)
    user_mention = f'<a href="tg://user?id={int(user.id)}">{safe_user_name}</a>'

    bot_username = getattr(app, "username", None)
    bot_name = getattr(app, "name", None) or bot_username or "SWAGGYMUSIC"
    safe_bot_name = html.escape(str(bot_name).strip(), quote=False)
    bot_mention = (
        f'<a href="https://t.me/{bot_username}">{safe_bot_name}</a>'
        if bot_username
        else safe_bot_name
    )

    return template.format(user_mention, bot_mention)


async def _send_start_photo_with_effect(
    message: types.Message,
    photo: str,
    caption: str,
    reply_markup: types.InlineKeyboardMarkup,
) -> None:
    """Send the private /start welcome photo through the Bot API so the
    celebration message-effect ID can be attached. Falls back to a regular
    Kurigram reply_photo / reply_text on failure so the start flow keeps
    working even if the Bot API call fails.
    """
    keyboard = []
    for row in (reply_markup.inline_keyboard if reply_markup else []):
        row_buttons = []
        for button in row:
            item = {"text": button.text}
            if button.url:
                item["url"] = button.url
            elif button.callback_data is not None:
                item["callback_data"] = button.callback_data
            elif button.user_id:
                item["url"] = f"tg://user?id={button.user_id}"
            else:
                continue

            style = getattr(button, "style", None)
            if style == ButtonStyle.PRIMARY:
                item["style"] = "primary"
            elif style == ButtonStyle.SUCCESS:
                item["style"] = "success"
            elif style == ButtonStyle.DANGER:
                item["style"] = "danger"

            row_buttons.append(item)
        if row_buttons:
            keyboard.append(row_buttons)

    payload = {
        "chat_id": message.chat.id,
        "photo": photo,
        "caption": caption,
        "parse_mode": "HTML",
        "has_spoiler": True,
        "message_effect_id": str(CELEBRATION_EFFECT_ID),
        "reply_markup": json.dumps({"inline_keyboard": keyboard}),
        "reply_parameters": json.dumps({"message_id": message.id}),
    }

    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendPhoto"
    timeout = aiohttp.ClientTimeout(total=30)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, data=payload) as response:
                result = await response.json(content_type=None)
                if response.status != 200 or not result.get("ok"):
                    raise RuntimeError(f"Telegram Bot API sendPhoto failed: {result}")
                return
    except Exception:
        # Fallback: send the photo through Kurigram (without the message
        # effect) so the welcome message still works.
        try:
            await message.reply_photo(
                photo=photo,
                caption=caption,
                quote=True,
                reply_markup=reply_markup,
            )
        except Exception:
            try:
                await message.reply_text(
                    text=caption,
                    quote=True,
                    reply_markup=reply_markup,
                )
            except Exception:
                pass


@app.on_message(filters.command(["help"]) & filters.private & ~app.bl_users)
@lang.language()
async def _help(_, m: types.Message):
    await m.reply_text(
        text=m.lang["help_menu"],
        reply_markup=buttons.help_markup(m.lang),
        quote=True,
    )


@app.on_message(filters.command(["start"]))
@lang.language()
async def start(_, message: types.Message):
    if message.from_user.id in app.bl_users and message.from_user.id not in db.notified:
        return await message.reply_text(message.lang["bl_user_notify"])

    if len(message.command) > 1 and message.command[1] == "help":
        return await _help(_, message)

    private = message.chat.type == enums.ChatType.PRIVATE

    # ❤️ reaction on the user's /start message (best-effort, never fatal).
    if private:
        try:
            await message.react("❤️", big=True)
        except Exception:
            pass

    if private:
        _text = _build_start_caption(message, message.lang["start_pm"])
    else:
        _text = message.lang["start_gp"].format(app.name)

    key = buttons.start_key(message.lang, private)

    # Random image from the SWAGGYMUSIC 11-image pool.
    start_photo = random.choice(config.START_IMAGES)

    if private:
        # Private chat: send via Bot API to attach the 🎉 celebration effect.
        await _send_start_photo_with_effect(
            message=message,
            photo=start_photo,
            caption=_text,
            reply_markup=key,
        )
    else:
        # Group chat: regular Kurigram reply_photo (no effect needed here).
        await message.reply_photo(
            photo=start_photo,
            caption=_text,
            reply_markup=key,
            quote=not private,
        )

    if private:
        # Log EVERY /start, but add the user to the database only once.
        await utils.send_log(message)
        if not await db.is_user(message.from_user.id):
            await db.add_user(message.from_user.id)
    else:
        # Log EVERY group /start, but add the chat to the database only once.
        await utils.send_log(message, True)
        if not await db.is_chat(message.chat.id):
            await db.add_chat(message.chat.id)


@app.on_message(filters.command(["settings", "playmode"]) & filters.group & ~app.bl_users)
@lang.language()
@admin_check
async def settings(_, message: types.Message):
    admin_only = await db.get_play_mode(message.chat.id)
    cmd_delete = await db.get_cmd_delete(message.chat.id)
    vclogger = await db.get_vclogger(message.chat.id)
    thumbnail = await db.get_thumb_mode(message.chat.id)
    autoplay = await db.get_autoplay(message.chat.id)
    _language = await db.get_lang(message.chat.id)
    await message.reply_text(
        text=message.lang["start_settings"].format(message.chat.title),
        reply_markup=buttons.settings_markup(
            message.lang,
            admin_only,
            cmd_delete,
            vclogger,
            thumbnail,
            autoplay,
            _language,
            message.chat.id,
        ),
        quote=True,
    )

@app.on_message(filters.new_chat_members, group=7)
@lang.language()
async def _new_member(_, message: types.Message):
    if message.chat.type != enums.ChatType.SUPERGROUP:
        return await message.chat.leave()

    await asyncio.sleep(3)
    for member in message.new_chat_members:
        if member.id == app.id:
            #if await db.is_chat(message.chat.id):
                #return
            await utils.send_log(message, True)
            await db.add_chat(message.chat.id)

            adder = message.from_user.mention if message.from_user else "there"
            _text = message.lang["chat_added"].format(
                adder, app.name, message.lang["support"]
            )
            key = types.InlineKeyboardMarkup(
                [
                    [
                        types.InlineKeyboardButton(
                            text=message.lang["add_me"],
                            url=f"https://t.me/{app.username}?startgroup=true",
                            style=ButtonStyle.SUCCESS,
                        ),
                        types.InlineKeyboardButton(
                            text=message.lang["support"],
                            url=config.SUPPORT_CHAT,
                            style=ButtonStyle.PRIMARY,
                        ),
                    ]
                ]
            )
            try:
                await app.send_photo(
                    chat_id=message.chat.id,
                    photo=random.choice(config.START_IMAGES),
                    caption=_text,
                    reply_markup=key,
                )
            except Exception:
                try:
                    await app.send_message(
                        chat_id=message.chat.id,
                        text=_text,
                        reply_markup=key,
                    )
                except Exception:
                    pass


@app.on_message(filters.left_chat_member, group=8)
async def _left_member(_, message: types.Message):
    if message.left_chat_member and message.left_chat_member.id == app.id:
        await utils.send_left_log(message.chat.id, message.chat.title, message.from_user)
        await db.rm_chat(message.chat.id)


@app.on_chat_member_updated()
async def _my_chat_member_updated(_, member: types.ChatMemberUpdated):
    if not member.old_chat_member or not member.new_chat_member:
        return
    old_status = member.old_chat_member.status
    new_status = member.new_chat_member.status

    if (
        old_status in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR]
        and new_status in [enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED]
    ):
        if member.new_chat_member.user and member.new_chat_member.user.id == app.id:
            await utils.send_left_log(member.chat.id, member.chat.title, member.from_user)
            await db.rm_chat(member.chat.id)
