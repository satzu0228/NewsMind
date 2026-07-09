# ============================================
# 文件名: backend/ai/train.py
# 功能: 训练新闻摘要模型
# 流程: 加载数据 → TextRank生成伪标签 → 微调T5 → ROUGE-L评估 → 保存模型
# 用法: python -m backend.ai.train
# ============================================

import json
import time
import random
import warnings
from pathlib import Path
from typing import List, Optional

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from transformers import (
    AutoTokenizer,
    T5ForConditionalGeneration,
    get_linear_schedule_with_warmup,
)

from .config import (
    DEVICE, USE_AMP,
    T5_MODEL_NAME, T5_MAX_INPUT_LENGTH, T5_MAX_TARGET_LENGTH,
    BATCH_SIZE, LEARNING_RATE, NUM_EPOCHS, WARMUP_STEPS,
    MAX_GRAD_NORM, WEIGHT_DECAY, SAVE_STEPS, EVAL_STEPS, LOGGING_STEPS,
    CPU_MAX_TRAIN_SAMPLES, CPU_NUM_EPOCHS,
    ROUGE_L_THRESHOLD, PROCESSED_DIR, MODEL_DIR,
)
from .summarizer import (
    clean_text, split_sentences,
    BertEncoder, TextRank, rouge_l_score,
)

warnings.filterwarnings('ignore')

# ============================================
# 1. 数据集类
# ============================================

class SummarizationDataset(Dataset):
    """
    新闻摘要数据集
    输入: 新闻原文
    目标: TextRank 提取的关键句（作为伪标签）
    """

    def __init__(self,
                 data: List[dict],
                 tokenizer: AutoTokenizer,
                 max_input_length: int = T5_MAX_INPUT_LENGTH,
                 max_target_length: int = T5_MAX_TARGET_LENGTH):
        """
        参数:
            data: 预处理后的数据列表 [{"content": ..., "category": ...}, ...]
            tokenizer: T5 分词器
            max_input_length: 输入最大长度
            max_target_length: 目标最大长度
        """
        self.data = data
        self.tokenizer = tokenizer
        self.max_input_length = max_input_length
        self.max_target_length = max_target_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        content = item.get("content", "")

        # 截断过长文本
        if len(content) > self.max_input_length * 4:
            content = content[:self.max_input_length * 4]

        # 构建输入（T5 格式）
        input_text = f"summarize: {content}"

        # 目标摘要（来自 TextRank 预计算或 item 中已存）
        target_text = item.get("summary", "")
        if not target_text:
            # 如果没有预计算摘要，用原文前几句作为fallback
            sentences = split_sentences(clean_text(content))
            target_text = "。".join(sentences[:3]) + "。" if sentences else content[:200]

        # 编码输入
        input_enc = self.tokenizer(
            input_text,
            max_length=self.max_input_length,
            truncation=True,
            padding="max_length",
            return_tensors="pt"
        )

        # 编码目标
        target_enc = self.tokenizer(
            target_text,
            max_length=self.max_target_length,
            truncation=True,
            padding="max_length",
            return_tensors="pt"
        )

        # 将 pad_token 的 label 设为 -100（忽略损失计算）
        labels = target_enc.input_ids.squeeze(0)
        labels[labels == self.tokenizer.pad_token_id] = -100

        return {
            "input_ids": input_enc.input_ids.squeeze(0),
            "attention_mask": input_enc.attention_mask.squeeze(0),
            "labels": labels,
        }


# ============================================
# 2. 伪标签生成（TextRank）
# ============================================

