"""Шаблон Telegram-бота для обучения."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Dict, List, Tuple
import html

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from .config import Settings
from .rag_service import RAGService

logger = logging.getLogger(__name__)


class TelegramRAGBot:
    """Минимальный набор методов, которые должен реализовать студент."""

    def __init__(self, settings: Settings, rag_service: RAGService) -> None:
        self.settings = settings
        self.rag_service = rag_service
        self.bot = Bot(token=settings.telegram_bot_token)
        self.dispatcher = Dispatcher()
        self.chat_history: Dict[int, List[Tuple[str, str]]] = defaultdict(list)

        self.dispatcher.message.register(self.handle_start, CommandStart())
        self.dispatcher.message.register(self.handle_help, Command("help"))
        self.dispatcher.message.register(self.handle_answer, F.text)

    def _is_allowed(self, user_id: int | None) -> bool:
            if user_id is None:
                return False
            if not self.settings.allowed_user_ids:
                return True
            return user_id in self.settings.allowed_user_ids
    
    async def handle_start(self, message: Message) -> None:
        user_id = message.from_user.id if message.from_user else None

        if not self._is_allowed(user_id):
            await message.answer("Доступ запрещён.")
            return
        
        await message.answer("Привет! Я вирутальный помошник на базе GigaChat, чем могу помочь?")

    async def handle_help(self, message: Message) -> None:
        await message.answer(
            "Я RAG-бот. Задай вопрос текстом — я попробую ответить по базе знаний.\n"
            "Команды:\n"
            "/start — начать\n"
            "/help — помощь"
        )

    async def handle_answer(self, message: Message) -> None:
        user_id = message.from_user.id if message.from_user else None

        if not self._is_allowed(user_id):
            await message.answer("Доступ запрещён.")
            return
        
        question = message.text.strip()

        chat_id = message.chat.id

        try:
            result = await asyncio.to_thread(self.rag_service.ask, question)
        except Exception:
            await message.answer("Произошла ошибка при обработке запроса. Попробуй ещё раз.")
            return
        answer = (result.get("answer") or "").strip()
        source_documents = result.get("source_documents") or []
        self.chat_history[chat_id].append((question, answer))

        reply = answer if answer else "Не удалось сформировать ответ."

        if source_documents:
            reply += "\n\nИсточники:"
            for i, doc in enumerate(source_documents, start=1):
                meta = getattr(doc, "metadata", {}) or {}
                src = meta.get("source") or meta.get("url") or meta.get("title") or "unknown"

                quote = (doc.page_content or "").strip().replace("\n", " ")
                if len(quote) > 240:
                    quote = quote[:240] + "…"

                reply += f"\n{i}. {src}\n   '{quote}'"

        
        await message.answer(reply)

    async def run(self) -> None:
        logger.info("Запуск учебного бота")
        await self.dispatcher.start_polling(self.bot)


async def run_bot() -> None:
    settings = Settings()
    rag = RAGService(settings)
    bot = TelegramRAGBot(settings, rag)
    await bot.run()


if __name__ == "__main__":
    asyncio.run(run_bot())
