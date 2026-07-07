# ============================================
# 文件名: backend/ai/summarizer.py
# 功能: 新闻摘要核心引擎
# 流程: 文本清洗 → 分句 → BERT向量 → TextRank关键句 → T5摘要生成
# ============================================

import re
import time
import numpy as np
from typing import List, Tuple, Optional
from collections import defaultdict

import torch
import torch.nn.functional as F
from transformers import (
    AutoTokenizer,
    AutoModel,
    T5ForConditionalGeneration,
)

from .config import (
    DEVICE, USE_AMP,
    BERT_MODEL_NAME, BERT_MAX_LENGTH,
    T5_MODEL_NAME, T5_MAX_INPUT_LENGTH, T5_MAX_TARGET_LENGTH,
    TEXTRANK_TOP_K, TEXTRANK_DAMPING, TEXTRANK_MAX_ITER,
    TEXTRANK_CONVERGENCE, TEXTRANK_MIN_SENTENCE_LENGTH,
    SUMMARY_MIN_LENGTH, SUMMARY_MAX_LENGTH, NUM_BEAMS,
    MODEL_DIR,
)


# ============================================
# 1. 文本清洗（与 data_preprocess.py 保持一致）
# ============================================

def clean_text(text: str) -> str:
    """
    清洗新闻文本：去HTML、URL、特殊字符、多余空白
    """
    if not text or not isinstance(text, str):
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&[a-z]+;', '', text)
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', text)
    text = re.sub(r'[^一-龥A-Za-z0-9'
                  r'　-〿＀-￯'
                  r'，。！？；：""''【】《》（）…—\n\r\t]', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'\r', '', text)
    text = re.sub(r'[ \t]{2,}', '', text)
    return text.strip()


# ============================================
# 2. 句子分割
# ============================================

def split_sentences(text: str) -> List[str]:
    """
    中文分句：基于标点符号分割
    保留句号、问号、感叹号、分号、换行等作为分割点
    """
    # 重要的句子边界标点
    boundaries = r'[。！？!?\n；;]'
    raw_sentences = re.split(boundaries, text)

    sentences = []
    for sent in raw_sentences:
        sent = sent.strip()
        # 过滤空句和过短句子
        if sent and len(sent) >= TEXTRANK_MIN_SENTENCE_LENGTH:
            # 对过长的句子按逗号再分割
            if len(sent) > 200:
                sub_sents = re.split(r'[，,、]', sent)
                for sub in sub_sents:
                    sub = sub.strip()
                    if len(sub) >= TEXTRANK_MIN_SENTENCE_LENGTH:
                        sentences.append(sub)
            else:
                sentences.append(sent)

    return sentences


def is_low_quality_generated_summary(summary: str) -> bool:
    """检测未微调生成模型常见的异常输出，异常时回退到 TextRank 摘要。"""
    if not summary or len(summary.strip()) < SUMMARY_MIN_LENGTH:
        return True
    if "extra" in summary.lower():
        return True
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', summary)
    return len(chinese_chars) / max(len(summary), 1) < 0.35


_SENTENCE_END_RE = re.compile(r'[\u3002\uff01\uff1f!?;\uff1b\n]+')
_CLAUSE_END_RE = re.compile(r'[\uff0c,\u3001\uff1b;]+')


def _normalize_for_compare(text: str) -> str:
    return re.sub(r'[\s\u3000\uff0c,\u3001\u3002.!?\uff01\uff1f\uff1b;]+', '', text or '')


def _is_too_close_to_original(summary: str, original: str) -> bool:
    summary_norm = _normalize_for_compare(summary)
    original_norm = _normalize_for_compare(original)
    if not summary_norm or not original_norm:
        return True
    if summary_norm == original_norm:
        return True
    if summary_norm in original_norm and len(summary_norm) >= len(original_norm) * 0.85:
        return True
    return len(summary) >= len(original) * 0.85


