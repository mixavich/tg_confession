import qrcode
import os
import asyncio
from telethon.errors.rpcerrorlist import SessionPasswordNeededError 
from telethon.sync import TelegramClient, events
from telethon.tl.functions.account import UpdateProfileRequest
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

APP_ID = int(os.getenv('APP_ID'))
APP_HASH = os.getenv('APP_HASH')
TG_PASSWORD = os.getenv('TG_PASSWORD')


async def ensure_logged_in(client: TelegramClient):
    await client.connect()

    if not await client.is_user_authorized():
        qr_login = await client.qr_login()
        qr = qrcode.QRCode(border=2)
        qr.add_data(qr_login.url)
        qr.make(fit=True)
        qr_matrix = qr.get_matrix()
        for y in range(0, len(qr_matrix) - 1, 2):
            upper = qr_matrix[y]
            lower = qr_matrix[y + 1]
            line = ''
            for u, l in zip(upper, lower):
                if u and l:
                    line += '█'  # full block
                elif u and not l:
                    line += '▀'  # upper half block
                elif not u and l:
                    line += '▄'  # lower half block
                else:
                    line += ' '  # empty
            print(line)

        try:
            await qr_login.wait()
        except SessionPasswordNeededError:
            await client.sign_in(password=TG_PASSWORD)

async def main():
    client = TelegramClient('confession_session', APP_ID, APP_HASH)
    await ensure_logged_in(client)

    @client.on(events.NewMessage)
    async def on_new_message(event):
        dialogs = await client.get_dialogs(archived=False)
        total_unread_unmuted = 0
        for dialog in dialogs:
            notify_settings = dialog.dialog.notify_settings
            mute_until = getattr(notify_settings, 'mute_until', None)
            if mute_until is None or mute_until == 0 or mute_until < datetime.now(timezone.utc):
                total_unread_unmuted += dialog.unread_count

        await client(UpdateProfileRequest(about=f"Sorry for not responding, my current number of unread messages is {total_unread_unmuted}"))

    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())