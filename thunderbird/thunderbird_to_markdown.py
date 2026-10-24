#!/usr/bin/env python3
"""Export locally stored Thunderbird messages as Markdown files.

Reads Thunderbird mbox folders and standalone .eml files. It does not contact
mail servers, modify the Thunderbird profile, or export account credentials.
"""

from __future__ import annotations

import argparse
import configparser
import hashlib
import html
import mailbox
import os
import re
import sys
from datetime import datetime
from email.header import decode_header, make_header
from email import policy
from email.message import Message
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Iterable


def default_profile_roots() -> list[Path]:
    home = Path.home()
    candidates = [
        home / "Library" / "Thunderbird",
        home / ".thunderbird",
        home / ".mozilla-thunderbird",
    ]
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.insert(0, Path(appdata) / "Thunderbird")
    return [p for p in candidates if p.is_dir()]


def discover_profiles() -> list[Path]:
    profiles: list[Path] = []
    for root in default_profile_roots():
        ini = root / "profiles.ini"
        if not ini.exists():
            continue
        parser = configparser.RawConfigParser()
        parser.read(ini, encoding="utf-8")
        for section in parser.sections():
            if not section.startswith("Profile"):
                continue
            value = parser.get(section, "Path", fallback="").strip()
            if not value:
                continue
            relative = parser.get(section, "IsRelative", fallback="1") == "1"
            profile = (root / value) if relative else Path(value)
            if profile.is_dir() and profile not in profiles:
                profiles.append(profile)
    return profiles


def clean_name(value: str, limit: int = 100) -> str:
    value = re.sub(r"[\\/:*?\"<>|\x00-\x1f]", "_", value)
    value = re.sub(r"\s+", " ", value).strip(" ._")
    return (value or "mail")[:limit]


def header_text(message: Message, name: str) -> str:
    value = message.get(name)
    if value is None:
        return ""
    try:
        return str(make_header(decode_header(str(value)))).strip()
    except Exception:
        return ""


class PlainTextExtractor:
    def __init__(self) -> None:
        self.parts: list[str] = []
        self.hidden = 0

    def feed(self, source: str) -> None:
        # A small standard-library HTML-to-text conversion for HTML-only mail.
        from html.parser import HTMLParser

        class Parser(HTMLParser):
            def __init__(self, outer: "PlainTextExtractor") -> None:
                super().__init__(convert_charrefs=True)
                self.outer = outer

            def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
                if tag.lower() in {"script", "style", "head"}:
                    self.outer.hidden += 1
                elif tag.lower() in {"br", "p", "div", "li", "tr", "h1", "h2", "h3"}:
                    self.outer.parts.append("\n")

            def handle_endtag(self, tag: str) -> None:
                if tag.lower() in {"script", "style", "head"}:
                    self.outer.hidden = max(0, self.outer.hidden - 1)
                elif tag.lower() in {"p", "div", "li", "tr", "h1", "h2", "h3"}:
                    self.outer.parts.append("\n")

            def handle_data(self, data: str) -> None:
                if not self.outer.hidden:
                    self.outer.parts.append(data)

        Parser(self).feed(source)

    def text(self) -> str:
        text = html.unescape("".join(self.parts))
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n[ \t]+", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def message_body(message: Message) -> tuple[str, list[str]]:
    plain: list[str] = []
    rich: list[str] = []
    attachments: list[str] = []
    parts: Iterable[Message] = message.walk() if message.is_multipart() else [message]
    for part in parts:
        filename = part.get_filename()
        disposition = part.get_content_disposition()
        if filename or disposition == "attachment":
            attachments.append(filename or "(ファイル名なし)")
            continue
        if part.get_content_maintype() != "text":
            continue
        try:
            content = part.get_content()
        except Exception:
            raw = part.get_payload(decode=True) or b""
            charset = part.get_content_charset() or "utf-8"
            try:
                content = raw.decode(charset, errors="replace")
            except LookupError:
                content = raw.decode("utf-8", errors="replace")
        if not isinstance(content, str):
            continue
        if part.get_content_subtype() == "plain":
            plain.append(content)
        elif part.get_content_subtype() == "html":
            rich.append(content)
    body = "\n\n".join(plain).strip()
    if not body and rich:
        extractor = PlainTextExtractor()
        extractor.feed("\n".join(rich))
        body = extractor.text()
    return body, attachments


def safe_date(raw_date: str) -> tuple[str, str]:
    if raw_date:
        try:
            parsed = parsedate_to_datetime(raw_date)
            if parsed.tzinfo is None:
                parsed = parsed.astimezone()
            return parsed.isoformat(), parsed.strftime("%Y-%m-%d")
        except Exception:
            pass
    return "", "日付不明"


