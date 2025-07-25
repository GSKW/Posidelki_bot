# 🎉 PosidelkiBot - Бот для учета общих расходов

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![Aiogram](https://img.shields.io/badge/Aiogram-3.x-blue)](https://docs.aiogram.dev)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## 📌 О проекте

PosidelkiBot — это Telegram-бот для удобного учета общих расходов в компаниях друзей, соседей по квартире или коллег. Бот позволяет:

- Вносить совместные траты
- Автоматически рассчитывать долги
- Просматривать историю расходов
- Получать напоминания о задолженностях

## ✨ Возможности

### 💸 Учет расходов
- Добавление трат с описанием и категоризацией
- Указание плательщика и участников
- Гибкое распределение сумм

### 📊 Автоматический расчет
- Интеллектуальное вычисление долгов
- Наглядное представление "кто кому должен"
- Поддержка разных валют

### 📱 Удобный интерфейс
- Интуитивно понятное меню
- Быстрый ввод данных
- Подробная статистика

## 🛠 Технологии

- **Python 3.9+**
- **Aiogram 3.x**

## 🚀 Быстрый старт

### Требования
- Python 3.9 или новее
- Telegram бот (получить у [@BotFather](https://t.me/BotFather))

### Установка
```bash
# Клонировать репозиторий
git clone https://github.com/GSKW/posidelkibot.git
cd posidelkibot

# Установить зависимости
pip install -r requirements.txt

# Настроить конфигурацию
cp .env.example .env
nano .env