def generate_pseudo_labels(data: List[dict],
                           bert_encoder: BertEncoder,
                           top_k: int = 5,
                           save_path: Optional[Path] = None) -> List[dict]:
    """
    使用 BERT + TextRank 为每条新闻生成伪标签摘要
    参数:
        data: 新闻数据列表
        bert_encoder: BERT 编码器
        top_k: 关键句数量
        save_path: 保存路径（可选），避免重复计算
    返回:
        添加了 "summary" 字段的数据列表
    """
    textrank = TextRank()

    print(f"\n[*] 为 {len(data)} 条数据生成 TextRank 伪标签...")
    print(f"    这可能需要一些时间（CPU上约每秒处理1-3条）...")

    for i, item in enumerate(data):
        if (i + 1) % 100 == 0:
            print(f"  进度: {i + 1}/{len(data)}")

        content = item.get("content", "")
        cleaned = clean_text(content)

        if len(cleaned) < 20:
            item["summary"] = cleaned
            continue

        # 分句
        sentences = split_sentences(cleaned)
        if not sentences:
            item["summary"] = cleaned[:200]
            continue

        # BERT 编码
        embeddings = bert_encoder.encode_sentences(sentences)

        # TextRank 提取关键句
        ranked = textrank.extract(sentences, embeddings, top_k=top_k)

        # 拼接关键句作为伪标签
        summary = "。".join([s for s, _, _ in ranked]) + "。"
        item["summary"] = summary

    print(f"[✓] 伪标签生成完成!")

    # 缓存
    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[✓] 伪标签已缓存: {save_path}")

    return data


# ============================================
# 3. 训练函数
# ============================================

def train_epoch(model, dataloader, optimizer, scheduler, scaler=None):
    """训练一个 epoch"""
    model.train()
    total_loss = 0
    start_time = time.time()

    for step, batch in enumerate(dataloader):
        # 将数据移到设备
        input_ids = batch["input_ids"].to(DEVICE)
        attention_mask = batch["attention_mask"].to(DEVICE)
        labels = batch["labels"].to(DEVICE)

        # 前向传播
        if USE_AMP and scaler is not None:
            with torch.amp.autocast('cuda'):
                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels,
                )
                loss = outputs.loss
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), MAX_GRAD_NORM)
            scaler.step(optimizer)
            scaler.update()
        else:
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels,
            )
            loss = outputs.loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), MAX_GRAD_NORM)
            optimizer.step()

        scheduler.step()
        optimizer.zero_grad()

        total_loss += loss.item()

        # 打印日志
        if (step + 1) % LOGGING_STEPS == 0:
            avg_loss = total_loss / (step + 1)
            elapsed = time.time() - start_time
            print(f"    Step {step + 1}/{len(dataloader)} | "
                  f"Loss: {avg_loss:.4f} | "
                  f"Time: {elapsed:.0f}s")

    avg_loss = total_loss / len(dataloader)
    return avg_loss


def evaluate(model, dataloader, tokenizer) -> dict:
    """在验证集上评估 ROUGE-L"""
    model.eval()
    predictions = []
    references = []

    print("\n[*] 评估 ROUGE-L ...")
    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch["input_ids"].to(DEVICE)
            attention_mask = batch["attention_mask"].to(DEVICE)
            labels = batch["labels"]

            # 生成摘要
            outputs = model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_length=T5_MAX_TARGET_LENGTH,
                num_beams=4,
                early_stopping=True,
            )

            # 解码
            for i, output in enumerate(outputs):
                pred = tokenizer.decode(output, skip_special_tokens=True)

                # 处理 labels（去掉 -100）
                label_ids = labels[i][labels[i] != -100]
                ref = tokenizer.decode(label_ids, skip_special_tokens=True)

                predictions.append(pred)
                references.append(ref)

    # 计算 ROUGE-L
    scores = []
    for pred, ref in zip(predictions, references):
        score = rouge_l_score(ref, pred)
        scores.append(score)

    avg_rouge = np.mean(scores) if scores else 0

    # 打印几个示例
    print(f"\n  评估结果 ({len(scores)} 条):")
    print(f"    平均 ROUGE-L: {avg_rouge:.4f}")
    print(f"    最高分: {max(scores):.4f}" if scores else "")
    print(f"    达标率(≥0.4): {np.mean(np.array(scores) >= 0.4) * 100:.1f}%")

    if predictions and references:
        print(f"\n  --- 示例 ---")
        print(f"  参考: {references[0][:100]}...")
        print(f"  生成: {predictions[0][:100]}...")

    return {
        "avg_rouge_l": round(float(avg_rouge), 4),
        "predictions": predictions[:3],
        "references": references[:3],
    }


