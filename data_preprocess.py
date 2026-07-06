# ============================================
# 文件名: data_preprocess.py
# 功能: THUCNews 新闻数据集预处理
# 说明: 读取原始THUCNews → 文本清洗 → 中文分词 →
#       去停用词 → 构建JSON → 划分数据集 → 统计可视化
# 用法: python data_preprocess.py
# ============================================

import os
import re
import json
import random
import shutil
import zipfile
import warnings
from pathlib import Path
from collections import Counter

import jieba
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 非交互式后端，服务器环境也能运行
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm

warnings.filterwarnings('ignore')

# ============================================
# 全局配置
# ============================================
# 数据集路径
DATA_DIR = Path("data/THUCNews")
OUTPUT_DIR = Path("data/processed")
STOPWORDS_FILE = Path("data/stopwords.txt")

# 输出文件
TRAIN_FILE = OUTPUT_DIR / "train.json"
VAL_FILE = OUTPUT_DIR / "val.json"
TEST_FILE = OUTPUT_DIR / "test.json"
STATS_FILE = OUTPUT_DIR / "statistics.json"

# 数据集划分比例
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

# 随机种子（保证结果可复现）
RANDOM_SEED = 42

# 最大序列长度（用于后续BERT模型）
MAX_SEQ_LENGTH = 512
MIN_TEXT_LENGTH = 20  # 太短的新闻过滤掉

# 是否启用分词（True=分词后存储，False=保留原文字符）
ENABLE_TOKENIZE = True

# 新闻类别（THUCNews标准分类）
CATEGORIES = [
    "体育", "娱乐", "家居", "彩票", "房产",
    "教育", "时尚", "时政", "星座", "游戏",
    "社会", "科技", "股票", "财经"
]

# ============================================
# 1. 数据集下载与解压
# ============================================

def download_thucnews():
    """
    下载 THUCNews 数据集
    优先使用 HuggingFace datasets，失败则尝试手动下载
    返回 True 表示数据集已就绪
    """
    # 检查是否已经存在
    if DATA_DIR.exists() and any(DATA_DIR.iterdir()):
        print(f"[✓] 数据集已存在于: {DATA_DIR}")
        return True

    print("[!] 未找到本地数据集，尝试自动下载...")
    print(f"    目标路径: {DATA_DIR}")

    # 方法1: 使用 HuggingFace datasets 库下载
    try:
        print("[*] 方法1: 从 HuggingFace datasets 下载...")
        from datasets import load_dataset
        dataset = load_dataset("thuc_news", trust_remote_code=True, cache_dir=str(OUTPUT_DIR / "hf_cache"))

        # 从 HuggingFace 格式转换为原始目录结构
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        print("[*] 正在转换数据格式...")

        for split_name, split_data in dataset.items():
            for item in tqdm(split_data, desc=f"  转换 {split_name}"):
                category = CATEGORIES[item['label']] if 'label' in item else str(item['label'])
                text = item.get('text', '') or item.get('content', '')
                cat_dir = DATA_DIR / category
                cat_dir.mkdir(parents=True, exist_ok=True)
                # 用文本hash作为文件名，避免重复
                file_id = abs(hash(text[:100])) % 100000000
                with open(cat_dir / f"{file_id}.txt", 'w', encoding='utf-8') as f:
                    f.write(text)

        print("[✓] 从 HuggingFace 下载完成！")
        return True

    except Exception as e:
        print(f"[✗] HuggingFace 下载失败: {e}")
        print("     尝试其他方法...")

    # 方法2: 从清华NLP镜像下载
    try:
        print("[*] 方法2: 从清华NLP镜像下载...")
        import requests

        url = "https://thunlp.oss-cn-qingdao.aliyuncs.com/THUCNews.zip"
        zip_path = OUTPUT_DIR / "THUCNews.zip"

        print(f"    下载地址: {url}")
        print(f"    文件大小约 2.5GB，请耐心等待...")

        response = requests.get(url, stream=True, timeout=3600)
        total_size = int(response.headers.get('content-length', 0))

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        with open(zip_path, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc="  下载进度") as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

        # 解压
        print("[*] 正在解压数据集...")
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(DATA_DIR.parent)

        # 清理压缩包
        zip_path.unlink()
        print("[✓] 数据集下载并解压完成！")
        return True

    except Exception as e:
        print(f"[✗] 自动下载失败: {e}")

    # 方法3: 提示手动下载
    print("""
╔══════════════════════════════════════════════════════╗
║ [!] 自动下载失败，请手动下载 THUCNews 数据集         ║
║                                                      ║
║ 下载地址（任一可用）:                                  ║
║ 1. https://thunlp.oss-cn-qingdao.aliyuncs.com/       ║
║    THUCNews.zip                                      ║
║ 2. http://thuctc.thunlp.org/                         ║
║                                                      ║
║ 下载后将 THUCNews 文件夹放到:                          ║
║ data/THUCNews/                                       ║
║                                                      ║
║ 目录结构:                                             ║
║ data/THUCNews/                                       ║
║   ├── 科技/                                          ║
║   ├── 体育/                                          ║
║   ├── 财经/                                          ║
║   └── ...                                            ║
╚══════════════════════════════════════════════════════╝
    """)
    return False


