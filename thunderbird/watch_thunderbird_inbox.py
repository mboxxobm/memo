#!/usr/bin/env python3
"""Watch selected local Thunderbird Inboxes without using credentials."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import mailbox
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from email.message import Message
from pathlib import Path

from thunderbird_to_markdown import markdown_for


def read_prefs(path: Path) -> dict[str, object]:
    prefs: dict[str, object] = {}
    pattern = re.compile(r'^\s*user_pref\("([^"\\]*(?:\\.[^"\\]*)*)",\s*(.*?)\);\s*$')
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = pattern.match(line)
        if not match:
            continue
        key = match.group(1)
        raw = match.group(2).strip()
        try:
            value = ast.literal_eval(raw)
        except (ValueError, SyntaxError):
            value = raw
        prefs[key] = value
    return prefs


def discover_profiles() -> list[Path]:
    home = Path.home()
    roots = [home / "Library" / "Thunderbird", home / ".thunderbird", home / ".mozilla-thunderbird"]
    appdata = os.environ.get("APPDATA")
    if appdata:
        roots.insert(0, Path(appdata) / "Thunderbird")
    found: list[Path] = []
    for root in roots:
        ini = root / "profiles.ini"
        if not ini.is_file():
            continue
        section = None
        vals: dict[str, dict[str, str]] = {}
        for line in ini.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            match = re.match(r"\[(Profile\d+)\]", line)
            if match:
                section = match.group(1)
                vals[section] = {}
            elif section and "=" in line:
                k, v = line.split("=", 1)
                vals[section][k.strip()] = v.strip()
        for info in vals.values():
            profile_path = info.get("Path")
            if not profile_path:
                continue
            profile = root / profile_path if info.get("IsRelative", "1") == "1" else Path(profile_path)
            if profile.is_dir() and profile not in found:
                found.append(profile)
    return found


def account_mailboxes(profile: Path, target_address: str, target_host: str | None = None) -> list[Path]:
    prefs_path = profile / "prefs.js"
    if not prefs_path.is_file():
        return []
    prefs = read_prefs(prefs_path)
    server_ids = set()
    for key, val in prefs.items():
        match = re.fullmatch(r"mail\.server\.(server\d+)\.hostname", key)
        if match and isinstance(val, str) and (target_host is None or val.lower() == target_host.lower()):
            sid = match.group(1)
            username = prefs.get(f"mail.server.{sid}.userName", "")
            if str(username).lower() == target_address.lower():
                server_ids.add(sid)
    if not server_ids:
        return []

    preferred: list[Path] = []
    for sid in server_ids:
        for key in (f"mail.server.{sid}.directory", f"mail.server.{sid}.directory-rel"):
            value = prefs.get(key)
            if not isinstance(value, str) or not value:
                continue
            if value.startswith("[ProfD]"):
                directory = profile / value.removeprefix("[ProfD]").lstrip("/\\")
            else:
                directory = Path(value)
                if not directory.is_absolute():
                    directory = profile / directory
            preferred.extend((directory / "INBOX", directory / "Inbox"))

    # Prefer Thunderbird's account-specific storage path. This matters when
    # one profile has many mailboxes on the same server, or an old server path.
    existing = [p for p in preferred if p.is_file() and not p.name.endswith(".msf")]
    unique: list[Path] = []
    for path in existing:
        if not any(os.path.samefile(path, item) for item in unique):
            unique.append(path)
    return sorted(unique)


def all_account_mailboxes(profile: Path) -> dict[str, list[Path]]:
    """Return every configured email account with a locally stored Inbox."""
    prefs_path = profile / "prefs.js"
    if not prefs_path.is_file():
        return {}
    prefs = read_prefs(prefs_path)
    result: dict[str, list[Path]] = {}
    for key, username in prefs.items():
        match = re.fullmatch(r"mail\.server\.(server\d+)\.userName", key)
        if not match or not isinstance(username, str) or "@" not in username:
            continue
        sid = match.group(1)
        address = username.strip().lower()
        inboxes: list[Path] = []
        for pref_key in (f"mail.server.{sid}.directory", f"mail.server.{sid}.directory-rel"):
            value = prefs.get(pref_key)
            if not isinstance(value, str) or not value:
                continue
            if value.startswith("[ProfD]"):
                directory = profile / value.removeprefix("[ProfD]").lstrip("/\\")
            else:
                directory = Path(value)
                if not directory.is_absolute():
                    directory = profile / directory
            for name in ("INBOX", "Inbox"):
                candidate = directory / name
                if candidate.is_file() and not candidate.name.endswith(".msf"):
                    try:
                        if not any(os.path.samefile(candidate, existing) for existing in inboxes):
                            inboxes.append(candidate)
                    except OSError:
                        continue
        if inboxes:
            result.setdefault(address, []).extend(inboxes)
        else:
            result.setdefault(address, [])
    return result


def message_key(message: Message) -> str:
    msg_id = str(message.get("Message-ID", "")).strip()
    if msg_id:
        return hashlib.sha256(msg_id.encode("utf-8", errors="replace")).hexdigest()
    fallback = "\0".join(str(message.get(name, "")) for name in ("From", "Date", "To", "Subject"))
    return hashlib.sha256(fallback.encode("utf-8", errors="replace")).hexdigest()


def read_inbox(path: Path) -> list[tuple[str, Message]]:
    rows: list[tuple[str, Message]] = []
    box = mailbox.mbox(path, create=False)
    try:
        for message in box:
            rows.append((message_key(message), message))
    finally:
        box.close()
    return rows


def notify(subject: str) -> None:
    if sys.platform != "darwin":
        return
    safe_subject = subject.replace("\\", "\\\\").replace('"', '\\"')[:160]
    script = f'display notification "新着メールがあります" with title "{safe_subject}"'
    subprocess.run(["osascript", "-e", script], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def export_new(message: Message, key: str, source: str, output: Path, address: str) -> Path:
    now = datetime.now().astimezone()
    subject = str(message.get("Subject", "メール"))
    subject = re.sub(r"[\\/:*?\"<>|\r\n]+", "_", subject).strip(" ._")[:60] or "メール"
    account_dir = re.sub(r"[^a-zA-Z0-9@._+-]", "_", address)
    target = output / "new" / account_dir / f"{now:%Y%m%d-%H%M%S}_{key[:12]}_{subject}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown_for(message, source), encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Thunderbird内の指定受信箱をローカルで監視します")
    parser.add_argument("--profile", type=Path, help="Thunderbirdプロファイル。省略時は自動検索")
    parser.add_argument("--output", type=Path, default=Path.home() / "Documents" / "Thunderbird-Markdown", help="新着メールのMarkdown保存先")
    parser.add_argument("--accounts", default="", help="監視するメールアドレスをカンマ区切りで指定")
    parser.add_argument("--host", help="指定アカウントの検索時に使うメールサーバー名で絞り込む")
    parser.add_argument("--all-accounts", action="store_true", help="Thunderbirdに設定され、ローカル受信箱が読める全アドレスを監視")
    parser.add_argument("--interval", type=int, default=60, help="確認間隔（秒、既定: 60）")
    parser.add_argument("--notify", action="store_true", help="macOS通知センターにも新着を表示")
    parser.add_argument("--include-existing", action="store_true", help="初回起動時に現在の受信箱も書き出す")
    args = parser.parse_args()
    if args.interval < 10:
        parser.error("--interval は10秒以上にしてください")

    profiles = [args.profile.expanduser()] if args.profile else discover_profiles()
    profiles = [p.resolve() for p in profiles if p.is_dir()]
    addresses = [value.strip().lower() for value in args.accounts.split(",") if value.strip()]
    if not args.all_accounts and not addresses:
        parser.error("--accounts または --all-accounts を指定してください")
    matches: dict[str, tuple[Path, Path]] = {}
    missing: list[str] = []
    all_inboxes: dict[tuple[str, str], list[Path]] = {}
    if args.all_accounts:
        for profile in profiles:
            for address, inboxes in all_account_mailboxes(profile).items():
                all_inboxes.setdefault((str(profile), address), []).extend(inboxes)
        addresses = sorted({address for _, address in all_inboxes})
    for address in addresses:
        if args.all_accounts:
            found = [
                (Path(profile), path)
                for (profile, candidate_address), paths in all_inboxes.items()
                if candidate_address == address
                for path in paths
            ]
        else:
            found = [(profile, path) for profile in profiles for path in account_mailboxes(profile, address, args.host)]
        if len(found) == 1:
            matches[address] = found[0]
        elif not found:
            missing.append(address)
        else:
            print(f"{address} の受信箱が複数見つかりました。--profile でプロファイルを指定してください。", file=sys.stderr)
            for profile, path in found:
                print(f"{profile}: {path}", file=sys.stderr)
            return 2
    if not matches:
        print("指定されたメールアドレスのローカル受信箱が見つかりません。Thunderbirdで同期済みか確認してください。", file=sys.stderr)
        return 2

    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    state_path = output / ".mail-watch-state.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        saved_seen = state.get("seen_by_inbox", {})
        if not isinstance(saved_seen, dict):
            saved_seen = {}
    except (OSError, ValueError, TypeError):
        saved_seen = {}

    seen_by_inbox: dict[str, set[str]] = {}
    last_signatures: dict[str, tuple[int, int] | None] = {}
    for address, (_, inbox) in matches.items():
        inbox_key = str(inbox)
        existed = inbox_key in saved_seen and isinstance(saved_seen[inbox_key], list)
        seen = set(saved_seen.get(inbox_key, [])) if existed else set()
        print(f"監視中: {address} / {inbox}")
        if not existed and not args.include_existing:
            current = read_inbox(inbox)
            seen.update(key for key, _ in current)
            print(f"初回登録: {address} の既存メール {len(current)} 件を記録しました。")
        seen_by_inbox[inbox_key] = seen
        stat = inbox.stat()
        last_signatures[inbox_key] = None if not existed and args.include_existing else (stat.st_mtime_ns, stat.st_size)

    if missing:
        print("Thunderbird内で見つからなかったアドレス: " + ", ".join(missing), file=sys.stderr)
    print(f"新着Markdown: {output / 'new'}")

    while True:
        try:
            for address, (_, inbox) in matches.items():
                inbox_key = str(inbox)
                stat = inbox.stat()
                signature = (stat.st_mtime_ns, stat.st_size)
                current = read_inbox(inbox) if signature != last_signatures[inbox_key] else []
                last_signatures[inbox_key] = signature
                seen = seen_by_inbox[inbox_key]
                new_items = [(key, msg) for key, msg in current if key not in seen]
                for key, message in new_items:
                    key = hashlib.sha256(f"{address}\0{key}".encode()).hexdigest()
                    saved = export_new(message, key, str(inbox), output, address)
                    subject = str(message.get("Subject", "(件名なし)"))
                    print(f"新着: {address} / {subject} -> {saved}", flush=True)
                    if args.notify:
                        notify(subject)
                    seen.add(message_key(message))
            state_path.write_text(json.dumps({"seen_by_inbox": {path: sorted(seen) for path, seen in seen_by_inbox.items()}}, ensure_ascii=False), encoding="utf-8")
            time.sleep(args.interval)
        except KeyboardInterrupt:
            print("監視を終了しました。")
            return 0
        except (OSError, mailbox.Error) as exc:
            print(f"受信箱の読み取りエラー: {exc}", file=sys.stderr, flush=True)
            time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