# ============================================
# 4. 主训练流程
# ============================================

def main():
    """主训练流程"""
    print("=" * 60)
    print(" NewsMind - 摘要模型训练")
    print("=" * 60)
    print(f"  设备: {DEVICE}")
    print(f"  模型: {T5_MODEL_NAME}")
    print(f"  批次大小: {BATCH_SIZE}")
    print(f"  学习率: {LEARNING_RATE}")
    num_epochs = CPU_NUM_EPOCHS if DEVICE.type != "cuda" else NUM_EPOCHS
    print(f"  训练轮数: {num_epochs}")
    print("=" * 60)

    # ========== 步骤1: 加载数据 ==========
    print("\n[步骤1/5] 加载预处理数据...")
    train_file = PROCESSED_DIR / "train.json"
    val_file = PROCESSED_DIR / "val.json"

    if not train_file.exists():
        print(f"[✗] 训练数据未找到: {train_file}")
        print("    请先运行 data_preprocess.py")
        return

    with open(train_file, 'r', encoding='utf-8') as f:
        train_data = json.load(f)
    print(f"[✓] 训练集: {len(train_data)} 条")

    val_data = []
    if val_file.exists():
        with open(val_file, 'r', encoding='utf-8') as f:
            val_data = json.load(f)
        print(f"[✓] 验证集: {len(val_data)} 条")

    # CPU 模式限制数据量
    if DEVICE.type != "cuda":
        n_train = min(len(train_data), CPU_MAX_TRAIN_SAMPLES)
        n_val = min(len(val_data), CPU_MAX_TRAIN_SAMPLES // 5)
        print(f"[!] CPU 模式，训练集限制: {n_train} 条")
        train_data = train_data[:n_train]
        val_data = val_data[:n_val]

    # ========== 步骤2: 生成伪标签 ==========
    print("\n[步骤2/5] 生成 TextRank 伪标签...")
    pseudo_labels_file = PROCESSED_DIR / "train_with_summaries.json"

    if pseudo_labels_file.exists():
        print("[*] 发现已缓存的伪标签，直接加载...")
        with open(pseudo_labels_file, 'r', encoding='utf-8') as f:
            train_data = json.load(f)
        print(f"[✓] 加载完成: {len(train_data)} 条")
    else:
        print("[*] 加载 BERT 编码器（用于 TextRank）...")
        bert = BertEncoder()
        train_data = generate_pseudo_labels(
            train_data, bert,
            top_k=5,
            save_path=pseudo_labels_file,
        )
        # 清理 BERT 以释放内存（T5 训练不需要 BERT）
        del bert
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print("[✓] BERT 已释放")

    # 为验证集生成伪标签
    if val_data:
        val_pseudo_file = PROCESSED_DIR / "val_with_summaries.json"
        if not val_pseudo_file.exists():
            print("[*] 为验证集生成伪标签...")
            bert = BertEncoder()
            val_data = generate_pseudo_labels(val_data, bert, top_k=5,
                                               save_path=val_pseudo_file)
            del bert
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        else:
            with open(val_pseudo_file, 'r', encoding='utf-8') as f:
                val_data = json.load(f)

    # ========== 步骤3: 初始化模型 ==========
    print("\n[步骤3/5] 初始化 T5 模型...")
    tokenizer = AutoTokenizer.from_pretrained(T5_MODEL_NAME)
    model = T5ForConditionalGeneration.from_pretrained(T5_MODEL_NAME).to(DEVICE)

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        model.config.pad_token_id = model.config.eos_token_id

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[✓] 总参数: {total_params:,}")
    print(f"[✓] 可训练参数: {trainable_params:,}")

    # ========== 步骤4: 训练 ==========
    print("\n[步骤4/5] 开始训练...")

    # DataLoader
    train_dataset = SummarizationDataset(train_data, tokenizer)
    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0,  # Windows 兼容
    )

    val_loader = None
    if val_data:
        val_dataset = SummarizationDataset(val_data[:500], tokenizer)  # 验证只用500条
        val_loader = DataLoader(
            val_dataset,
            batch_size=BATCH_SIZE,
            shuffle=False,
            num_workers=0,
        )

    # 优化器和调度器
    optimizer = AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    total_steps = len(train_loader) * num_epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=min(WARMUP_STEPS, total_steps // 10),
        num_training_steps=total_steps,
    )

    # 混合精度
    scaler = torch.amp.GradScaler('cuda') if USE_AMP else None

    best_rouge = 0.0
    best_model_path = MODEL_DIR / "t5_summarizer_best"

    for epoch in range(num_epochs):
        print(f"\n{'='*40}")
        print(f" Epoch {epoch + 1}/{num_epochs}")
        print(f"{'='*40}")

        # 训练
        train_loss = train_epoch(model, train_loader, optimizer, scheduler, scaler)
        print(f"\n  Epoch {epoch + 1} 训练完成 | 平均 Loss: {train_loss:.4f}")

        # 评估
        if val_loader:
            eval_results = evaluate(model, val_loader, tokenizer)
            rouge = eval_results["avg_rouge_l"]
            print(f"  ROUGE-L: {rouge:.4f} (最佳: {best_rouge:.4f})")

            # 保存最佳模型
            if rouge > best_rouge:
                best_rouge = rouge
                best_model_path.mkdir(parents=True, exist_ok=True)
                model.save_pretrained(str(best_model_path))
                tokenizer.save_pretrained(str(best_model_path))
                print(f"  [✓] 新最佳模型已保存: {best_model_path}")

    # 训练结束
    if best_rouge == 0.0:
        # 没有验证集，直接保存最终模型
        best_model_path.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(str(best_model_path))
        tokenizer.save_pretrained(str(best_model_path))
        print(f"\n[✓] 最终模型已保存: {best_model_path}")

    # ========== 步骤5: 最终评估 ==========
    print("\n[步骤5/5] 最终评估...")

    # 加载测试集
    test_file = PROCESSED_DIR / "test.json"
    if test_file.exists():
        with open(test_file, 'r', encoding='utf-8') as f:
            test_data = json.load(f)

        # 限制测试量
        n_test = min(len(test_data), 200)
        test_data = test_data[:n_test]

        # 生成伪标签作为参考
        print(f"[*] 为测试集生成参考摘要...")
        bert = BertEncoder()
        test_data_with_labels = generate_pseudo_labels(
            test_data, bert, top_k=5,
            save_path=PROCESSED_DIR / "test_with_summaries.json",
        )
        del bert
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        # 评估
        test_dataset = SummarizationDataset(test_data_with_labels, tokenizer)
        test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)
        test_results = evaluate(model, test_loader, tokenizer)

        print(f"\n{'='*60}")
        print(f" 最终测试结果")
        print(f"{'='*60}")
        print(f"  ROUGE-L: {test_results['avg_rouge_l']:.4f}")
        print(f"  目标: ≥ {ROUGE_L_THRESHOLD}")
        if test_results['avg_rouge_l'] >= ROUGE_L_THRESHOLD:
            print(f"  [✓] 达标！")
        else:
            print(f"  [!] 未达标，可能需要更多训练数据或更大模型")

    # 清理
    model.eval()
    torch.cuda.empty_cache() if torch.cuda.is_available() else None

    print(f"\n{'='*60}")
    print(f" 训练完成!")
    print(f"{'='*60}")
    print(f"  模型路径: {best_model_path}")
    print(f"  最佳 ROUGE-L: {best_rouge:.4f}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
