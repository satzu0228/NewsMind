# ============================================
# 文件名: scripts/import_data_fast.py
# 功能: 快速导入预处理数据到 SQLite（批量去重，不走 API）
# 用法: python scripts/import_data_fast.py
# ============================================

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database import SessionLocal, init_db
from backend.models.models import News

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"


def main():
    init_db()
    db = SessionLocal()

    # 先查出库里已有的去重指纹（前100字）
    existing = set()
    for row in db.query(News.content).all():
        text = (row[0] or "")[:100]
        if text:
            existing.add(text)

    print(f"已有 {len(existing)} 条记录，跳过重复")

    total = 0
    for filename in ["train.json", "val.json", "test.json"]:
        filepath = PROCESSED_DIR / filename
        if not filepath.exists():
            print(f"[!] 未找到: {filepath}，跳过")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        batch = []
        for item in data:
            preview = (item.get("content", "") or "")[:100]
            if preview in existing:
                continue
            existing.add(preview)
            batch.append(News(
                category=item.get("category", "未知"),
                content=item.get("content", ""),
                tokenized=item.get("tokenized", ""),
                length=item.get("length", 0),
                token_length=item.get("token_length", 0),
            ))

        if batch:
            db.bulk_save_objects(batch)
            db.commit()
            total += len(batch)

        print(f"[OK] {filename}: 新增 {len(batch)} 条")

    db.close()
    print(f"\n[DONE] 共导入 {total} 条新闻")


if __name__ == "__main__":
    main()
