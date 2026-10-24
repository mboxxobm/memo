#!/usr/bin/env python3
"""Build a local Markdown index of interview/meeting emails for chosen accounts."""

from __future__ import annotations

import argparse
import hashlib
import mailbox
import re
import sys
from email.message import Message
from pathlib import Path

from thunderbird_to_markdown import discover_profiles, header_text, message_body, safe_date
from watch_thunderbird_inbox import account_mailboxes


TERMS = re.compile(r"面談|面接|予約|日程調整|候補日|打合せ|打ち合わせ|ミーティング|meeting|interview", re.I)
DETAIL_TERMS = re.compile(r"日時|日程|候補|予定|予約|面談|面接|会場|場所|URL|Zoom|Teams|Meet|時間|時|月|日", re.I)
DATE_TIME = re.compile(
    r"(?:20\d{2}[年/.-]\s*\d{1,2}[月/.-]\s*\d{1,2}日?)|"
    r"(?:\d{1,2}月\s*\d{1,2}日)|(?:\d{1,2}/\d{1,2})|"
    r"(?:午前|午後)?\s*\d{1,2}(?:[:：時]\s*\d{1,2}分?)"
)


def account_root(profile: Path, address: str, target_host: str | None = None) -> Path | None:
    inboxes = account_mailboxes(profile, address, target_host)
    if len(inboxes) == 1:
        return inboxes[0].parent
    return None


def mail_files(root: Path) -> list[Path]:
    result = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        if path.suffix.lower() in {".msf", ".dat", ".sqlite", ".json", ".lock", ".tmp"}:
            continue
        if path.suffix and path.suffix.lower() not in {".eml", ".mbox"}:
            continue
        result.append(path)
    return result


def read_box(path: Path):
    try:
        box = mailbox.mbox(path, create=False)
        try:
            for message in box:
                yield message
        finally:
            box.close()
    except (OSError, mailbox.Error, ValueError):
        return


def details_excerpt(body: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in body.splitlines()]
    lines = [line for line in lines if line and DETAIL_TERMS.search(line)]
    unique = list(dict.fromkeys(lines))
    return "\n".join(f"> {line[:400]}" for line in unique[:10]) or "> (日時・内容の行を特定できませんでした)"


def main() -> int:
    parser = argparse.ArgumentParser(description="Thunderbirdから面談・予約メールを探してMarkdown一覧を作ります")
    parser.add_argument("--profile", type=Path, help="Thunderbirdプロファイル。省略時は自動検索")
    parser.add_argument("--accounts", required=True, help="検索するメールアドレスをカンマ区切りで指定")
    parser.add_argument("--host", help="指定アカウントの検索時に使うメールサーバー名で絞り込む")
    parser.add_argument("--output", type=Path, default=Path.home() / "Documents" / "Thunderbird-Markdown" / "面談一覧.md", help="一覧の保存先")
    args = parser.parse_args()
    profiles = [args.profile.expanduser()] if args.profile else discover_profiles()
    profiles = [p.resolve() for p in profiles if p.is_dir()]
    addresses = [a.strip().lower() for a in args.accounts.split(",") if a.strip()]

    rows: list[tuple[str, str, Message, str, str]] = []
    missing: list[str] = []
    seen: set[str] = set()
    for address in addresses:
        roots = [root for profile in profiles if (root := account_root(profile, address, args.host)) is not None]
        if len(roots) != 1:
            missing.append(address)
            continue
        root = roots[0]
        for path in mail_files(root):
            for message in read_box(path):
                body, _ = message_body(message)
                subject = header_text(message, "Subject") or "(件名なし)"
                if not TERMS.search(subject + "\n" + body):
                    continue
                mid = header_text(message, "Message-ID")
                identity = mid or f"{path}:{subject}:{header_text(message, 'Date')}"
                digest = hashlib.sha256(identity.encode("utf-8", errors="replace")).hexdigest()
                if digest in seen:
                    continue
                seen.add(digest)
                folder = path.relative_to(root).as_posix()
                rows.append((address, folder, message, body, details_excerpt(body)))

    rows.sort(key=lambda item: header_text(item[2], "Date"), reverse=True)
    out = ["# 面談・面接・予約メール一覧", "", f"検索対象: {', '.join(addresses)}", f"候補メール: {len(rows)} 件", ""]
    if missing:
        out.extend(["対象メールボックスが見つからなかったアドレス:", "", *[f"- {a}" for a in missing], ""])
    if not rows:
        out.extend(["該当メールは見つかりませんでした。", ""])
    for index, (address, folder, message, body, excerpt) in enumerate(rows, start=1):
        date, _ = safe_date(header_text(message, "Date"))
        subject = header_text(message, "Subject") or "(件名なし)"
        out.extend([
            f"## {index}. {subject}",
            "",
            f"- 受信アカウント: {address}",
            f"- メール日時: {date or header_text(message, 'Date') or '不明'}",
            f"- 送信者: {header_text(message, 'From') or '不明'}",
            f"- 保存フォルダー: {folder}",
            "",
            "### 面談日時・内容の候補行",
            "",
            excerpt,
            "",
        ])
    output = args.output.expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(out), encoding="utf-8")
    print(f"候補メール {len(rows)} 件を {output.resolve()} に保存しました。")
    if missing:
        print("見つからなかったメールボックス: " + ", ".join(missing), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
