from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db import *
from filters import IsWhitelistedFilter, IsAdminFilter
from logger import info, warning, error
from reminder_task_manager import ReminderTaskManager

router = Router()

class AddTranslationStates(StatesGroup):
    waiting_for_translation = State()
    waiting_for_examples = State()
    waiting_for_complexity = State()

class ChangeSettingState(StatesGroup):
    waiting_for_new_value = State()

@router.message(Command("start"), IsWhitelistedFilter())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    info(f"User {user_id} started bot")
    
    if not is_added_to_users(user_id):
        add_user(user_id)
    
    await message.answer("Welcome! Let's start learning English words! 📚\n\nUse /learn to get your first word.")

@router.message(Command("learn"), IsWhitelistedFilter())
async def cmd_learn(message: Message):
    user_id = message.from_user.id
    info(f"User {user_id} requested /learn")
    
    if not are_words_up_to_date(user_id):
        words_for_today(user_id)
    
    await send_word(message, user_id)

@router.message(Command("settings"), IsWhitelistedFilter())
async def cmd_settings(message: Message):
    user_id = message.from_user.id
    info(f"User {user_id} requested /settings")
    
    settings = get_settings(user_id)
    text = "Your current settings:\n"
    for setting, value in settings.items():
        text += f"- {setting}: {value}\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Change {setting}", callback_data=f"change_setting_{setting}")]
        for setting, value in settings.items() if not setting=="user_id" and not setting=="debug"
    ])
    await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("change_setting_"), IsWhitelistedFilter())
async def handle_change_setting(query: CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    data = query.data.split("_")
    setting = '_'.join(data[2:])
    
    await state.update_data(setting=setting)
    await state.set_state(ChangeSettingState.waiting_for_new_value)
    
    info(f"User {user_id} is changing setting {setting}")
    
    await query.answer(f"Please enter a new value for setting '{setting}'")

@router.message(ChangeSettingState.waiting_for_new_value, IsWhitelistedFilter())
async def receive_new_setting_value(message: Message, state: FSMContext,reminder_manager: ReminderTaskManager):
    user_id = message.from_user.id
    data = await state.get_data()
    setting = data["setting"]
    new_value = message.text
    if(setting=="new_words_per_day"):
        try:
            new_value = int(new_value)
        except ValueError:
            await message.answer("❌ Please enter a valid number.")
            await state.clear()
            return
        
    if(setting == "reminder_time"):
        try:
            datetime.strptime(new_value, "%H:%M")  
        except ValueError:
            await message.answer("❌ Please enter a valid time in HH:MM format.")
            await state.clear()
            return
    
    change_settings(user_id, {setting: new_value})
    
    info(f"User {user_id} changed setting {setting} to {new_value}")
    
    if setting == "reminder_time":
        reminder_manager.add_task(bot=message.bot, user_id=user_id)


    await message.answer(f"✅ Setting '{setting}' updated to '{new_value}'")
    await state.clear()

async def send_word(message: Message, user_id: int):
    word_id = get_word_for_today(user_id)
    
    if word_id is None:
        await message.answer("No more words for today! Come back tomorrow! 😴")
        return

    word_info = get_word_info(word_id)
    if word_info is None:
        await message.answer("Error loading word. Try again.")
        return
    
    word = word_info["word"]
    translation = word_info.get("translation", "")
    usage_examples = word_info.get("usage_examples", "")
    complexity = word_info.get("complexity_level", "")
    
    # Build translation text with spoiler
    translation_text = translation if translation else "No translation available"
    spoiler_text = f"||{translation_text}||"
    
    text = f"📖 <b>{word}</b>\n\n"
    text += f"<tg-spoiler>{translation_text}</tg-spoiler>\n\n"
    
    if usage_examples:
        text += f"<i><tg-spoiler>Example: {usage_examples}</tg-spoiler></i>\n\n"
    
    if complexity:
        text += f"Level: {complexity}\n\n"
    
    text += "How well do you remember this word?"
    
    # Build keyboard with rating buttons
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="0 ❌", callback_data=f"rate_0_{word_id}"),
            InlineKeyboardButton(text="1", callback_data=f"rate_1_{word_id}"),
            InlineKeyboardButton(text="2", callback_data=f"rate_2_{word_id}"),
        ],
        [
            InlineKeyboardButton(text="3", callback_data=f"rate_3_{word_id}"),
            InlineKeyboardButton(text="4", callback_data=f"rate_4_{word_id}"),
            InlineKeyboardButton(text="5 ✅", callback_data=f"rate_5_{word_id}"),
        ]
    ])
    
    # Add translation button if missing and user is admin
    if not translation and is_admin(user_id):
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="➕ Add Translation", callback_data=f"add_trans_{word_id}")
        ])
    elif is_admin(user_id):
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="✏️ Edit Translation", callback_data=f"add_trans_{word_id}")
        ])

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("rate_"), IsWhitelistedFilter())
async def handle_rating(query: CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    data = query.data.split("_")
    rating = int(data[1])
    word_id = int(data[2])
    
    info(f"User {user_id} rated word {word_id} with rating {rating}")
    
    add_progress(user_id, word_id, rating)
    
    await query.answer(f"Rated! {['❌', '😞', '😐', '😊', '😄', '✅'][rating]}")
    # Remove rating buttons after rating
    await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(
    inline_keyboard=[
        [btn for btn in row if not btn.callback_data.startswith("rate_")]
        for row in query.message.reply_markup.inline_keyboard
    ]
    ))
    # Send next word
    await send_word(query.message, user_id)

