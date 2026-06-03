import asyncio
import time
import random
import os  # <-- ADDED FOR SECURITY
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Securely grab the token hidden in Render's environment settings
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("Error: BOT_TOKEN environment variable is not set!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Funny random affirmations and insults for the roulette wheel
ROULETTE_PHRASES = [
    "🌟 AFFIRMATION: Look at you, surviving on nothing but water and sheer spite. Your fat cells are screaming in agony, begging for a single molecule of sugar. Let them burn. You are the master of this biological prison now.",
    "🍼 INSULT: I just calculated the trajectory of your willpower, and a single cookie will completely erase your dignity. Your fasting buddy is out-surviving you in sheer biological dominance. Don't be the first to weep.",
    "🌟 AFFIRMATION: The intense sugar cravings you are feeling right now are just the chemical ghosts of your past bad decisions dying a painful death. Let them scream. Do not feed the corpses.",
    "🍩 INSULT: Go ahead, open the fridge. Eat the poison. Let the processed high-fructose syrup flood your veins and turn your brain back into mush. Just remember that the bot—and your buddy—will know you collapsed over a little bit of powder.",
    "💀 JUDGMENT: You aren't actually hungry; your mind is just a needy little toddler throwing a tantrum because it wants a cheap hit of dopamine. Drink your plain water, sit in a dark room, and think about your life choices.",
    "🌟 AFFIRMATION: Your liver is throwing an absolute party right now because you aren't choking it with soda. Hang in there. Let the hunger pangs remind you that you are winning the war against corporate snacks.",
    "🦥 INSULT: If you break your fast right now, I will modify the /status board to permanently label you a 'Weak-Willed Pastry Consumer' until Oscar gives you permission to clear it. Step away from the kitchen.",
    "🩸 DARK MOTIVATION: Every hour you survive without caving is another hour you prove your primitive caveman ancestors wouldn't be completely embarrassed by you. Don't let a marshmallow defeat you."
]

# Set up clean database tables
async def init_db():
    async with aiosqlite.connect("final_fasting.db") as db:
        # Active fasts table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS fasters (
                user_id INTEGER PRIMARY KEY, username TEXT, start_time REAL
            )
        """)
        # Lifetime total fasting hours history table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS history (
                user_id INTEGER PRIMARY KEY, username TEXT, total_seconds REAL DEFAULT 0
            )
        """)
        await db.commit()

def format_duration(seconds):
    hours, remainder = divmod(int(seconds), 3600)
    minutes, _ = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    return f"{hours}h {minutes}m"

# --- 💧 CORE FASTING COMMANDS ---

@dp.message(Command("fast"))
async def start_fast(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    
    async with aiosqlite.connect("final_fasting.db") as db:
        await db.execute(
            "INSERT OR REPLACE INTO fasters (user_id, username, start_time) VALUES (?, ?, ?)",
            (user_id, username, time.time())
        )
        await db.commit()
        
    await message.reply(f"🔒 **LOCK THE FRIDGE!**\n\n**{username}** has started their timer. The sugar-free clock is ticking! Type /status to check on each other.")

@dp.message(Command("status"))
async def check_status(message: types.Message):
    async with aiosqlite.connect("final_fasting.db") as db:
        async with db.execute("SELECT username, start_time FROM fasters") as cursor:
            rows = await cursor.fetchall()
            
    if not rows:
        return await message.reply("❌ Nobody is fasting right now. Did you both cave to the sugar demons? Type /fast immediately!")
        
    response = "📊 **CURRENT ACTIVE SUFFERING:**\n\n"
    for username, start_time in rows:
        elapsed = time.time() - start_time
        response += f"• 👤 **{username}**: Fasting for `{format_duration(elapsed)}` 💧\n"
    
    await message.reply(response)

@dp.message(Command("stop"))
async def stop_fast(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    
    async with aiosqlite.connect("final_fasting.db") as db:
        async with db.execute("SELECT start_time FROM fasters WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            
        if row:
            elapsed = time.time() - row[0]
            await db.execute("DELETE FROM fasters WHERE user_id = ?", (user_id,))
            
            # Save to lifetime leaderboard history
            await db.execute("""
                INSERT INTO history (user_id, username, total_seconds) VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET total_seconds = total_seconds + ?
            """, (user_id, username, elapsed, elapsed))
            await db.commit()
            
            await message.reply(
                f"🏁 **FAST BROKEN!**\n\n"
                f"**{username}** tapped out after `{format_duration(elapsed)}`.\n"
                f"Your milestone has been added to the /leaderboard!"
            )
        else:
            await message.reply("You aren't even tracking an active fast! Type /fast first. 🙄")

# --- 🏆 LIFETIME LEADERBOARD ---

@dp.message(Command("leaderboard"))
async def show_leaderboard(message: types.Message):
    async with aiosqlite.connect("final_fasting.db") as db:
        async with db.execute("SELECT username, total_seconds FROM history ORDER BY total_seconds DESC") as cursor:
            rows = await cursor.fetchall()
            
    if not rows:
        return await message.reply("No historical records yet! Complete a fast and use /stop to get on the board.")
        
    response = "🏆 **LIFETIME SUFFERING CHAMPIONS:**\n\n"
    for rank, (username, total_seconds) in enumerate(rows, 1):
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "⭐"
        response += f"{medal} **{username}**: Total record of `{format_duration(total_seconds)}` completed.\n"
    await message.reply(response)

# --- 🎰 ROULETTE WHEEL ---

@dp.message(Command("roulette"))
async def phrase_roulette(message: types.Message):
    chosen_phrase = random.choice(ROULETTE_PHRASES)
    await message.reply(f"🎰 **ROULETTE SPIN RESULT:**\n\n{chosen_phrase}")

async def main():
    await init_db()
    print("Fasting Leaderboard & Roulette Bot is up and running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