def _finish_sentence(text: str) -> str:
    text = (text or '').strip(' \t\r\n\uff0c,\u3001\uff1b;\u3002.!?\uff01\uff1f')
    if not text:
        return ''
    return text + '\u3002'


def make_concise_summary(original: str, candidate: str = '') -> str:
    """Return a concise summary that is intentionally shorter than the source."""
    original = (original or '').strip()
    candidate = (candidate or '').strip()
    if not original:
        return ''
    if len(original) <= SUMMARY_MIN_LENGTH:
        return original

    limit = max(SUMMARY_MIN_LENGTH, min(SUMMARY_MAX_LENGTH, int(len(original) * 0.65)))
    if candidate and not _is_too_close_to_original(candidate, original) and len(candidate) <= limit:
        return _finish_sentence(candidate)

    sentences = [s.strip() for s in _SENTENCE_END_RE.split(original) if s.strip()]
    source = sentences[0] if sentences else original
    if len(source) > limit:
        clauses = [s.strip() for s in _CLAUSE_END_RE.split(source) if s.strip()]
        source = clauses[0] if clauses else source
    if len(source) > limit:
        source = source[:limit]
    return _finish_sentence(source)


# ============================================
# 3. BERT 句子向量编码器
# ============================================

class BertEncoder:
    """
    使用 BERT-base-chinese 将句子编码为固定维度向量（768维）
    """

    def __init__(self):
        print(f"[BERT] 加载模型: {BERT_MODEL_NAME} ...")
        self.tokenizer = AutoTokenizer.from_pretrained(BERT_MODEL_NAME)
        self.model = AutoModel.from_pretrained(BERT_MODEL_NAME).to(DEVICE)
        self.model.eval()  # 推理模式
        print(f"[BERT] 模型已加载到 {DEVICE}")

    def encode_sentences(self, sentences: List[str]) -> np.ndarray:
        """
        将句子列表编码为向量矩阵
        参数:
            sentences: 句子列表
        返回:
            numpy array, shape=(n_sentences, 768)
        """
        if not sentences:
            return np.array([])

        embeddings = []

        # 批量编码（减小显存占用）
        batch_size = 16 if DEVICE.type == "cuda" else 8

        for i in range(0, len(sentences), batch_size):
            batch = sentences[i:i + batch_size]

            with torch.no_grad():
                # 分词
                inputs = self.tokenizer(
                    batch,
                    padding=True,
                    truncation=True,
                    max_length=BERT_MAX_LENGTH,
                    return_tensors="pt"
                ).to(DEVICE)

                # BERT 前向传播
                outputs = self.model(**inputs)

                # 取 [CLS] token 的向量作为句子表示
                # 或者用所有 token 的 mean pooling
                cls_embeddings = outputs.last_hidden_state[:, 0, :]  # [batch, 768]

                embeddings.append(cls_embeddings.cpu().numpy())

        if embeddings:
            return np.concatenate(embeddings, axis=0)
        return np.array([])

    def encode_single(self, text: str) -> np.ndarray:
        """编码单个文本为向量（取CLS向量）"""
        with torch.no_grad():
            inputs = self.tokenizer(
                text,
                padding=True,
                truncation=True,
                max_length=BERT_MAX_LENGTH,
                return_tensors="pt"
            ).to(DEVICE)
            outputs = self.model(**inputs)
            return outputs.last_hidden_state[:, 0, :].cpu().numpy().squeeze(0)


# ============================================
# 4. TextRank 关键句提取算法
# ============================================

