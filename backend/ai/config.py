# ============================================
# 文件名: backend/ai/config.py
# 功能: AI 摘要模块全局配置
# ============================================

import os
import torch
from pathlib import Path

# ============================================
# 路径配置
# ============================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # NewsMind 根目录
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MODEL_DIR = BASE_DIR / "trained_models"

# 确保目录存在
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# ============================================
# 设备配置
# ============================================
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
USE_AMP = torch.cuda.is_available()  # 混合精度（仅GPU可用）

print(f"[配置] 计算设备: {DEVICE}")
if torch.cuda.is_available():
    print(f"[配置] GPU: {torch.cuda.get_device_name(0)}")
    print(f"[配置] 显存: {torch.cuda.get_device_properties(0).total_mem / 1024**3:.1f} GB")

# ============================================
# BERT 模型配置
# ============================================
BERT_MODEL_NAME = "bert-base-chinese"      # 中文BERT预训练模型
BERT_MAX_LENGTH = 512                       # BERT最大输入长度
BERT_EMBEDDING_DIM = 768                    # BERT输出向量维度

# ============================================
# T5 摘要模型配置
# ============================================
T5_MODEL_NAME = "uer/t5-small-chinese-cluecorpussmall"  # 小型中文T5（约16M参数）
T5_MAX_INPUT_LENGTH = 512    # T5编码器最大输入长度
T5_MAX_TARGET_LENGTH = 128   # T5解码器最大输出长度（摘要长度）

# ============================================
# TextRank 配置
# ============================================
TEXTRANK_TOP_K = 5              # 提取关键句数量
TEXTRANK_DAMPING = 0.85         # PageRank 阻尼系数
TEXTRANK_MAX_ITER = 100         # PageRank 最大迭代次数
TEXTRANK_CONVERGENCE = 1e-6     # PageRank 收敛阈值
TEXTRANK_MIN_SENTENCE_LENGTH = 5  # 最短句子长度（字符数）

# ============================================
# 训练配置
# ============================================
BATCH_SIZE = 4 if DEVICE.type == "cuda" else 2
LEARNING_RATE = 3e-4
NUM_EPOCHS = 3
WARMUP_STEPS = 500
MAX_GRAD_NORM = 1.0
WEIGHT_DECAY = 0.01
SAVE_STEPS = 2000
EVAL_STEPS = 1000
LOGGING_STEPS = 100

# CPU 训练限制（避免过慢）
CPU_MAX_TRAIN_SAMPLES = 10000   # CPU模式下最大训练样本数
CPU_NUM_EPOCHS = 1              # CPU模式下训练轮数

# ============================================
# 评估配置
# ============================================
ROUGE_L_THRESHOLD = 0.4          # ROUGE-L 最低要求
MAX_INFERENCE_TIME = 1.5         # 单篇最大推理时间（秒）

# ============================================
# 输出配置
# ============================================
SUMMARY_MIN_LENGTH = 30           # 摘要最小长度
SUMMARY_MAX_LENGTH = 150          # 摘要最大长度
NUM_BEAMS = 4                     # Beam Search 束宽（推理用）
