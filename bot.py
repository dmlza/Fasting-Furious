import asyncio
import time
import random
import os
import psycopg2
import psycopg2.extras  # Configured for clean dictionary row parsing
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

TOKEN = os.environ.get("BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")

if not TOKEN or not DATABASE_URL:
    raise ValueError("Missing system configuration variables!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

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

def format_duration(seconds):
    hours, remainder = divmod(int(seconds), 3600)
    minutes, _ = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    return f"{hours}h {minutes}m"

# Helper for secure db execution with dictionary layout profiles
def run_query(query, params=(), fetch=False):
    conn = psycopg2.connect(DATABASE_URL)
    # Using RealDictCursor forces Python to read data by names instead of numbers
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(query, params)
    result = None
    if fetch:
        result = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return result

@dp.message(Command("fast"))
async def start_fast(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    
    run_query(
        "INSERT INTO fasters (user_id, username, start_time) VALUES (%s, %s, %s) ON CONFLICT (user_id) DO UPDATE SET start_time = EXCLUDED.start_time, username = EXCLUDED.username",
        (user_id, username, time.time())
    )
    await message.reply(f"🔒 **LOCK THE FRIDGE!**\n\n**{username}** has started their timer. The sugar-free clock is ticking! Type /status to check on each other.")

@dp.message(Command("status"))
async def check_status(message: types.Message):
    rows = run_query("SELECT username, start_time FROM fasters", fetch=True)
    if not rows:
        return await message.reply("❌ Nobody is fasting right now. Did you both cave to the sugar demons? Type /fast immediately!")
        
    response = "📊 **CURRENT ACTIVE SUFFERING:**\n\n"
    for row in rows:
        username = row['username']
        start_time = float(row['start_time'])
        elapsed = time.time() - start_time
        response += f"• 👤 **{username}**: Fasting for `{format_duration(elapsed)}` 💧\n"
    await message.reply(response)

@dp.message(Command("stop"))
async def stop_fast(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    
    rows = run_query("SELECT start_time FROM fasters WHERE user_id = %s", (user_id,), fetch=True)
    if rows and len(rows) > 0:
        start_time = float(rows[0]['start_time'])
        elapsed = time.time() - start_time
        
        run_query("DELETE FROM fasters WHERE user_id = %s", (user_id,))
        run_query("""
            INSERT INTO history (user_id, username, total_seconds) VALUES (%s, %s, %s)
            ON CONFLICT(user_id) DO UPDATE SET total_seconds = history.total_seconds + EXCLUDED.total_seconds
        """, (user_id, username, elapsed))
        
        await message.reply(f"🏁 **FAST BROKEN!**\n\n**{username}** tapped out after `{format_duration(elapsed)}`.\nYour milestone has been added to the /leaderboard!")
    else:
        await message.reply("You aren't even tracking an active fast! Type /fast first. 🙄")

@dp.message(Command("leaderboard"))
async def show_leaderboard(message: types.Message):
    rows = run_query("SELECT username, total_seconds FROM history ORDER BY total_seconds DESC", fetch=True)
    if not rows:
        return await message.reply("No historical records yet! Complete a fast and use /stop to get on the board.")
        
    response = "🏆 **LIFETIME SUFFERING CHAMPIONS:**\n\n"
    for rank, row in enumerate(rows, 1):
        username = row['username']
        total_seconds = float(row['total_seconds'])
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "⭐"
        response += f"{medal} **{username}**: Total record of `{format_duration(total_seconds)}` completed.\n"
    await message.reply(response)

@dp.message(Command("roulette"))
async def phrase_roulette(message: types.Message):
    chosen_phrase = random.choice(ROULETTE_PHRASES)
    await message.reply(f"🎰 **ROULETTE SPIN RESULT:**\n\n{chosen_phrase}")

async def handle(request):
    return web.Response(text="Bot is running!")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