# ============================================
# 2. 文本清洗模块
# ============================================

def clean_text(text: str) -> str:
    """
    清洗新闻文本
    - 去除HTML标签
    - 去除URL链接
    - 去除特殊字符
    - 去除多余空白
    - 统一全角/半角
    """
    if not text or not isinstance(text, str):
        return ""

    # 去除HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&[a-z]+;', '', text)

    # 去除URL链接
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', text)

    # 去除特殊字符（保留中英文、数字、基本标点）
    text = re.sub(r'[^一-龥A-Za-z0-9'
                  r'　-〿＀-￯'
                  r'，。！？；：""''【】《》（）…—\n\r\t]', '', text)

    # 去除重复标点
    text = re.sub(r'[，]{2,}', '，', text)
    text = re.sub(r'[。]{2,}', '。', text)
    text = re.sub(r'[！]{2,}', '！', text)
    text = re.sub(r'[？]{2,}', '？', text)

    # 去除多余换行和空白
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'\r', '', text)
    text = re.sub(r'[ \t]{2,}', '', text)

    # 去除首尾空白
    text = text.strip()

    return text


def is_valid_text(text: str, min_length: int = MIN_TEXT_LENGTH) -> bool:
    """
    检查文本是否有效
    - 长度 >= min_length
    - 非纯数字/符号
    - 包含足够的中文字符
    """
    if len(text) < min_length:
        return False

    # 统计中文字符占比（至少30%是中文字符）
    chinese_chars = len(re.findall(r'[一-龥]', text))
    if chinese_chars / max(len(text), 1) < 0.3:
        return False

    return True


# ============================================
# 3. 中文分词模块
# ============================================

def load_stopwords() -> set:
    """
    加载停用词表
    返回停用词集合
    """
    stopwords = set()
    if STOPWORDS_FILE.exists():
        with open(STOPWORDS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    stopwords.add(line)
    else:
        # 内置最小停用词表（文件缺失时的后备）
        print("[!] 警告: 停用词文件未找到，使用内置最小停用词表")
        stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
            '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着',
            '没有', '看', '好', '自己', '这', '他', '她', '它', '们', '那', '些',
            '什么', '而', '为', '所以', '因为', '但是', '可以', '这个', '那个',
            '已经', '如果', '虽然', '而且', '不过', '还是', '只是', '然后',
        }
    return stopwords


def tokenize_text(text: str, stopwords: set) -> str:
    """
    中文分词 + 去除停用词
    参数:
        text: 清洗后的文本
        stopwords: 停用词集合
    返回:
        分词后的文本（空格分隔）
    """
    # jieba 精确模式分词
    tokens = jieba.lcut(text)

    # 去除停用词
    tokens = [t.strip() for t in tokens
              if t.strip()
              and t not in stopwords
              and len(t.strip()) > 1  # 去除单字
              and not t.strip().isdigit()  # 去除纯数字
              and not re.match(r'^[^一-龥]+$', t)]  # 保留含中文的词

    return ' '.join(tokens)


# ============================================
# 4. 数据集构建模块
# ============================================

