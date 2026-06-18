import telebot
from telebot import types
import json
import os

TOKEN = "8607077799:AAFQN7KuuTCBkWtfoHx2ieYC83pKb9wsH2U"
ADMIN_ID = 6351786994

BKASH_NUMBER = "01781340116"
COIN_RATE = 200

bot = telebot.TeleBot(TOKEN)

DB_FILE = "data.json"

user_state = {}
buy_requests = {}

def load_data():
    if not os.path.exists(DB_FILE):
        return {
            "users": {},
            "requests": {}
        }

    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_user(uid):
    data = load_data()

    uid = str(uid)

    if uid not in data["users"]:
        data["users"][uid] = {
            "balance": 0
        }
        save_data(data)

    return data["users"][uid]

def main_menu():
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        "💰 Balance",
        "🛒 Buy Coin"
    )

    markup.row(
        "🔄 Transfer",
        "📊 Rate"
    )

    markup.row(
        "❓ Help"
    )

    return markup
@bot.message_handler(commands=["start"])
def start(message):

    get_user(message.from_user.id)

    bot.send_message(
        message.chat.id,
        "🏠 Main Menu",
        reply_markup=main_menu()
    )


@bot.message_handler(func=lambda m: m.text == "💰 Balance")
def balance(message):

    user = get_user(message.from_user.id)

    bot.send_message(
        message.chat.id,
        f"💰 Balance: {user['balance']} Coin"
    )


@bot.message_handler(func=lambda m: m.text == "📊 Rate")
def rate(message):

    bot.send_message(
        message.chat.id,
        "📊 Rate List\n\n"
        "1 View = 1 Coin\n"
        "1 Review = 3 Coin\n"
        "1 User = 5 Coin\n\n"
        f"{COIN_RATE} Coin = 1 Taka"
    )


@bot.message_handler(func=lambda m: m.text == "❓ Help")
def help_menu(message):

    bot.send_message(
        message.chat.id,
        f"📩 Contact Admin\n\nID: {ADMIN_ID}"
    )


@bot.message_handler(func=lambda m: m.text == "🛒 Buy Coin")
def buy_coin(message):

    user_state[message.from_user.id] = {
        "step": "buy_amount"
    }

    bot.send_message(
        message.chat.id,
        "🛒 কত Coin কিনতে চান?\n\nশুধু সংখ্যা লিখুন।"
    )
@bot.message_handler(func=lambda m: True)
def all_messages(message):

    uid = message.from_user.id

    if uid not in user_state:
        return

    state = user_state[uid]

    if state["step"] == "buy_amount":

        if not message.text.isdigit():
            bot.reply_to(
                message,
                "❌ শুধু সংখ্যা লিখুন"
            )
            return

        coin_amount = int(message.text)

        taka = coin_amount / COIN_RATE

        user_state[uid] = {
            "step": "trx_id",
            "coin_amount": coin_amount
        }

        bot.send_message(
            message.chat.id,
            f"🪙 Coin: {coin_amount}\n"
            f"💵 Pay: {taka:.2f} Taka\n\n"
            f"📱 bKash Personal:\n{BKASH_NUMBER}\n\n"
            "Payment করার পরে Transaction ID পাঠান।"
        )

        return

    if state["step"] == "trx_id":

        trx = message.text
        coin_amount = state["coin_amount"]

        request_id = str(uid)

        buy_requests[request_id] = {
            "user_id": uid,
            "coin": coin_amount,
            "trx": trx
        }

        markup = types.InlineKeyboardMarkup()

        approve_btn = types.InlineKeyboardButton(
            "✅ Approve",
            callback_data=f"approve:{uid}"
        )

        reject_btn = types.InlineKeyboardButton(
            "❌ Reject",
            callback_data=f"reject:{uid}"
        )

        markup.add(
            approve_btn,
            reject_btn
        )

        bot.send_message(
            ADMIN_ID,
            f"🛒 New Coin Order\n\n"
            f"👤 User ID: {uid}\n"
            f"🪙 Coin: {coin_amount}\n"
            f"🧾 TRX: {trx}",
            reply_markup=markup
        )

        bot.send_message(
            message.chat.id,
            "✅ Request Sent To Admin"
        )

        del user_state[uid]
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):

    data = call.data

    if data.startswith("approve:"):

        uid = data.split(":")[1]

        if uid not in buy_requests:
            bot.answer_callback_query(
                call.id,
                "Request Not Found"
            )
            return

        req = buy_requests[uid]

        data_db = load_data()

        uid_str = str(req["user_id"])

        if uid_str not in data_db["users"]:
            data_db["users"][uid_str] = {
                "balance": 0
            }

        data_db["users"][uid_str]["balance"] += req["coin"]

        save_data(data_db)

        bot.send_message(
            req["user_id"],
            f"✅ Your Order Approved\n\n"
            f"🪙 Added Coin: {req['coin']}"
        )

        bot.edit_message_text(
            f"✅ Approved\n\nUser: {uid}",
            call.message.chat.id,
            call.message.message_id
        )

        del buy_requests[uid]

    elif data.startswith("reject:"):

        uid = data.split(":")[1]

        if uid not in buy_requests:
            bot.answer_callback_query(
                call.id,
                "Request Not Found"
            )
            return

        req = buy_requests[uid]

        bot.send_message(
            req["user_id"],
            "❌ Your Order Rejected"
        )

        bot.edit_message_text(
            f"❌ Rejected\n\nUser: {uid}",
            call.message.chat.id,
            call.message.message_id
        )

        del buy_requests[uid]


print("Bot Started...")
bot.infinity_polling()
