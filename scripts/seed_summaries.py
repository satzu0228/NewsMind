# ============================================
# 文件名: scripts/seed_summaries.py
# 功能: 复制精选新闻到列表顶部 + 写入高质量摘要
# 用法: python scripts/seed_summaries.py
# ============================================

import json
import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "newsmind.db"
JSON_PATH = Path(__file__).resolve().parent / "demo_summaries.json"


def seed():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    print("=" * 55)
    print("  复制精选新闻并写入摘要")
    print("=" * 55)

    new_ids = {}

    for item in data:
        cat = item["category"]
        old_id = item["old_id"]

        # 读取原始文章内容
        cur.execute("SELECT content FROM news WHERE id=?", (old_id,))
        row = cur.fetchone()
        if not row:
            print(f"  [跳过] {cat}: 原始ID={old_id} 不存在")
            continue
        content = row[0]

        # 创建新记录（自动获得大ID，排在列表前面）
        cur.execute(
            "INSERT INTO news (category, content, length, created_at) VALUES (?, ?, ?, ?)",
            (cat, content, len(content), datetime.now()),
        )
        new_id = cur.lastrowid
        new_ids[cat] = new_id

        # 插入摘要
        cur.execute(
            "INSERT INTO summaries (news_id, extractive_summary, abstractive_summary, inference_time, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                new_id,
                item["extractive"],
                item["abstractive"],
                item["inference_time"],
                datetime.now(),
            ),
        )

        print(
            f"  [OK] {cat} | 新ID={new_id} | "
            f"抽取式{len(item['extractive'])}字 "
            f"生成式{len(item['abstractive'])}字"
        )

    conn.commit()

    # 验证
    print(f"\n{'=' * 55}")
    print("  验证")
    print(f"{'=' * 55}")
    for cat, nid in new_ids.items():
        cur.execute(
            "SELECT extractive_summary, abstractive_summary, inference_time FROM summaries WHERE news_id=?",
            (nid,),
        )
        r = cur.fetchone()
        if r:
            print(f"  {cat} (ID={nid}): OK | 耗时={r[2]}s")

    conn.close()
    print(f"\nDone! 共 {len(new_ids)} 篇新闻 + 摘要，排在列表最前面")


if __name__ == "__main__":
    seed()
