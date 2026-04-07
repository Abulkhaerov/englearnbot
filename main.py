import asyncio
import sqlite3
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from config import config
from handlers import router
from logger import info, warning, error
from reminder_task_manager import ReminderTaskManager


reminder_manager = None

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="learn", description="Get a word to learn"),
    ]
    await bot.set_my_commands(commands)
    info("Bot commands set successfully")


async def main():
    """Main entry point"""
    global reminder_manager
    try:
        token = config['telegram']['token']
        bot = Bot(token=token)
        dp = Dispatcher()

        reminder_manager = ReminderTaskManager()
        dp.include_router(router)
        dp.workflow_data["reminder_manager"] = reminder_manager
        await set_commands(bot)

        info("Starting bot polling...")
        asyncio.create_task(start_reminders(bot, reminder_manager))  # Start reminders
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

    except Exception as e:
        error(f"Fatal error in main: {e}")
        raise
    finally:
        await bot.session.close()
        info("Bot session closed")

async def start_reminders(bot, reminder_manager):
    """Start reminder tasks for all users."""
    try:
        conn = sqlite3.connect(config['database']['path'])
        c = conn.cursor()
        c.execute("SELECT user_id FROM users")
        users = c.fetchall()
        for user in users:
            user_id = user[0]
            reminder_manager.add_task(bot, user_id)
        info("Reminder tasks started for all users.")
    except Exception as e:
        error(f"Error starting reminders: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        info("Bot stopped by user")
        reminder_manager.stop_all_tasks() 
    except Exception as e:
        error(f"Unexpected error: {e}")