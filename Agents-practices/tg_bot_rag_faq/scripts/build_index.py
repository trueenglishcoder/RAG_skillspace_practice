#!/usr/bin/env python3
"""Учебный скрипт для построения FAISS индекса."""

from __future__ import annotations

import argparse
import pathlib
import json
import os

from langchain_core.documents import Document
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import GigaChatEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

def load_dataset(path: pathlib.Path) -> list[Document]:
    data = json.loads(path.read_text(encoding="utf-8"))

    docs: list[Document] = []
    for i, item in enumerate(data):
        question = (item.get("question") or "").strip()
        answer = (item.get("answer") or "").strip()
        if not question or not answer:
            continue

        docs.append(
            Document(
                page_content=f"Вопрос: {question}\nОтвет: {answer}",
                metadata={
                    "source": str(path),
                    "row": i,
                    "question": question,
                },
            )

        )
    return docs

def build_index(input_path: pathlib.Path, store_dir: pathlib.Path) -> None:
    documents = load_dataset(input_path)

    splitter = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap = 150)
    chunks = splitter.split_documents(documents)

    embeddings = GigaChatEmbeddings(credentials = os.environ["GIGACHAT_CREDENTIALS"],
                                  scope = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS"),
                                  verify_ssl_certs = os.getenv("GIGACHAT_VERIFY_SSL"))
    store = FAISS.from_documents(chunks, embeddings)
    store_dir.mkdir(parents=True, exist_ok=True)
    store.save_local(str(store_dir))


def main() -> None:
    parser = argparse.ArgumentParser(description="FAISS builder")
    parser.add_argument("--input", required=True, type=pathlib.Path, help="JSON файл датасета")
    parser.add_argument("--store", required=True, type=pathlib.Path, help="Папка для сохранения индекса")
    args = parser.parse_args()

    build_index(args.input, args.store)


if __name__ == "__main__":
    main()
