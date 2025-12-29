#!/usr/bin/env python3
"""Учебный конвертер FAQ в JSON."""

from __future__ import annotations

import argparse
import json
import pathlib

from bs4 import BeautifulSoup


def parse_html(path: pathlib.Path) -> list[dict[str, str]]:
    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    result: list[dict[str, str]] = []
    headings = soup.find_all("h2")
    for h2 in headings:
        question = h2.get_text(" ", strip=True)
        if not question:
            continue

        parts: list[str] = []
        for sib in h2.next_siblings:
            if getattr(sib, "name", None) == "h2":
                break
            if getattr(sib, "get_text", None):
                text = sib.get_text(" ", strip=True)
                if text:
                    parts.append(text)
        
        answer = "\n".join(parts).strip()
        if answer:
            result.append({"question": question, "answer": answer})

    return result


def parse_markdown(path: pathlib.Path) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    items: list[dict[str, str]] = []
    current_q: str | None = None
    current_a: list[str] = []

    def flush():
        nonlocal current_q, current_a
        if current_q is not None:
            answer = "\n".join(current_a).strip()
            q = current_q.strip()
            if q and answer:
                items.append({"question": q, "answer": answer})
        current_q = None
        current_a = []

    for line in lines:
        if line.startswith("## "):
            flush()
            current_q = line[3:].strip()
        else:
            if current_q is not None:
                current_a.append(line)

    flush()
    return items


def main() -> None:
    parser = argparse.ArgumentParser(description="Сбор датасета")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--html", type=pathlib.Path, help="HTML файл с FAQ")
    group.add_argument("--markdown", type=pathlib.Path, help="Markdown файл с FAQ (## Вопрос)")
    parser.add_argument("--out", required=True, type=pathlib.Path, help="Куда сохранить JSON датасет")
    args = parser.parse_args()

    if args.html:
        data = parse_html(args.html)
    else:
        data = parse_markdown(args.markdown)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
