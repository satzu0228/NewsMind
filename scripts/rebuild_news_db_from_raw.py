import argparse
import re
import sqlite3
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "newsmind.db"
RAW_DIR = BASE_DIR / "data" / "THUCNews"


def clean_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def iter_news_files(limit_per_category: int | None):
    categories = sorted(path for path in RAW_DIR.iterdir() if path.is_dir())
    for category_dir in categories:
        files = sorted(
            category_dir.glob("*.txt"),
            key=lambda path: int(path.stem) if path.stem.isdigit() else path.name,
        )
        if limit_per_category is not None:
            files = files[:limit_per_category]
        for file_path in files:
            yield category_dir.name, file_path


def reset_tables(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = OFF")
    for trigger in ["news_ai", "news_ad", "news_au"]:
        cur.execute(f"DROP TRIGGER IF EXISTS {trigger}")
    for table in ["feedback", "history", "favorites", "summaries", "news"]:
        cur.execute(f"DELETE FROM {table}")
    cur.execute("DROP TABLE IF EXISTS news_fts")
    has_sequence = cur.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'sqlite_sequence'"
    ).fetchone()
    if has_sequence:
        for table in ["feedback", "history", "favorites", "summaries", "news"]:
            cur.execute("DELETE FROM sqlite_sequence WHERE name = ?", (table,))
    cur.execute("PRAGMA foreign_keys = ON")
    conn.commit()


def create_fts(conn: sqlite3.Connection):
    try:
        conn.execute(
            "CREATE VIRTUAL TABLE news_fts USING fts5("
            "content, category, content='news', content_rowid='id', tokenize='trigram'"
            ")"
        )
        return "trigram"
    except sqlite3.OperationalError:
        conn.execute(
            "CREATE VIRTUAL TABLE news_fts USING fts5("
            "content, category, content='news', content_rowid='id'"
            ")"
        )
        return "unicode61"


def create_fts_triggers(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TRIGGER IF NOT EXISTS news_ai AFTER INSERT ON news BEGIN
          INSERT INTO news_fts(rowid, content, category)
          VALUES (new.id, new.content, new.category);
        END;
        CREATE TRIGGER IF NOT EXISTS news_ad AFTER DELETE ON news BEGIN
          INSERT INTO news_fts(news_fts, rowid, content, category)
          VALUES('delete', old.id, old.content, old.category);
        END;
        CREATE TRIGGER IF NOT EXISTS news_au AFTER UPDATE ON news BEGIN
          INSERT INTO news_fts(news_fts, rowid, content, category)
          VALUES('delete', old.id, old.content, old.category);
          INSERT INTO news_fts(rowid, content, category)
          VALUES (new.id, new.content, new.category);
        END;
    """)
    conn.commit()


def rebuild(limit_per_category: int | None, batch_size: int):
    if not RAW_DIR.exists():
        raise FileNotFoundError(f"Raw THUCNews directory not found: {RAW_DIR}")

    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA temp_store = MEMORY")
        reset_tables(conn)
        tokenizer = create_fts(conn)
        print(f"[fts] tokenizer={tokenizer}", flush=True)

        news_batch = []
        fts_batch = []
        seen = set()
        total = 0
        skipped = 0
        now = datetime.now().isoformat(sep=" ", timespec="seconds")
        cur = conn.cursor()

        news_sql = """
            INSERT INTO news (category, content, tokenized, length, token_length, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        fts_sql = "INSERT INTO news_fts(rowid, content, category) VALUES (?, ?, ?)"

        for category, file_path in iter_news_files(limit_per_category):
            try:
                content = clean_text(file_path.read_text(encoding="utf-8", errors="replace"))
            except OSError as exc:
                skipped += 1
                print(f"[skip] {file_path}: {exc}", flush=True)
                continue

            if len(content) < 20:
                skipped += 1
                continue

            fingerprint = content[:200]
            if fingerprint in seen:
                skipped += 1
                continue
            seen.add(fingerprint)

            news_batch.append((category, content, "", len(content), 0, now))

            if len(news_batch) >= batch_size:
                cur.executemany(news_sql, news_batch)
                last_id = cur.execute("SELECT last_insert_rowid()").fetchone()[0]
                start_id = last_id - len(news_batch) + 1
                fts_batch = [
                    (start_id + index, item[1], item[0])
                    for index, item in enumerate(news_batch)
                ]
                cur.executemany(fts_sql, fts_batch)
                conn.commit()
                total += len(news_batch)
                news_batch.clear()
                print(f"[import] total={total}, skipped={skipped}", flush=True)

        if news_batch:
            cur.executemany(news_sql, news_batch)
            last_id = cur.execute("SELECT last_insert_rowid()").fetchone()[0]
            start_id = last_id - len(news_batch) + 1
            fts_batch = [
                (start_id + index, item[1], item[0])
                for index, item in enumerate(news_batch)
            ]
            cur.executemany(fts_sql, fts_batch)
            conn.commit()
            total += len(news_batch)

        conn.execute("INSERT INTO news_fts(news_fts) VALUES ('optimize')")
        create_fts_triggers(conn)
        conn.commit()
        print(f"[done] news={total}, skipped={skipped}, db={DB_PATH}", flush=True)
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit-per-category", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=1000)
    args = parser.parse_args()
    rebuild(args.limit_per_category, args.batch_size)


if __name__ == "__main__":
    main()