def markdown_for(message: Message, source: str) -> str:
    subject = header_text(message, "Subject") or "(件名なし)"
    sender = header_text(message, "From") or "(送信者不明)"
    to = header_text(message, "To")
    cc = header_text(message, "Cc")
    date, date_label = safe_date(header_text(message, "Date"))
    body, attachments = message_body(message)
    out = [
        f"# {subject}",
        "",
        f"- 日時: {date or date_label}",
        f"- From: {sender}",
    ]
    if to:
        out.append(f"- To: {to}")
    if cc:
        out.append(f"- Cc: {cc}")
    out.extend([f"- 元フォルダー: {source}", ""])
    if attachments:
        out.append("## 添付ファイル")
        out.extend(f"- {name}" for name in attachments)
        out.append("")
    out.extend(["## 本文", "", body or "(本文なし)", ""])
    return "\n".join(out)


def iter_mbox_files(profile: Path) -> Iterable[tuple[Path, str]]:
    for root_name in ("Mail", "ImapMail"):
        root = profile / root_name
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.name.startswith(".") or path.suffix.lower() in {".msf", ".dat", ".sqlite", ".json"}:
                continue
            # Thunderbird's default mbox folders are files without extensions;
            # skip obvious non-mail files and directories' metadata.
            if path.suffix and path.suffix.lower() not in {".eml", ".mbox"}:
                continue
            rel = path.relative_to(profile).as_posix()
            yield path, rel


def write_one(message: Message, output: Path, source: str, ordinal: int) -> None:
    date, date_label = safe_date(header_text(message, "Date"))
    subject = clean_name(header_text(message, "Subject") or "no-subject", 64)
    message_id = header_text(message, "Message-ID")
    digest_src = message_id or f"{source}:{ordinal}:{subject}"
    digest = hashlib.sha256(digest_src.encode("utf-8", errors="replace")).hexdigest()[:12]
    target_dir = output / Path(*source.split("/"))
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{date_label}_{ordinal:06d}_{subject}_{digest}.md"
    target.write_text(markdown_for(message, source), encoding="utf-8")


def export_profile(profile: Path, output: Path) -> tuple[int, int]:
    written = 0
    errors = 0
    candidates = list(iter_mbox_files(profile))
    if not candidates:
        print(f"メール保存フォルダーが見つかりません: {profile}", file=sys.stderr)
        return written, errors + 1
    for path, source in candidates:
        try:
            if path.suffix.lower() == ".eml":
                with path.open("rb") as stream:
                    message = BytesParser(policy=policy.default).parse(stream)
                write_one(message, output, source, 1)
                written += 1
                continue
            box = mailbox.mbox(path, factory=None, create=False)
            for ordinal, message in enumerate(box, start=1):
                write_one(message, output, source, ordinal)
                written += 1
            box.close()
        except (OSError, mailbox.Error, ValueError) as exc:
            errors += 1
            print(f"読み込み失敗: {path}: {exc}", file=sys.stderr)
    return written, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="ThunderbirdのローカルメールをMarkdownへ書き出します")
    parser.add_argument("--profile", type=Path, help="Thunderbirdプロファイルのフォルダー")
    parser.add_argument("--output", type=Path, default=Path.home() / "Documents" / "Thunderbird-Markdown", help="保存先 (既定: Documents/Thunderbird-Markdown)")
    args = parser.parse_args()

    profiles = [args.profile.expanduser()] if args.profile else discover_profiles()
    profiles = [p.resolve() for p in profiles if p.is_dir()]
    if not profiles:
        print("Thunderbirdプロファイルを見つけられません。--profile にプロファイルの場所を指定してください。", file=sys.stderr)
        return 2
    args.output.expanduser().mkdir(parents=True, exist_ok=True)
    total = errors = 0
    for index, profile in enumerate(profiles, start=1):
        profile_output = args.output.expanduser() / f"profile-{index}"
        print(f"読み取り: {profile}")
        count, failed = export_profile(profile, profile_output)
        total += count
        errors += failed
    print(f"完了: {total} 件を書き出しました。保存先: {args.output.expanduser().resolve()}")
    if errors:
        print(f"エラー: {errors} 件。詳細は上のメッセージを確認してください。", file=sys.stderr)
    print("添付ファイルの中身は書き出さず、ファイル名だけ記録します。")
    print("IMAPメールはThunderbirdにローカル保存されている分だけ対象になります。")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