class TextRank:
    """
    基于图排序的关键句提取
    思路: 句子为节点，语义相似度为边权，PageRank 迭代计算重要性
    """

    def __init__(self,
                 damping: float = TEXTRANK_DAMPING,
                 max_iter: int = TEXTRANK_MAX_ITER,
                 convergence: float = TEXTRANK_CONVERGENCE):
        self.damping = damping
        self.max_iter = max_iter
        self.convergence = convergence

    def build_similarity_matrix(self, embeddings: np.ndarray) -> np.ndarray:
        """
        构建句子相似度矩阵
        使用余弦相似度衡量句子间的语义相似性
        返回: shape=(n, n) 的归一化相似度矩阵
        """
        n = len(embeddings)
        if n <= 1:
            return np.array([[1.0]])

        # L2归一化（使余弦相似度等于内积）
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1  # 防止除零
        normalized = embeddings / norms

        # 余弦相似度矩阵 = 归一化向量的内积
        sim_matrix = np.dot(normalized, normalized.T)  # [n, n]

        # 对角线设为0（句子不与自身计算相似度）
        np.fill_diagonal(sim_matrix, 0)

        # 归一化为概率转移矩阵（每列和为1）
        col_sums = sim_matrix.sum(axis=0, keepdims=True)
        col_sums[col_sums == 0] = 1  # 防止除零
        sim_matrix = sim_matrix / col_sums

        return sim_matrix

    def pagerank(self, matrix: np.ndarray) -> np.ndarray:
        """
        迭代 PageRank 算法
        参数:
            matrix: 列归一化的转移矩阵 [n, n]
        返回:
            scores: 每个节点的 PageRank 分数 [n]
        """
        n = matrix.shape[0]
        if n == 0:
            return np.array([])
        if n == 1:
            return np.array([1.0])

        # 初始分数均匀分布
        scores = np.ones(n) / n

        # 阻尼向量（随机跳转概率）
        damping_vec = np.ones(n) / n * (1 - self.damping)

        for iteration in range(self.max_iter):
            prev_scores = scores.copy()

            # PageRank 迭代: PR = d * M * PR + (1-d) * uniform
            scores = self.damping * matrix @ scores + damping_vec

            # 检查收敛
            diff = np.abs(scores - prev_scores).sum()
            if diff < self.convergence:
                break

        return scores

    def extract(self, sentences: List[str], embeddings: np.ndarray,
                top_k: int = TEXTRANK_TOP_K) -> List[Tuple[str, float, int]]:
        """
        提取 Top-K 关键句
        参数:
            sentences: 原始句子列表
            embeddings: 句子BERT向量
            top_k: 提取的关键句数量
        返回:
            List of (sentence, score, original_index)
            按原始顺序排序
        """
        n = len(sentences)
        if n == 0:
            return []
        if n <= top_k:
            # 句子数不足 top_k，全部返回
            return [(sent, 1.0, i) for i, sent in enumerate(sentences)]

        # 构建相似度矩阵
        sim_matrix = self.build_similarity_matrix(embeddings)

        # PageRank 计算分数
        scores = self.pagerank(sim_matrix)

        # 选择 top-k（按分数降序）
        top_indices = np.argsort(scores)[::-1][:top_k]

        # 构建结果（按原始位置排序，保持语义连贯）
        results = [(sentences[i], float(scores[i]), i) for i in top_indices]
        results.sort(key=lambda x: x[2])  # 按原始顺序

        return results


# ============================================
# 5. T5 抽象式摘要生成器
# ============================================

class T5Summarizer:
    """
    基于 T5 的抽象式摘要生成
    使用预训练中文 T5-small 模型进行微调
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        参数:
            model_path: 微调后模型路径，None 则使用预训练模型
        """
        model_name = model_path or T5_MODEL_NAME
        print(f"[T5] 加载模型: {model_name} ...")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = T5ForConditionalGeneration.from_pretrained(model_name).to(DEVICE)
        self.model_path = model_path

        # 如果 tokenizer 没有 pad_token，设为 eos_token
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        print(f"[T5] 模型已加载到 {DEVICE}")

    def generate_summary(self, text: str,
                         max_input_length: int = T5_MAX_INPUT_LENGTH,
                         max_target_length: int = T5_MAX_TARGET_LENGTH,
                         num_beams: int = NUM_BEAMS) -> str:
        """
        对输入文本生成摘要
        参数:
            text: 输入文本（可以是原文或TextRank关键句拼接）
            max_input_length: 输入截断长度
            max_target_length: 最大生成长度
            num_beams: Beam Search 束宽
        返回:
            生成的摘要文本
        """
        # 添加 T5 任务前缀
        input_text = f"summarize: {text}"

        # 编码输入
        inputs = self.tokenizer(
            input_text,
            max_length=max_input_length,
            truncation=True,
            padding=True,
            return_tensors="pt"
        ).to(DEVICE)

        # 生成摘要
        with torch.no_grad():
            outputs = self.model.generate(
                input_ids=inputs.input_ids,
                attention_mask=inputs.attention_mask,
                max_length=max_target_length,
                min_length=SUMMARY_MIN_LENGTH,
                num_beams=num_beams,
                length_penalty=1.0,
                early_stopping=True,
                no_repeat_ngram_size=3,       # 避免重复三元组
                repetition_penalty=1.2,        # 重复惩罚
            )

        # 解码
        summary = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return summary