def load_raw_data():
    """
    读取原始 THUCNews 数据集
    遍历每个类别文件夹，读取所有txt文件
    返回: list of {"category": str, "content": str, "file": str}
    """
    raw_data = []
    total_files = 0

    print("\n[*] 读取原始数据集...")
    print(f"    数据目录: {DATA_DIR}")

    for category in CATEGORIES:
        cat_dir = DATA_DIR / category
        if not cat_dir.exists():
            print(f"    [!] 未找到类别文件夹: {category}，跳过")
            continue

        files = list(cat_dir.glob("*.txt"))
        total_files += len(files)

        for file_path in tqdm(files, desc=f"  读取 [{category}]"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                raw_data.append({
                    "category": category,
                    "content": content,
                    "file": str(file_path)
                })
            except Exception as e:
                print(f"    [!] 读取失败: {file_path} - {e}")

    print(f"\n[✓] 共读取 {len(raw_data)} 篇文章（{total_files} 个文件）")
    return raw_data


def process_data(raw_data: list, stopwords: set):
    """
    完整的数据处理流程：
    1. 文本清洗
    2. 有效性过滤
    3. 去重
    4. 中文分词+去停用词
    5. 构建JSON格式
    """
    print("\n[*] 开始数据处理...")

    cleaned_data = []
    seen_texts = set()  # 用于去重（用前200字hash）
    duplicate_count = 0
    invalid_count = 0

    for item in tqdm(raw_data, desc="  处理进度"):
        # 1. 文本清洗
        cleaned = clean_text(item['content'])

        # 2. 有效性过滤
        if not is_valid_text(cleaned):
            invalid_count += 1
            continue

        # 3. 去重（基于文本前200字的相似度）
        text_hash = hash(cleaned[:200])
        if text_hash in seen_texts:
            duplicate_count += 1
            continue
        seen_texts.add(text_hash)

        # 4. 分词（可选）
        if ENABLE_TOKENIZE:
            tokenized = tokenize_text(cleaned, stopwords)
        else:
            tokenized = cleaned

        # 5. 构建JSON格式
        cleaned_data.append({
            "category": item['category'],
            "content": cleaned,           # 原始清洗后文本
            "tokenized": tokenized,       # 分词后文本
            "length": len(cleaned),       # 原文长度
            "token_length": len(tokenized.split())  # 分词后词数
        })

    print(f"\n[✓] 数据处理完成!")
    print(f"    有效数据: {len(cleaned_data)} 条")
    print(f"    过滤无效: {invalid_count} 条")
    print(f"    去除重复: {duplicate_count} 条")
    print(f"    有效率: {len(cleaned_data) / max(len(raw_data), 1) * 100:.1f}%")

    return cleaned_data


def split_dataset(data: list):
    """
    划分数据集: 训练集70% / 验证集15% / 测试集15%
    按类别分层采样，保证各类别比例一致
    """
    print("\n[*] 划分数据集...")

    # 按类别分组
    category_groups = {}
    for item in data:
        cat = item['category']
        if cat not in category_groups:
            category_groups[cat] = []
        category_groups[cat].append(item)

    train_data, val_data, test_data = [], [], []

    for cat, items in category_groups.items():
        # 打乱
        random.shuffle(items)
        n = len(items)

        # 按比例划分
        n_train = int(n * TRAIN_RATIO)
        n_val = int(n * VAL_RATIO)

        train_data.extend(items[:n_train])
        val_data.extend(items[n_train:n_train + n_val])
        test_data.extend(items[n_train + n_val:])

        print(f"  [{cat}] 总数:{n} → 训练:{n_train} 验证:{n_val} 测试:{n - n_train - n_val}")

    # 再次打乱
    random.shuffle(train_data)
    random.shuffle(val_data)
    random.shuffle(test_data)

    print(f"\n[✓] 数据集划分完成:")
    print(f"    训练集: {len(train_data)} 条 ({len(train_data)/max(len(data),1)*100:.1f}%)")
    print(f"    验证集: {len(val_data)} 条 ({len(val_data)/max(len(data),1)*100:.1f}%)")
    print(f"    测试集: {len(test_data)} 条 ({len(test_data)/max(len(data),1)*100:.1f}%)")

    return train_data, val_data, test_data


def save_json(data: list, filepath: Path, desc: str = ""):
    """保存数据为JSON文件"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    file_size = filepath.stat().st_size / (1024 * 1024)
    print(f"  [✓] {desc}: {filepath} ({len(data)} 条, {file_size:.1f} MB)")


# ============================================
# 5. 统计分析模块
# ============================================

def compute_statistics(data: dict):
    """计算并输出统计信息"""
    print("\n" + "=" * 60)
    print(" 数据集统计信息")
    print("=" * 60)

    stats = {}

    # 总体统计
    all_lengths = [item['length'] for item in data['train']]
    all_token_lengths = [item['token_length'] for item in data['train']]

    stats['total_samples'] = len(data['train']) + len(data['val']) + len(data['test'])
    stats['train_samples'] = len(data['train'])
    stats['val_samples'] = len(data['val'])
    stats['test_samples'] = len(data['test'])

    stats['avg_length'] = np.mean(all_lengths)
    stats['max_length'] = int(np.max(all_lengths))
    stats['min_length'] = int(np.min(all_lengths))
    stats['median_length'] = float(np.median(all_lengths))
    stats['std_length'] = float(np.std(all_lengths))

    stats['avg_token_length'] = np.mean(all_token_lengths)
    stats['max_token_length'] = int(np.max(all_token_lengths))
    stats['min_token_length'] = int(np.min(all_token_lengths))

    # 各类别统计
    category_counts = Counter()
    category_avg_length = {}
    for item in data['train'] + data['val'] + data['test']:
        category_counts[item['category']] += 1

    for cat in category_counts:
        cat_lengths = [item['length'] for item in data['train'] if item['category'] == cat]
        if cat_lengths:
            category_avg_length[cat] = {
                'count': category_counts[cat],
                'avg_length': round(np.mean(cat_lengths), 1)
            }

    stats['category_distribution'] = dict(category_counts)
    stats['category_stats'] = category_avg_length

    # 打印统计结果
    print(f"\n  总样本数:     {stats['total_samples']:,}")
    print(f"  训练集:       {stats['train_samples']:,} ({stats['train_samples']/stats['total_samples']*100:.1f}%)")
    print(f"  验证集:       {stats['val_samples']:,} ({stats['val_samples']/stats['total_samples']*100:.1f}%)")
    print(f"  测试集:       {stats['test_samples']:,} ({stats['test_samples']/stats['total_samples']*100:.1f}%)")

    print(f"\n  文本长度统计:")
    print(f"    平均长度:   {stats['avg_length']:.0f} 字符")
    print(f"    最大长度:   {stats['max_length']:,} 字符")
    print(f"    最小长度:   {stats['min_length']} 字符")
    print(f"    中位数:     {stats['median_length']:.0f} 字符")
    print(f"    标准差:     {stats['std_length']:.0f} 字符")

    print(f"\n  分词后长度统计:")
    print(f"    平均词数:   {stats['avg_token_length']:.0f} 词")
    print(f"    最大词数:   {stats['max_token_length']:,} 词")
    print(f"    最小词数:   {stats['min_token_length']} 词")

    print(f"\n  各类别分布:")
    for cat in sorted(category_counts.keys()):
        count = category_counts[cat]
        bar = '█' * int(count / max(category_counts.values()) * 30)
        print(f"    {cat:6s}  {count:>8,}  {bar}")

    return stats


# ============================================
# 6. 数据可视化模块
# ============================================

def visualize_data(data: dict, stats: dict):
    """生成数据可视化图表"""
    print("\n[*] 生成数据可视化...")

    # 设置中文字体（避免乱码）
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('THUCNews 数据集分析报告', fontsize=18, fontweight='bold', y=0.98)

    # ========== 图1: 类别分布 ==========
    ax1 = axes[0, 0]
    cat_counts = stats['category_distribution']
    categories = sorted(cat_counts.keys(), key=lambda x: cat_counts[x], reverse=True)
    counts = [cat_counts[c] for c in categories]

    colors = sns.color_palette("husl", len(categories))
    bars = ax1.barh(categories, counts, color=colors, edgecolor='white', linewidth=0.8)

    # 在柱状图上标注数值
    for bar, count in zip(bars, counts):
        ax1.text(bar.get_width() + 100, bar.get_y() + bar.get_height()/2,
                 f'{count:,}', va='center', fontsize=9)

    ax1.set_xlabel('样本数量', fontsize=12)
    ax1.set_title('各类别样本分布', fontsize=14, fontweight='bold')
    ax1.invert_yaxis()
    ax1.grid(axis='x', alpha=0.3, linestyle='--')

    # ========== 图2: 文本长度分布（直方图） ==========
    ax2 = axes[0, 1]
    train_lengths = [item['length'] for item in data['train']]

    # 去除离群值（99分位数以上截断）
    p99 = np.percentile(train_lengths, 99)
    lengths_to_plot = [l for l in train_lengths if l <= p99]

    ax2.hist(lengths_to_plot, bins=80, color='#5B9BD5', edgecolor='white',
             alpha=0.8, linewidth=0.3)
    ax2.axvline(np.mean(lengths_to_plot), color='red', linestyle='--',
                linewidth=2, label=f'平均值: {np.mean(lengths_to_plot):.0f} 字符')
    ax2.axvline(np.median(lengths_to_plot), color='orange', linestyle='--',
                linewidth=2, label=f'中位数: {np.median(lengths_to_plot):.0f} 字符')
    ax2.set_xlabel('文本长度 (字符)', fontsize=12)
    ax2.set_ylabel('样本数量', fontsize=12)
    ax2.set_title('文本长度分布 (训练集)', fontsize=14, fontweight='bold')
    ax2.legend(loc='upper right', fontsize=10)
    ax2.grid(axis='y', alpha=0.3, linestyle='--')

    # ========== 图3: 各类别平均长度对比 ==========
    ax3 = axes[1, 0]
    cat_stats = stats['category_stats']
    sorted_cats = sorted(cat_stats.keys(),
                         key=lambda x: cat_stats[x]['avg_length'],
                         reverse=True)
    avg_lengths = [cat_stats[c]['avg_length'] for c in sorted_cats]

    bar_colors = sns.color_palette("viridis", len(sorted_cats))
    ax3.barh(sorted_cats, avg_lengths, color=bar_colors, edgecolor='white',
             linewidth=0.8)
    for i, (cat, length) in enumerate(zip(sorted_cats, avg_lengths)):
        ax3.text(length + 5, i, f'{length:.0f}', va='center', fontsize=9)
    ax3.set_xlabel('平均字符数', fontsize=12)
    ax3.set_title('各类别平均文本长度', fontsize=14, fontweight='bold')
    ax3.invert_yaxis()
    ax3.grid(axis='x', alpha=0.3, linestyle='--')

    # ========== 图4: 长度箱线图 ==========
    ax4 = axes[1, 1]
    box_data = {}
    for cat in sorted(cat_counts.keys())[:8]:  # 最多显示8个类别
        box_data[cat] = [
            item['length'] for item in data['train']
            if item['category'] == cat and item['length'] <= p99
        ]

    bp = ax4.boxplot(box_data.values(), labels=box_data.keys(),
                     patch_artist=True, vert=True,
                     showfliers=False,  # 不显示离群点
                     widths=0.6)

    # 设置箱线图颜色
    box_colors = sns.color_palette("Set2", len(box_data))
    for patch, color in zip(bp['boxes'], box_colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax4.set_ylabel('文本长度 (字符)', fontsize=12)
    ax4.set_title('各主要类别文本长度分布', fontsize=14, fontweight='bold')
    ax4.tick_params(axis='x', rotation=45)
    ax4.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.subplots_adjust(top=0.93)

    # 保存
    viz_path = OUTPUT_DIR / "data_analysis.png"
    plt.savefig(viz_path, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"  [✓] 可视化图表已保存: {viz_path}")

    # 单独生成类别分布饼图（更清晰）
    fig2, ax_pie = plt.subplots(figsize=(10, 10))
    explode = [0.02] * len(categories)
    wedges, texts, autotexts = ax_pie.pie(
        counts,
        labels=categories,
        autopct='%1.1f%%',
        explode=explode,
        colors=sns.color_palette("husl", len(categories)),
        startangle=90,
        pctdistance=0.85
    )
    ax_pie.set_title('THUCNews 类别分布', fontsize=16, fontweight='bold')

    # 中心添加总样本数
    ax_pie.text(0, 0, f'总计\n{sum(counts):,}\n篇',
                ha='center', va='center', fontsize=14, fontweight='bold')

    pie_path = OUTPUT_DIR / "category_pie.png"
    plt.savefig(pie_path, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"  [✓] 类别饼图已保存: {pie_path}")


# ============================================
# 7. 主流程
# ============================================

def main():
    """主流程入口"""
    print("=" * 60)
    print(" NewsMind - THUCNews 数据集预处理")
    print("=" * 60)
    print(f"  数据集路径: {DATA_DIR}")
    print(f"  输出路径:   {OUTPUT_DIR}")
    print(f"  划分比例:   训练{TRAIN_RATIO:.0%} / 验证{VAL_RATIO:.0%} / 测试{TEST_RATIO:.0%}")
    print(f"  随机种子:   {RANDOM_SEED}")
    print("=" * 60)

    # 设置随机种子
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ===== 步骤0: 下载数据集 =====
    print("\n" + "=" * 40)
    print(" 步骤0/6: 准备数据集")
    print("=" * 40)
    if not download_thucnews():
        print("[✗] 数据集未就绪，无法继续。请手动下载后重试。")
        return

    # ===== 步骤1: 加载停用词 =====
    print("\n" + "=" * 40)
    print(" 步骤1/6: 加载停用词表")
    print("=" * 40)
    stopwords = load_stopwords()
    print(f"[✓] 加载了 {len(stopwords)} 个停用词")

    # ===== 步骤2: 读取原始数据 =====
    print("\n" + "=" * 40)
    print(" 步骤2/6: 读取原始数据")
    print("=" * 40)
    raw_data = load_raw_data()

    if not raw_data:
        print("[✗] 未读取到任何数据！请检查 data/THUCNews/ 目录结构。")
        return

    # ===== 步骤3: 数据处理 =====
    print("\n" + "=" * 40)
    print(" 步骤3/6: 文本清洗 + 分词 + 去重")
    print("=" * 40)
    cleaned_data = process_data(raw_data, stopwords)

    # ===== 步骤4: 划分数据集 =====
    print("\n" + "=" * 40)
    print(" 步骤4/6: 划分数据集")
    print("=" * 40)
    train_data, val_data, test_data = split_dataset(cleaned_data)

    # ===== 步骤5: 保存数据 =====
    print("\n" + "=" * 40)
    print(" 步骤5/6: 保存处理结果")
    print("=" * 40)
    save_json(train_data, TRAIN_FILE, "训练集")
    save_json(val_data, VAL_FILE, "验证集")
    save_json(test_data, TEST_FILE, "测试集")

    # 保存统计信息
    all_data = {
        'train': train_data,
        'val': val_data,
        'test': test_data
    }

    stats = compute_statistics(all_data)
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"  [✓] 统计信息已保存: {STATS_FILE}")

    # ===== 步骤6: 数据可视化 =====
    print("\n" + "=" * 40)
    print(" 步骤6/6: 数据可视化")
    print("=" * 40)
    visualize_data(all_data, stats)

    # ===== 输出最终总结 =====
    print("\n" + "=" * 60)
    print(" ✅ 数据预处理全部完成！")
    print("=" * 60)
    print(f"  训练集:    {TRAIN_FILE}      ({len(train_data):,} 条)")
    print(f"  验证集:    {VAL_FILE}        ({len(val_data):,} 条)")
    print(f"  测试集:    {TEST_FILE}       ({len(test_data):,} 条)")
    print(f"  统计信息:  {STATS_FILE}")
    print(f"  可视化:    {OUTPUT_DIR / 'data_analysis.png'}")
    print(f"  饼图:      {OUTPUT_DIR / 'category_pie.png'}")
    print(f"  总样本数:  {len(train_data) + len(val_data) + len(test_data):,} 条")
    print("=" * 60)


if __name__ == "__main__":
    main()
