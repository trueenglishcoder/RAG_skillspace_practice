"""Учебная версия RAG сервиса. Заполните пропуски."""

from __future__ import annotations

import logging
from functools import cached_property
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import GigaChat
from langchain_community.embeddings import GigaChatEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

from .config import Settings  # можно переключиться на боевой config после реализации

logger = logging.getLogger(__name__)


ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Ты — помощник, отвечающий по базе знаний. Используй только контекст. "
            "Если ответа нет в контексте — так и скажи и попроси уточнить вопрос."
        ),
        ("human", "Контекст:\n{context}\n\nВопрос:\n{question}\n\nОтвет:"),
    ]
)


class RAGService:
    """Скелет, где нужно реализовать шаги RAG."""

    def __init__(self, settings: Settings):
        self.settings = settings

    @cached_property
    def embeddings(self) -> GigaChatEmbeddings:
        return GigaChatEmbeddings(credentials = self.settings.gigachat_credentials,
                                  scope = self.settings.gigachat_scope,
                                  verify_ssl_certs = self.settings.gigachat_verify_ssl)

    @cached_property
    def retriever(self):
        store = FAISS.load_local(
            folder_path = str(self.settings.vector_store_path),
            embeddings = self.embeddings,
            allow_dangerous_deserialization=True
        )
        return store.as_retriever(search_kwargs = {"k": self.settings.top_k_results})

    @cached_property
    def llm(self) -> GigaChat:
        return GigaChat(
            credentials = self.settings.gigachat_credentials,
            scope = self.settings.gigachat_scope,
            model=self.settings.gigachat_model,
            verify_ssl_certs = self.settings.gigachat_verify_ssl,
            temperature=0.1
        )

    @cached_property
    def chain(self):
        answer_chain = ANSWER_PROMPT | self.llm | StrOutputParser()

        def _invoke(payload: dict[str, Any]):
            question = payload["question"]
            source_documents = self.retriever.invoke(question)
            context = "\n\n---\n\n".join(doc.page_content for doc in source_documents) if source_documents else ""
            answer = answer_chain.invoke({"context": context, "question": question})
            logger.info("Retrieved %d documents", len(source_documents))
            return {"answer": answer, "source_documents": source_documents}
        return RunnableLambda(_invoke)

    def ask(self, question: str) -> dict[str, Any]:
        return self.chain.invoke({"question": question})


__all__ = ["RAGService"]