# ============================================
# 6. 新闻摘要引擎（组合 BERT + TextRank + T5）
# ============================================

class NewsSummarizer:
    """
    完整的新闻摘要引擎
    流程:
      1. 文本清洗
      2. 中文分句
      3. BERT 编码句子向量
      4. TextRank 提取关键句 (extractive)
      5. T5 将关键句改写为精炼摘要 (abstractive)
      6. 计时与评估
    """

    def __init__(self,
                 bert_encoder: Optional[BertEncoder] = None,
                 t5_summarizer: Optional[T5Summarizer] = None):
        """
        参数:
            bert_encoder: BERT 编码器（可共享）
            t5_summarizer: T5 摘要器（可共享）
        """
        self.bert = bert_encoder or BertEncoder()
        self.textrank = TextRank()
        self.t5 = t5_summarizer  # 可以为 None（仅用 TextRank）

    def summarize(self, text: str,
                  top_k: int = TEXTRANK_TOP_K,
                  use_t5: bool = True) -> dict:
        """
        对新闻文本生成摘要
        参数:
            text: 新闻原文
            top_k: TextRank 提取的关键句数量
            use_t5: 是否使用 T5 精炼摘要
        返回:
            {
                "extractive_summary": "TextRank 提取的关键句拼接",
                "abstractive_summary": "T5 生成的精炼摘要",
                "key_sentences": [(句子, 分数), ...],
                "inference_time": 秒数,
                "sentence_count": 原文句子数
            }
        """
        start_time = time.time()
        result = {}

        # 步骤1: 文本清洗
        cleaned = clean_text(text)

        if len(cleaned) < TEXTRANK_MIN_SENTENCE_LENGTH:
            # 文本过短，原文即摘要
            elapsed = time.time() - start_time
            concise = make_concise_summary(cleaned)
            return {
                "extractive_summary": concise,
                "abstractive_summary": concise,
                "key_sentences": [(concise, 1.0)],
                "inference_time": elapsed,
                "sentence_count": 1
            }

        # 步骤2: 分句
        sentences = split_sentences(cleaned)
        result["sentence_count"] = len(sentences)

        if not sentences:
            elapsed = time.time() - start_time
            concise = make_concise_summary(cleaned)
            result.update({
                "extractive_summary": concise,
                "abstractive_summary": concise,
                "key_sentences": [],
                "inference_time": elapsed,
            })
            return result

        # 步骤3: BERT 编码句子向量
        embeddings = self.bert.encode_sentences(sentences)

        # 步骤4: TextRank 提取关键句
        effective_top_k = min(top_k, max(1, int(np.ceil(len(sentences) * 0.4))))
        ranked = self.textrank.extract(sentences, embeddings, top_k=effective_top_k)
        key_sentences_str = "\u3002".join([s for s, _, _ in ranked]) + "\u3002"
        key_sentences_str = make_concise_summary(cleaned, key_sentences_str)

        result["key_sentences"] = [(s, round(sc, 4)) for s, sc, _ in ranked]
        result["extractive_summary"] = key_sentences_str

        # 步骤5: T5 精炼摘要
        if use_t5 and self.t5 is not None:
            # 将关键句拼接作为 T5 的输入，生成更精炼的摘要
            try:
                abstractive = self.t5.generate_summary(key_sentences_str)
                if is_low_quality_generated_summary(abstractive) or _is_too_close_to_original(abstractive, cleaned):
                    abstractive = key_sentences_str
                abstractive = make_concise_summary(cleaned, abstractive)
                result["abstractive_summary"] = abstractive
            except Exception as e:
                print(f"[!] T5 生成失败: {e}")
                result["abstractive_summary"] = key_sentences_str
        else:
            result["abstractive_summary"] = key_sentences_str

        # 步骤6: 计时
        elapsed = time.time() - start_time
        result["inference_time"] = round(elapsed, 3)

        return result

    def batch_summarize(self, texts: List[str], top_k: int = TEXTRANK_TOP_K) -> List[dict]:
        """
        批量生成摘要
        参数:
            texts: 新闻文本列表
            top_k: 关键句数量
        返回:
            摘要结果列表
        """
        results = []
        total = len(texts)

        print(f"\n[*] 批量生成摘要 ({total} 篇)...")
        for i, text in enumerate(texts):
            if (i + 1) % 50 == 0:
                print(f"  进度: {i + 1}/{total}")

            result = self.summarize(text, top_k=top_k)
            results.append(result)

        # 统计平均时间
        avg_time = np.mean([r['inference_time'] for r in results])
        print(f"[✓] 完成! 平均耗时: {avg_time:.3f} 秒/篇")

        return results


