import asyncio
from datetime import datetime, timedelta
from logger import info, warning, error
from db import get_settings

class ReminderTaskManager:
    def __init__(self):
        self.tasks = {}

    async def reminder_task(self, bot, user_id):
        """Send daily reminders to the user."""
        try:
            while True:
                settings = get_settings(user_id)
                if not settings:
                    warning(f"Settings not found for user {user_id}, stopping reminder task.")
                    break

                reminder_time = settings.get("reminder_time", "15:00")
                now = datetime.now()
                reminder_datetime = datetime.strptime(reminder_time, "%H:%M").replace(
                    year=now.year, month=now.month, day=now.day
                )

                # If the reminder time is in the past, schedule it for the next day
                if reminder_datetime < now:
                    reminder_datetime += timedelta(days=1)

                wait_time = (reminder_datetime - now).total_seconds()
                info(f"User {user_id} will be reminded at {reminder_datetime}. Waiting {wait_time} seconds.")
                await asyncio.sleep(wait_time)
                await bot.send_message(user_id, "⏰ Reminder: It's time to /learn!")
        except asyncio.CancelledError:
            info(f"Reminder task cancelled for user {user_id}")
        
        except Exception as e:
            error(f"Error in reminder task for user {user_id}: {e}")

    def add_task(self, bot, user_id):
        """Add or replace a reminder task for a user."""
        if user_id in self.tasks:
            self.remove_task(user_id)

        task = asyncio.create_task(self.reminder_task(bot, user_id))
        self.tasks[user_id] = task
        info(f"Reminder task added for user {user_id}.")

    def remove_task(self, user_id):
        """Cancel and remove a reminder task for a user."""
        if user_id in self.tasks:
            self.tasks[user_id].cancel()
            del self.tasks[user_id]
            info(f"Reminder task removed for user {user_id}.")

    def stop_all_tasks(self):
        """Cancel all running tasks."""
        for user_id, task in self.tasks.items():
            task.cancel()
        self.tasks.clear()
        info("All reminder tasks stopped.")