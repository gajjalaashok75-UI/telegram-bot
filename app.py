import os
import json
import logging
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# ==================== CONFIGURATION ====================
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'your_token_here')

if TOKEN == 'your_token_here':
    raise ValueError("Set TELEGRAM_BOT_TOKEN environment variable!")

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== DATABASE ====================
def load_user_data():
    try:
        with open('user_data.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_user_data(data):
    with open('user_data.json', 'w') as f:
        json.dump(data, f, indent=2)

user_data = load_user_data()

# ==================== HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    
    if user_id not in user_data:
        user_data[user_id] = {"queries": [], "joined": str(datetime.now())}
        save_user_data(user_data)
    
    welcome_text = f"""
👋 Hello {user.first_name}!

🤖 *GAKR Assistant* is ready!

🔍 *Smart Search* - Type any question
🧮 *Calculator* - "calc: 15*23"
🎲 *Random* - "random" or "coin"
📊 *Stats* - /stats

_Just send me anything!_
    """
    
    keyboard = [
        [InlineKeyboardButton("🔍 Example Query", callback_data='example_query')],
        [InlineKeyboardButton("🧮 Calculator", callback_data='calc_demo')],
        [InlineKeyboardButton("📊 My Stats", callback_data='show_stats')]
    ]
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
*🤖 GAKR Assistant Commands:*

/start - Start bot & show menu
/help - Show this help message
/stats - Your usage statistics
/clear - Clear your history

*Examples:*
`calc: 125 * 45`
`search: Python programming`
`random`
`coin`
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in user_data:
        queries = len(user_data[user_id].get("queries", []))
        joined = user_data[user_id].get("joined", "Unknown")[:10]
        
        stats_text = f"""
📊 *Your Statistics*

📝 Total Queries: {queries}
📅 Joined: {joined}
🤖 Status: Active
        """
    else:
        stats_text = "No data found. Send /start first!"
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in user_data:
        user_data[user_id]["queries"] = []
        save_user_data(user_data)
    await update.message.reply_text("🗑 History cleared!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = str(update.effective_user.id)
    
    if user_id not in user_data:
        user_data[user_id] = {"queries": [], "joined": str(datetime.now())}
    user_data[user_id]["queries"].append({"text": text, "time": str(datetime.now())})
    save_user_data(user_data)
    
    await update.message.chat.send_action(action="typing")
    
    text_lower = text.lower()
    
    if text_lower.startswith('calc:'):
        expression = text.split(':', 1)[1].strip()
        await handle_calculation(update, expression)
    elif text_lower.startswith('search:'):
        query = text.split(':', 1)[1].strip()
        await handle_search(update, query)
    elif text_lower in ['random', 'dice', 'roll']:
        await handle_random(update)
    elif text_lower in ['coin', 'flip', 'toss']:
        await handle_coin(update)
    elif any(word in text_lower for word in ['time', 'date', 'day']):
        await handle_datetime(update)
    elif any(word in text_lower for word in ['joke', 'funny', 'laugh']):
        await handle_joke(update)
    else:
        await handle_general_query(update, text)

async def handle_calculation(update: Update, expression: str):
    try:
        allowed = set('0123456789+-*/.() ')
        if not all(c in allowed for c in expression):
            await update.message.reply_text("❌ Invalid characters. Only numbers and + - * / allowed.")
            return
        
        result = eval(expression)
        response = f"🧮 *Calculation*\n\n`{expression}` = *{result}*"
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception:
        await update.message.reply_text("❌ Error in calculation.")

async def handle_search(update: Update, query: str):
    wiki_url = f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}"
    
    results = f"""
🔍 *Search Results for:* "{query}"

1️⃣ *Wikipedia*
   [Read more]({wiki_url})

2️⃣ *Knowledge Base*
   Key facts about {query}.

3️⃣ *Related Topics*
   • Introduction to {query}
   • {query} examples

_Tip: Be more specific!_
    """
    
    await update.message.reply_text(results, parse_mode='Markdown', disable_web_page_preview=True)

async def handle_random(update: Update):
    dice = random.randint(1, 6)
    num = random.randint(1, 100)
    await update.message.reply_text(f"🎲 *Dice:* {dice}\n🔢 *Number:* {num}")

async def handle_coin(update: Update):
    result = random.choice(['Heads', 'Tails'])
    emoji = '👑' if result == 'Heads' else '🪙'
    await update.message.reply_text(f"{emoji} *Coin:* {result}", parse_mode='Markdown')

async def handle_datetime(update: Update):
    now = datetime.now()
    await update.message.reply_text(
        f"🕐 *Time:* {now.strftime('%H:%M:%S')}\n📅 *Date:* {now.strftime('%B %d, %Y')}",
        parse_mode='Markdown'
    )

async def handle_joke(update: Update):
    jokes = [
        "Why do programmers prefer dark mode? Because light attracts bugs! 🐛",
        "Why did the developer go broke? Because he used up all his cache! 💸",
        "Why do Python programmers wear glasses? Because they can't C! 👓",
    ]
    await update.message.reply_text(random.choice(jokes))

async def handle_general_query(update: Update, text: str):
    text_lower = text.lower()
    
    if any(g in text_lower for g in ['hi', 'hello', 'hey']):
        response = "👋 Hello! Try 'search: [topic]' or 'calc: [math]'."
    elif 'thank' in text_lower:
        response = "🙌 You're welcome!"
    else:
        response = f"""
💡 I got: "{text}"

Try:
• "search: {text}"
• "calc: 15*23"
• "random" or "coin"

_Type /help for more_
        """
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'example_query':
        await query.edit_message_text("Try: `search: Python programming`", parse_mode='Markdown')
    elif query.data == 'calc_demo':
        await query.edit_message_text("Try: `calc: 15 * 23`", parse_mode='Markdown')
    elif query.data == 'show_stats':
        user_id = str(update.effective_user.id)
        count = len(user_data.get(user_id, {}).get("queries", []))
        await query.edit_message_text(f"📊 You've made *{count}* queries!", parse_mode='Markdown')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("⚠️ Error occurred. Try /start")

# ==================== MAIN ====================

def main():
    print("🤖 Starting GAKR Bot on Render...")
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    # RUN POLLING (Works on Render, blocked on HF Spaces)
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