# ============================================
# 7. ROUGE-L 评估
# ============================================

def rouge_l_score(reference: str, hypothesis: str) -> float:
    """
    计算 ROUGE-L 分数（最长公共子序列）
    参数:
        reference: 参考摘要
        hypothesis: 生成的摘要
    返回:
        F1 分数 (0~1)
    """
    if not reference or not hypothesis:
        return 0.0

    # 分词（按字符级别，中文友好）
    ref_chars = list(reference)
    hyp_chars = list(hypothesis)

    # 最长公共子序列 (LCS)
    lcs_len = _lcs_length(ref_chars, hyp_chars)

    if lcs_len == 0:
        return 0.0

    # 召回率 = LCS长度 / 参考长度
    recall = lcs_len / len(ref_chars) if len(ref_chars) > 0 else 0
    # 精确率 = LCS长度 / 生成长度
    precision = lcs_len / len(hyp_chars) if len(hyp_chars) > 0 else 0

    # F1 分数
    if recall + precision == 0:
        return 0.0
    f1 = 2 * recall * precision / (recall + precision)

    return round(f1, 4)


def _lcs_length(a: list, b: list) -> int:
    """计算两个序列的最长公共子序列长度（DP 优化版）"""
    m, n = len(a), len(b)

    # 空间优化：只保留两行
    prev = [0] * (n + 1)
    curr = [0] * (n + 1)

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev, curr = curr, prev

    return prev[n]


def evaluate_rouge(reference_summaries: List[str],
                   generated_summaries: List[str]) -> dict:
    """
    批量计算 ROUGE-L 分数
    返回:
        {
            "avg_rouge_l": 平均ROUGE-L,
            "max_rouge_l": 最高分,
            "min_rouge_l": 最低分,
            "pass_rate": 超过阈值(0.4)的比例
        }
    """
    scores = []
    for ref, gen in zip(reference_summaries, generated_summaries):
        score = rouge_l_score(ref, gen)
        scores.append(score)

    scores = np.array(scores)
    pass_rate = np.mean(scores >= 0.4)

    result = {
        "avg_rouge_l": round(float(np.mean(scores)), 4),
        "max_rouge_l": round(float(np.max(scores)), 4),
        "min_rouge_l": round(float(np.min(scores)), 4),
        "std_rouge_l": round(float(np.std(scores)), 4),
        "pass_rate": round(float(pass_rate), 4),
        "total_samples": len(scores),
    }

    return result
