# ============================================
# 文件名: backend/ai/predict.py
# 功能: 新闻摘要预测/推理
# 用法:
#   单条预测:  python -m backend.ai.predict --text "新闻正文..."
#   文件预测:  python -m backend.ai.predict --file input.json
#   交互模式:  python -m backend.ai.predict --interactive
#   评估模式:  python -m backend.ai.predict --eval test.json
# ============================================

import json
import time
import argparse
import sys
from pathlib import Path
from typing import List, Optional

import numpy as np

from .config import (
    DEVICE, TEXTRANK_TOP_K, ROUGE_L_THRESHOLD,
    MAX_INFERENCE_TIME, PROCESSED_DIR, MODEL_DIR,
)
from .summarizer import (
    clean_text, NewsSummarizer, BertEncoder, T5Summarizer,
    rouge_l_score, evaluate_rouge,
)


# ============================================
# 1. 加载模型
# ============================================

def load_summarizer(model_path: Optional[str] = None,
                    use_t5: bool = True) -> NewsSummarizer:
    """
    加载摘要引擎
    参数:
        model_path: 微调后的 T5 模型路径，None 则使用原始预训练模型
        use_t5: 是否加载 T5（False 则只用 TextRank）
    返回:
        NewsSummarizer 实例
    """
    print("=" * 50)
    print(" 加载 NewsMind 摘要引擎")
    print("=" * 50)

    # 加载 BERT（TextRank 必需）
    bert = BertEncoder()

    # 加载 T5（可选）
    t5 = None
    if use_t5:
        # 优先使用微调后的模型
        if model_path and Path(model_path).exists():
            print(f"[*] 使用微调模型: {model_path}")
            t5 = T5Summarizer(model_path=model_path)
        else:
            # 检查默认路径
            default_path = MODEL_DIR / "t5_summarizer_best"
            if default_path.exists():
                print(f"[*] 使用默认微调模型: {default_path}")
                t5 = T5Summarizer(model_path=str(default_path))
            else:
                print("[!] 未找到微调模型，使用预训练 T5（效果有限）")
                print("    建议先运行 train.py 训练模型")
                t5 = T5Summarizer()

    summarizer = NewsSummarizer(bert_encoder=bert, t5_summarizer=t5)
    print("[✓] 摘要引擎就绪\n")
    return summarizer


# ============================================
# 2. 单条预测
# ============================================

def predict_single(text: str, summarizer: NewsSummarizer,
                   top_k: int = TEXTRANK_TOP_K) -> dict:
    """
    对单条新闻生成摘要
    参数:
        text: 新闻原文
        summarizer: 摘要引擎
        top_k: 关键句数量
    返回:
        包含摘要和统计信息的字典
    """
    start = time.time()
    result = summarizer.summarize(text, top_k=top_k, use_t5=True)
    elapsed = result["inference_time"]

    print("\n" + "=" * 50)
    print(" 摘要结果")
    print("=" * 50)

    print(f"\n📝 原文 ({len(text)} 字符):")
    print(f"   {text[:200]}...")

    print(f"\n📌 关键句提取 (TextRank, {len(result['key_sentences'])} 句):")
    for i, (sent, score) in enumerate(result["key_sentences"][:3], 1):
        print(f"   [{i}] (分数:{score:.4f}) {sent[:80]}...")

    print(f"\n📋 抽取式摘要 ({len(result['extractive_summary'])} 字符):")
    print(f"   {result['extractive_summary'][:300]}")

    print(f"\n✨ 生成式摘要 ({len(result['abstractive_summary'])} 字符):")
    print(f"   {result['abstractive_summary'][:300]}")

    print(f"\n⏱️  耗时: {elapsed:.3f} 秒", end="")
    if elapsed > MAX_INFERENCE_TIME:
        print(f" ⚠️ 超过 {MAX_INFERENCE_TIME}s 阈值")
    else:
        print(f" ✅ 达标")
    print(f"   句子数: {result['sentence_count']}")

    return result


# ============================================
# 3. 文件批量预测
# ============================================

