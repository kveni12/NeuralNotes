from __future__ import annotations

import re
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from app.models.note import RawNote

NOTES_DB = Path.home() / "Library" / "Group Containers" / "group.com.apple.notes" / "NoteStore.sqlite"


def read_apple_notes() -> list[RawNote]:
    """Read Apple Notes using the best local strategy available on this Mac."""
    if NOTES_DB.exists():
        parsed = _read_with_parser(NOTES_DB)
        if parsed:
            return parsed
        sampled = _read_sqlite_metadata(NOTES_DB)
        if sampled:
            return sampled
    return _read_with_applescript()


def _read_with_parser(path: Path) -> list[RawNote]:
    try:
        from apple_notes_parser import AppleNotesParser

        try:
            parser = AppleNotesParser(database=str(path))
        except TypeError:
            parser = AppleNotesParser()
            if hasattr(parser, "database_path"):
                parser.database_path = str(path)
        parser.load_data()
        notes = []
        for note in parser.notes.values():
            body = getattr(note, "text", None) or getattr(note, "body", "") or ""
            title = getattr(note, "title", None) or body.splitlines()[0][:80] or "Untitled"
            folder = getattr(getattr(note, "folder", None), "name", None) or "Notes"
            created = _coerce_date(getattr(note, "creation_date", None))
            updated = _coerce_date(getattr(note, "modification_date", None))
            notes.append(
                RawNote(
                    external_id=str(getattr(note, "id", title)),
                    title=title,
                    body=body,
                    folder=folder,
                    account=getattr(note, "account", "Apple Notes"),
                    tags=list(getattr(note, "tags", []) or []),
                    created_at=created,
                    updated_at=updated,
                    attachments=list(getattr(note, "attachments", []) or []),
                )
            )
        return notes
    except Exception:
        return []


def _read_sqlite_metadata(path: Path) -> list[RawNote]:
    """Last-resort metadata reader for modern NoteStore.sqlite schemas.

    Rich note bodies are compressed/protobuf data in ZICNOTEDATA on modern macOS,
    so this fallback intentionally captures titles/timestamps when the parser is
    unavailable and leaves body text minimal instead of pretending fidelity.
    """
    try:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            select
              n.ZIDENTIFIER as id,
              coalesce(n.ZTITLE, 'Untitled') as title,
              coalesce(f.ZTITLE2, f.ZNAME, 'Notes') as folder,
              n.ZCREATIONDATE1 as created,
              n.ZMODIFICATIONDATE1 as updated
            from ZICCLOUDSYNCINGOBJECT n
            left join ZICCLOUDSYNCINGOBJECT f on n.ZFOLDER = f.Z_PK
            where n.ZTITLE is not null
            order by n.ZMODIFICATIONDATE1 desc
            limit 5000
            """
        ).fetchall()
        return [
            RawNote(
                external_id=row["id"] or f"sqlite-{index}",
                title=row["title"],
                body=row["title"],
                folder=row["folder"],
                created_at=_apple_epoch(row["created"]),
                updated_at=_apple_epoch(row["updated"]),
            )
            for index, row in enumerate(rows)
        ]
    except Exception:
        return []


def _read_with_applescript() -> list[RawNote]:
    script = """
    tell application "Notes"
      set output to ""
      repeat with eachNote in notes
        set noteId to id of eachNote
        set noteName to name of eachNote
        set noteBody to plaintext of eachNote
        set modDate to modification date of eachNote
        set createDate to creation date of eachNote
        set output to output & noteId & "\t" & noteName & "\t" & (modDate as string) & "\t" & (createDate as string) & "\t" & noteBody & "\n---NEURALNOTES---\n"
      end repeat
      return output
    end tell
    """
    try:
        result = subprocess.run(["osascript", "-e", script], check=True, capture_output=True, text=True, timeout=60)
    except Exception:
        return []

    notes = []
    for block in result.stdout.split("\n---NEURALNOTES---\n"):
        parts = block.split("\t", 4)
        if len(parts) != 5:
            continue
        external_id, title, updated, created, body = parts
        notes.append(
            RawNote(
                external_id=external_id,
                title=title or body.splitlines()[0][:80] or "Untitled",
                body=body,
                folder="Notes",
                created_at=_coerce_date(created),
                updated_at=_coerce_date(updated),
            )
        )
    return notes


def _apple_epoch(value: float | int | None) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    return datetime.fromtimestamp(float(value) + 978307200, timezone.utc).isoformat()


def _coerce_date(value: object) -> str:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, str) and value.strip():
        cleaned = re.sub(r"[\u202f\u00a0]", " ", value.replace(" at ", " "))
        for pattern in (
            "%A, %B %d, %Y %I:%M:%S %p",
            "%A, %B %d, %Y %I:%M %p",
            "%B %d, %Y %I:%M:%S %p",
            "%B %d, %Y %I:%M %p",
        ):
            try:
                return datetime.strptime(cleaned, pattern).replace(tzinfo=timezone.utc).isoformat()
            except ValueError:
                pass
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            return value
    return datetime.now(timezone.utc).isoformat()
