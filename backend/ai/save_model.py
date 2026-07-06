# ============================================
# 文件名: backend/ai/save_model.py
# 功能: 模型保存、加载、导出、信息查看
# 用法:
#   保存模型:  python -m backend.ai.save_model --save
#   导出ONNX:  python -m backend.ai.save_model --export onnx
#   查看信息:  python -m backend.ai.save_model --info
# ============================================

import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional

import torch

from .config import (
    DEVICE, MODEL_DIR, T5_MODEL_NAME,
    BERT_MODEL_NAME, TEXTRANK_TOP_K,
    T5_MAX_INPUT_LENGTH, T5_MAX_TARGET_LENGTH,
)
from .summarizer import T5Summarizer, BertEncoder


# ============================================
# 1. 模型保存
# ============================================

def save_t5_model(save_path: Optional[str] = None):
    """
    保存 T5 摘要模型（含 tokenizer 和配置）
    参数:
        save_path: 保存路径，默认为 trained_models/t5_summarizer_v{timestamp}
    """
    if save_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = MODEL_DIR / f"t5_summarizer_{timestamp}"

    save_path = Path(save_path)
    save_path.mkdir(parents=True, exist_ok=True)

    print("=" * 50)
    print(" 保存 T5 摘要模型")
    print("=" * 50)
    print(f"  目标路径: {save_path}")

    # 查找最佳模型
    best_model = MODEL_DIR / "t5_summarizer_best"
    if best_model.exists() and best_model.is_dir():
        source = best_model
        print(f"  源模型: {source}")
    else:
        # 从预训练模型保存
        print(f"  未找到微调模型，保存预训练模型: {T5_MODEL_NAME}")
        print("[*] 下载并保存预训练 T5...")
        summarizer = T5Summarizer()
        summarizer.model.save_pretrained(str(save_path))
        summarizer.tokenizer.save_pretrained(str(save_path))
        print(f"[✓] 预训练模型已保存: {save_path}")
        return str(save_path)

    # 复制模型文件
    print("[*] 复制模型文件...")
    for file in source.iterdir():
        if file.is_file():
            shutil.copy2(file, save_path / file.name)

    # 保存元信息
    meta = {
        "model_type": "T5ForConditionalGeneration",
        "base_model": T5_MODEL_NAME,
        "task": "news_summarization",
        "language": "chinese",
        "max_input_length": T5_MAX_INPUT_LENGTH,
        "max_target_length": T5_MAX_TARGET_LENGTH,
        "top_k_sentences": TEXTRANK_TOP_K,
        "device": str(DEVICE),
        "saved_at": datetime.now().isoformat(),
        "framework": "pytorch + transformers",
    }

    with open(save_path / "model_meta.json", 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # 计算大小
    total_size = sum(f.stat().st_size for f in save_path.rglob("*") if f.is_file())
    print(f"[✓] 模型已保存: {save_path}")
    print(f"    大小: {total_size / 1024**2:.1f} MB")
    print(f"    文件数: {len(list(save_path.iterdir()))}")

    return str(save_path)


# ============================================
# 2. 模型导出
# ============================================

def export_to_onnx(model_path: Optional[str] = None):
    """
    将 PyTorch 模型导出为 ONNX 格式（便于部署）
    注意: T5 是生成模型，ONNX 导出较复杂，此处导出编码器部分
    """
    print("=" * 50)
    print(" 导出模型")
    print("=" * 50)

    onnx_available = False
    try:
        import onnx
        import onnxruntime
        onnx_available = True
    except ImportError:
        print("[!] ONNX 依赖未安装")
        print("    安装: pip install onnx onnxruntime")
        return None

    # 加载模型
    model_path = Path(model_path) if model_path else (MODEL_DIR / "t5_summarizer_best")
    if not model_path.exists():
        print(f"[✗] 模型不存在: {model_path}")
        print("    请先运行 train.py 训练模型")
        return None

    print(f"[*] 加载模型: {model_path}")
    import transformers
    model = transformers.T5ForConditionalGeneration.from_pretrained(str(model_path))
    tokenizer = transformers.AutoTokenizer.from_pretrained(str(model_path))
    model.eval()

    # 导出编码器
    print("[*] 导出 T5 编码器...")
    encoder = model.encoder

    # 准备示例输入
    sample_text = "summarize: 人工智能技术正在改变世界"
    inputs = tokenizer(sample_text, return_tensors="pt",
                       max_length=T5_MAX_INPUT_LENGTH, truncation=True)

    onnx_path = MODEL_DIR / "t5_encoder.onnx"

    torch.onnx.export(
        encoder,
        (inputs.input_ids,),
        str(onnx_path),
        input_names=["input_ids"],
        output_names=["encoder_output"],
        dynamic_axes={
            "input_ids": {0: "batch", 1: "sequence"},
            "encoder_output": {0: "batch", 1: "sequence"},
        },
        opset_version=14,
        do_constant_folding=True,
    )

    size_mb = onnx_path.stat().st_size / 1024**2
    print(f"[✓] 编码器已导出: {onnx_path} ({size_mb:.1f} MB)")

    # 保存完整模型权重（TorchScript 作为备选）
    print("[*] 导出完整模型权重...")
    weights_path = MODEL_DIR / "t5_model_weights.pt"
    torch.save({
        "model_state_dict": model.state_dict(),
        "model_config": model.config.to_dict(),
        "tokenizer_name": T5_MODEL_NAME,
    }, weights_path)
    size_mb = weights_path.stat().st_size / 1024**2
    print(f"[✓] 权重已导出: {weights_path} ({size_mb:.1f} MB)")

    return str(onnx_path), str(weights_path)


# ============================================
# 3. 模型信息
# ============================================

def show_model_info():
    """显示已保存模型的信息"""
    print("=" * 50)
    print(" 模型信息")
    print("=" * 50)

    model_dir = MODEL_DIR

    if not model_dir.exists() or not any(model_dir.iterdir()):
        print(f"[!] 未找到模型: {model_dir}")
        print("    请先运行 train.py 训练模型")
        return

    for model_path in sorted(model_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if model_path.is_dir():
            size_mb = sum(f.stat().st_size for f in model_path.rglob("*") if f.is_file()) / 1024**2
            modified = datetime.fromtimestamp(model_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            print(f"\n  📁 {model_path.name}")
            print(f"     大小: {size_mb:.1f} MB")
            print(f"     修改: {modified}")

            # 元信息
            meta_file = model_path / "model_meta.json"
            if meta_file.exists():
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                print(f"     模型: {meta.get('model_type', 'N/A')}")
                print(f"     基座: {meta.get('base_model', 'N/A')}")
                print(f"     任务: {meta.get('task', 'N/A')}")

        elif model_path.suffix in ['.pt', '.pth', '.onnx']:
            size_mb = model_path.stat().st_size / 1024**2
            print(f"\n  📄 {model_path.name} ({size_mb:.1f} MB)")

    # 检查 BERT 缓存
    print(f"\n  BERT 模型: {BERT_MODEL_NAME}")
    print(f"    (首次运行自动从 HuggingFace 下载缓存)")


# ============================================
# 4. 命令行入口
# ============================================

def main():
    parser = argparse.ArgumentParser(description="NewsMind 模型保存/导出工具")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--save", "-s", action="store_true",
                       help="保存当前最佳模型到带时间戳的目录")
    group.add_argument("--export", "-e", type=str, default=None,
                       choices=["onnx", "torchscript", "all"],
                       help="导出模型格式 (onnx/torchscript/all)")
    group.add_argument("--info", "-i", action="store_true",
                       help="显示已保存模型的信息")

    parser.add_argument("--model", "-m", type=str, default=None,
                        help="源模型路径（默认: trained_models/t5_summarizer_best）")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="输出路径")

    args = parser.parse_args()

    if args.save:
        save_t5_model(save_path=args.output)
    elif args.export:
        export_to_onnx(model_path=args.model)
    elif args.info:
        show_model_info()
    else:
        # 默认：显示帮助并列出模型信息
        parser.print_help()
        print()
        show_model_info()


if __name__ == "__main__":
    main()
