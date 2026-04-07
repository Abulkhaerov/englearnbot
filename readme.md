# English Learn Bot

This project is a Telegram bot designed to help users learn English vocabulary. It uses the SuperMemo 2 (SM2) algorithm for spaced repetition to optimize learning.

## Features
- Add users and track their progress.
- Provide daily vocabulary words for review and learning.
- Support for multiple wordlists (e.g., Oxford 3000, Oxford 5000).
- Admin and whitelist user management.

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   ```

2. Navigate to the project directory:
   ```bash
   cd english-learn-bot
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure the bot by editing `config.yaml`.

5. Run the bot:
   ```bash
   python main.py
   ```

## Project Structure
- `main.py`: Entry point for the bot.
- `db.py`: Database operations.
- `filters.py`: Custom filters for user roles.
- `handlers.py`: Telegram bot handlers.
- `utils.py`: Utility functions, including the SM2 algorithm.
- `logger.py`: Logging utility.
- `wordlists/`: Contains vocabulary wordlists.

---

# Бот для изучения английского языка

Этот проект представляет собой Telegram-бота, который помогает пользователям изучать английскую лексику. Он использует алгоритм SuperMemo 2 (SM2) для интервального повторения, чтобы оптимизировать обучение.

## Возможности
- Добавление пользователей и отслеживание их прогресса.
- Предоставление ежедневных слов для повторения и изучения.
- Поддержка нескольких списков слов (например, Oxford 3000, Oxford 5000).
- Управление администраторами и белым списком пользователей.

## Установка

1. Клонируйте репозиторий:
   ```bash
   git clone <repository-url>
   ```

2. Перейдите в директорию проекта:
   ```bash
   cd english-learn-bot
   ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Настройте бота, отредактировав файл `config.yaml`.

5. Запустите бота:
   ```bash
   python main.py
   ```

## Структура проекта
- `main.py`: Точка входа для бота.
- `db.py`: Операции с базой данных.
- `filters.py`: Кастомные фильтры для ролей пользователей.
- `handlers.py`: Обработчики Telegram-бота.
- `utils.py`: Утилиты, включая алгоритм SM2.
- `logger.py`: Утилита для логирования.
- `wordlists/`: Содержит списки слов.