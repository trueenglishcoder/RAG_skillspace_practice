#!/usr/bin/env python3
"""Учебный скрипт для скачивания HTML FAQ."""

from __future__ import annotations

import argparse
import pathlib

import requests


def download(url: str, output: pathlib.Path, verify: bool = True) -> None:
    resp = requests.get(url = url, verify = verify, timeout = 30)
    resp.raise_for_status()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(resp.text, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Загрузка FAQ страницы")
    parser.add_argument("--url", required=True)
    parser.add_argument("--out", required=True, type = pathlib.Path)
    parser.add_argument("--no-verify", action = "store_true")
    
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    download(args.url, args.out, not args.no_verify)


if __name__ == "__main__":
    main()