@router.callback_query(F.data.startswith("add_trans_"), IsAdminFilter())
async def start_add_translation(query: CallbackQuery, state: FSMContext):
    word_id = int(query.data.split("_")[2])
    word_info = get_word_info(word_id)
    
    if not word_info:
        await query.answer("Error loading word")
        return
    
    await state.set_state(AddTranslationStates.waiting_for_translation)
    await state.update_data(word_id=word_id, word=word_info["word"])
    
    await query.message.answer(
        f"Current translation: {word_info.get('translation', 'None')}\nEnter translation for <b>{word_info['word']}</b>(or '-' to skip):",
        parse_mode="HTML"
    )
    await query.answer()

@router.message(AddTranslationStates.waiting_for_translation)
async def receive_translation(message: Message, state: FSMContext):
    data = await state.get_data()
    word_id = data["word_id"]
    word_info = get_word_info(word_id)
    translation = message.text if message.text != "-" else word_info.get("translation", "")
    await state.update_data(translation=translation)
    await state.set_state(AddTranslationStates.waiting_for_examples)
    
    await message.answer(f"Current usage example: {word_info.get('usage_examples', 'None')}\n\nEnter new usage examples (or '-' to skip):")

@router.message(AddTranslationStates.waiting_for_examples)
async def receive_examples(message: Message, state: FSMContext):
    data = await state.get_data()
    word_id = data["word_id"]
    word_info = get_word_info(word_id)
    examples = message.text if message.text != "-" else word_info.get("usage_examples", "")
    
    await state.update_data(examples=examples)
    await state.set_state(AddTranslationStates.waiting_for_complexity)
    
    await message.answer(f"Current complexity level: {word_info.get('complexity_level', 'None')}\nEnter new complexity level (e.g., 'A1', 'B2', or '-' to skip):")

@router.message(AddTranslationStates.waiting_for_complexity)
async def receive_complexity(message: Message, state: FSMContext):
    data = await state.get_data()
    word_id = data["word_id"]
    word_info = get_word_info(word_id)
    complexity = message.text if message.text != "-" else word_info.get("complexity_level", "")
    
    # Update word info
    update_info = {
        "translation": data["translation"],
        "usage_examples": data["examples"],
        "complexity_level": complexity
    }
    update_word_info(word_id, update_info)
    
    await message.answer(f"✅ Translation saved for '{data['word']}'!")
    
    # Return to learning
    await state.clear()


@router.message(Command("admin"), IsAdminFilter())
async def admin_actions(message: Message):
    user_id = message.from_user.id
    info(f"User {user_id} requested /admin")
    
    settings = get_settings(user_id)
    text = "You can add users to whitelist using /whitelist tg_id\n Current whitelisted users:\n"
    whitelist=get_whitelisted_users()
    if(whitelist==[]):
        text+="<i>Empty :(</i>"
    else:
        for usr in whitelist:
            text+=f"<i>{usr}</i>\n"
    await message.answer(text, parse_mode="HTML")

@router.message(Command("whitelist"), IsAdminFilter())
async def admin_actions(message: Message):
    user_id = message.from_user.id
    info(f"User {user_id} requested /whitelist")
    id=message.text.split(' ')[1]
    try:
        id = int(id)
    except ValueError:
        await message.answer("❌ Please enter a valid number as tg_id.")
        return

    add_to_whitelist(id)
    await message.answer(f"User {id} successfully added to whitelist.")