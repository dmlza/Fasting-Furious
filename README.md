# 💧 Fasting & Furious Bot

A lightweight, secure Telegram bot designed to track group fasting streaks, monitor active fasting status, and display a community leaderboard. Built with Python and hosted on a completely free cloud architecture.

---

## 🏗️ System Architecture & Hosting (Free Tier ELI5)

To maintain a 100% free production environment without losing data or hitting inactivity timeouts, the architecture uses four decoupled cloud services:

1. **GitHub**: Hosts the codebase safely. Configured with a `.gitignore` profile to block local database files (`.db`) or runtime caches from leaking publicly.
2. **Render (Free Web Service - The Brain 🧠)**: Executes the Python runtime environment. Runs `aiogram` long-polling for Telegram updates, while simultaneously running a background `aiohttp` web server to satisfy Render's web traffic requirements.
3. **Supabase (Free PostgreSQL - The Notebook 📓)**: Provides permanent data storage. Since Render's free container file system resets on deployment cycles (erasing local files), data is stored externally in a permanent cloud PostgreSQL cluster.
4. **UptimeRobot (The Alarm Clock ⏰)**: Automates network pings to the Render public URL endpoint every 5 minutes. This overrides Render's 15-minute inactivity dormancy rule, keeping the bot awake 24/7.

---

## 🔐 Security Configuration

No sensitive credentials or access keys are stored inside the repository code files. The application relies on system environment variables injected at runtime through the Render dashboard:

- `BOT_TOKEN`: The private cryptographic API token issued by Telegram's `@BotFather`.
- `DATABASE_URL`: The PostgreSQL connection URI string pointing to the remote Supabase data cluster.

---

## 💻 Database Schema

The database relies on two tables initialized directly within the Supabase instance:

```sql
CREATE TABLE fasters (
    user_id BIGINT PRIMARY KEY,
    username TEXT,
    start_time DOUBLE PRECISION
);

CREATE TABLE history (
    user_id BIGINT PRIMARY KEY,
    username TEXT,
    total_seconds DOUBLE PRECISION DEFAULT 0
);
```

---

## 🤖 Available Bot Commands

- `/fast` - Registers the user's ID, name, and current timestamp into the active tracking table.
- `/status` - Queries the data cluster and displays a live, formatted duration tracker of all active participants.
- `/stop` - Terminates the active fast, computes total elapsed time, purges the user from the tracking table, and updates their lifetime statistics in the history ledger.
- `/leaderboard` - Generates a competitive list ranked by lifetime completed fasting durations.
- `/roulette` - Selects and delivers a random motivational phrase or satirical insult to keep users engaged.

---

## 📦 Required Production Dependencies

Configured under Render's environment build properties:
- `aiogram`: Telegram Bot API framework.
- `psycopg2-binary`: PostgreSQL database driver.
- `aiohttp`: Asynchronous HTTP web engine used for the keep-alive health check.