def predict_file(input_path: str, summarizer: NewsSummarizer,
                 output_path: Optional[str] = None) -> List[dict]:
    """
    对 JSON 文件中的新闻批量生成摘要
    输入格式: [{"content": "新闻正文", "category": "类别"}, ...]
    输出格式: [{"content": ..., "category": ..., "summary": ...}, ...]
    """
    input_path = Path(input_path)
    if not input_path.exists():
        print(f"[✗] 文件不存在: {input_path}")
        return []

    print(f"\n[*] 读取文件: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total = len(data)
    print(f"[*] 共 {total} 条新闻，开始生成摘要...\n")

    results = []
    times = []
    rouge_scores = []

    for i, item in enumerate(data):
        content = item.get("content", "")
        if not content:
            continue

        # 生成摘要
        result = summarizer.summarize(content, use_t5=True)
        times.append(result["inference_time"])

        # 如果有参考摘要，计算 ROUGE-L
        ref_summary = item.get("summary", "")
        if ref_summary:
            rouge = rouge_l_score(ref_summary,
                                  result.get("abstractive_summary", ""))
            rouge_scores.append(rouge)

        # 构建输出
        output_item = {
            "category": item.get("category", ""),
            "content": content,
            "extractive_summary": result["extractive_summary"],
            "abstractive_summary": result["abstractive_summary"],
            "inference_time": result["inference_time"],
            "sentence_count": result["sentence_count"],
        }
        if ref_summary:
            output_item["reference_summary"] = ref_summary
            output_item["rouge_l"] = rouge

        results.append(output_item)

        # 进度
        if (i + 1) % 10 == 0:
            avg_t = np.mean(times[-10:])
            print(f"  进度: {i + 1}/{total} | 平均耗时: {avg_t:.3f}s", end="")
            if rouge_scores:
                print(f" | ROUGE-L: {np.mean(rouge_scores[-10:]):.3f}", end="")
            print()

    # 统计
    avg_time = np.mean(times) if times else 0
    print(f"\n{'='*50}")
    print(f" 批量预测完成")
    print(f"{'='*50}")
    print(f"  总篇数:     {len(results)}")
    print(f"  总耗时:     {sum(times):.1f} 秒")
    print(f"  平均耗时:   {avg_time:.3f} 秒/篇")
    print(f"  最快:       {min(times):.3f} 秒" if times else "")
    print(f"  最慢:       {max(times):.3f} 秒" if times else "")
    print(f"  速度达标率: {np.mean(np.array(times) <= MAX_INFERENCE_TIME) * 100:.1f}%" if times else "")

    if rouge_scores:
        avg_rouge = np.mean(rouge_scores)
        pass_rate = np.mean(np.array(rouge_scores) >= ROUGE_L_THRESHOLD)
        print(f"\n  ROUGE-L 评估:")
        print(f"    平均:     {avg_rouge:.4f}")
        print(f"    达标率:   {pass_rate * 100:.1f}%")

    # 保存结果
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n[✓] 结果已保存: {output_path}")

    return results


# ============================================
# 4. ROUGE-L 评估模式
# ============================================

def eval_mode(test_file: str, summarizer: NewsSummarizer):
    """
    评估模式：加载测试集，生成摘要，计算 ROUGE-L
    参数:
        test_file: 测试集 JSON 文件（需包含 "summary" 参考字段）
    """
    print(f"\n[*] 加载测试集: {test_file}")
    with open(test_file, 'r', encoding='utf-8') as f:
        test_data = json.load(f)

    # 限制评估数量
    n = min(len(test_data), 200)
    test_data = test_data[:n]
    print(f"[*] 评估 {n} 条数据...\n")

    refs, gens = [], []
    times = []

    for i, item in enumerate(test_data):
        content = item.get("content", "")

        result = summarizer.summarize(content, use_t5=True)

        gen_summary = result.get("abstractive_summary",
                                 result.get("extractive_summary", ""))
        ref_summary = item.get("summary", "")

        gens.append(gen_summary)
        refs.append(ref_summary)
        times.append(result["inference_time"])

        if (i + 1) % 20 == 0:
            rouge = rouge_l_score(ref_summary, gen_summary) if ref_summary else 0
            print(f"  进度: {i + 1}/{n} | ROUGE-L: {rouge:.3f} | 耗时: {result['inference_time']:.3f}s")

    # 批量评估
    eval_result = evaluate_rouge(refs, gens)

    print(f"\n{'='*50}")
    print(f" ROUGE-L 评估结果")
    print(f"{'='*50}")
    print(f"  样本数:     {eval_result['total_samples']}")
    print(f"  平均:       {eval_result['avg_rouge_l']:.4f}")
    print(f"  最高:       {eval_result['max_rouge_l']:.4f}")
    print(f"  最低:       {eval_result['min_rouge_l']:.4f}")
    print(f"  标准差:     {eval_result['std_rouge_l']:.4f}")
    print(f"  达标率:     {eval_result['pass_rate'] * 100:.1f}% (≥{ROUGE_L_THRESHOLD})")

    avg_time = np.mean(times) if times else 0
    time_pass = np.mean(np.array(times) <= MAX_INFERENCE_TIME) * 100
    print(f"\n  平均耗时:   {avg_time:.3f} 秒")
    print(f"  速度达标率: {time_pass:.1f}% (<{MAX_INFERENCE_TIME}s)")

    if eval_result['avg_rouge_l'] >= ROUGE_L_THRESHOLD:
        print(f"\n  ✅ ROUGE-L 达标!")
    else:
        print(f"\n  ⚠️ ROUGE-L 未达标，建议进一步训练")

    return eval_result


# ============================================
# 5. 交互模式
# ============================================

def interactive_mode(summarizer: NewsSummarizer):
    """交互式摘要生成"""
    print("\n" + "=" * 50)
    print(" NewsMind 交互式摘要")
    print(" 输入新闻文本，按 Enter 后输入 'END' 结束")
    print(" 输入 'quit' 退出")
    print("=" * 50)

    while True:
        print("\n请输入新闻文本 (输入 'END' 结束, 'quit' 退出):")
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                return
            if line.strip() == 'END':
                break
            if line.strip() == 'quit':
                return
            lines.append(line)

        text = '\n'.join(lines).strip()
        if not text:
            print("[!] 文本为空，请重新输入")
            continue

        predict_single(text, summarizer)


# ============================================
# 6. 命令行入口
# ============================================

def main():
    parser = argparse.ArgumentParser(description="NewsMind 新闻摘要预测")

    # 输入模式（互斥）
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--text", "-t", type=str, help="直接输入新闻文本")
    group.add_argument("--file", "-f", type=str, help="JSON 文件路径（批量预测）")
    group.add_argument("--eval", "-e", type=str, help="测试集路径（ROUGE-L 评估模式）")
    group.add_argument("--interactive", "-i", action="store_true",
                       help="交互模式")

    # 可选参数
    parser.add_argument("--model", "-m", type=str, default=None,
                        help="微调模型路径（默认: trained_models/t5_summarizer_best）")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="输出 JSON 文件路径")
    parser.add_argument("--top-k", "-k", type=int, default=TEXTRANK_TOP_K,
                        help=f"TextRank 关键句数量（默认: {TEXTRANK_TOP_K}）")
    parser.add_argument("--no-t5", action="store_true",
                        help="仅使用 TextRank，不加载 T5")

    args = parser.parse_args()

    # 加载模型
    summarizer = load_summarizer(model_path=args.model, use_t5=not args.no_t5)

    # 执行
    if args.text:
        # 单条预测
        predict_single(args.text, summarizer, top_k=args.top_k)

    elif args.file:
        # 批量预测
        output = args.output or str(Path(args.file).with_suffix(".summaries.json"))
        predict_file(args.file, summarizer, output_path=output)

    elif args.eval:
        # 评估模式
        eval_mode(args.eval, summarizer)

    elif args.interactive:
        # 交互模式
        interactive_mode(summarizer)

    else:
        # 默认：演示示例
        print("[*] 未指定输入，运行演示示例...\n")
        demo_text = """
        新华社北京3月15日电（记者张泉）人工智能技术正在深刻改变世界。
        近年来，我国人工智能产业发展迅速，核心技术不断突破。在自然语言处理领域，
        预训练大模型取得了显著进展，BERT、GPT等模型在文本理解、生成等任务上
        展现出强大能力。业内人士表示，AI技术将在新闻、教育、医疗等多个领域
        发挥重要作用。专家指出，要进一步加强基础研究，突破关键核心技术，
        推动人工智能与实体经济深度融合，为高质量发展注入新动能。
        """
        predict_single(demo_text.strip(), summarizer, top_k=args.top_k)


if __name__ == "__main__":
    main()
