# NewsMind 系统运行配置与 AI 提示词说明

## 一、系统基本信息

项目名称：NewsMind - 基于自然语言处理的新闻文章自动摘要系统

系统功能：系统基于 THUCNews 新闻语料库，完成新闻数据导入、分类浏览、关键词搜索、全文查看、新闻收藏、自动摘要生成、摘要质量反馈和反馈统计等功能。摘要模块采用 BERT 句向量表示、TextRank 关键句抽取和基于 Transformer 的 T5 序列到序列生成模型。

主要技术栈：

- 客户端：HarmonyOS ArkTS
- 后端服务：FastAPI、SQLAlchemy、SQLite
- AI 模型：PyTorch、Hugging Face Transformers
- 摘要流程：BERT-base-chinese + TextRank + Chinese T5
- 数据集：THUCNews 清华新闻语料库
- 评估指标：ROUGE-L、单篇摘要生成耗时、用户反馈评分

## 二、运行环境配置

### 1. 后端运行环境

建议环境：

- Python 3.10 或以上
- Windows 10/11
- pip
- 可选 GPU：支持 CUDA 的 NVIDIA 显卡

安装 Python 依赖：

```bash
pip install -r requirements.txt
```

后端依赖文件：

```text
requirements.txt
```

主要依赖包括：

- fastapi
- uvicorn
- sqlalchemy
- torch
- transformers
- numpy
- scikit-learn
- jieba
- rouge-score

### 2. 前端运行环境

建议环境：

- DevEco Studio
- HarmonyOS 6.1.1 / API 24
- ArkTS 编译环境
- HarmonyOS 模拟器或真机设备

前端主模块：

```text
entry/
```

前端入口页面：

```text
entry/src/main/ets/pages/Index.ets
```

API 地址配置文件：

```text
entry/src/main/ets/api/ApiConfig.ets
```

默认后端地址：

```text
http://10.0.2.2:8000
```

说明：

- HarmonyOS 模拟器访问电脑本机后端时使用 `10.0.2.2`。
- 真机调试时需要将 `BASE_URL` 改为电脑在同一局域网下的 IP，例如 `http://192.168.x.x:8000`。

## 三、数据与模型配置

### 1. 数据集位置

THUCNews 原始数据目录：

```text
data/THUCNews/
```

预处理后数据目录：

```text
data/processed/
```

SQLite 数据库文件：

```text
newsmind.db
```

数据库文件为本地运行生成文件，体积较大，打包源码时可不放入 Git 仓库，但现场验收前需保证本机已导入数据。

### 2. 数据预处理

预处理 THUCNews 数据：

```bash
python data_preprocess.py
```

脚本会生成：

```text
data/processed/train.json
data/processed/val.json
data/processed/test.json
data/processed/statistics.json
```

### 3. 快速重建完整新闻数据库

如需从原始 THUCNews 目录直接重建数据库，可执行：

```bash
python scripts/rebuild_news_db_from_raw.py
```

该脚本会：

- 清空旧新闻、摘要、收藏、历史和反馈数据
- 从 `data/THUCNews/` 读取原始新闻
- 写入 `newsmind.db`
- 建立 SQLite FTS5 全文检索表 `news_fts`
- 建立触发器保证新闻内容和全文索引同步

### 4. 模型目录

训练后的摘要模型默认目录：

```text
trained_models/t5_summarizer_best/
```

后端启动时会优先加载该目录下的微调模型。如果目录不存在，系统会回退到 TextRank 快速摘要模式，以保证演示流程可运行。

AI 配置文件：

```text
backend/ai/config.py
```

关键配置：

```text
BERT_MODEL_NAME = "bert-base-chinese"
T5_MODEL_NAME = "uer/t5-small-chinese-cluecorpussmall"
T5_MAX_INPUT_LENGTH = 512
T5_MAX_TARGET_LENGTH = 128
TEXTRANK_TOP_K = 5
ROUGE_L_THRESHOLD = 0.4
MAX_INFERENCE_TIME = 1.5
SUMMARY_MIN_LENGTH = 30
SUMMARY_MAX_LENGTH = 150
```

## 四、系统启动步骤

### 1. 启动后端服务

在项目根目录执行：

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

启动成功后可访问：

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
```

健康检查接口返回示例：

```json
{
  "status": "ok",
  "message": "NewsMind API is running"
}
```

### 2. 启动 ArkTS 客户端

1. 使用 DevEco Studio 打开项目根目录。
2. 确认后端服务已启动。
3. 检查 `entry/src/main/ets/api/ApiConfig.ets` 中的 `BASE_URL`。
4. 启动 HarmonyOS 模拟器或连接真机。
5. 选择 `entry` 模块运行。

### 3. 验收前检查项

建议现场验收或录制视频前确认：

- 后端 `/health` 能正常访问。
- App 首页能展示新闻列表，数量不再是初始 5 条演示数据。
- 分类筛选能正常返回对应类别新闻。
- 搜索功能能在完整数据量下返回结果。
- 新闻详情页能查看全文。
- 点击收藏后，收藏页能看到对应新闻。
- 点击生成摘要后，能显示抽取式摘要、生成式摘要和耗时。
- 提交摘要评分和文字反馈后，反馈接口能正常写入。
- 若展示模型指标，需提前准备 ROUGE-L 和耗时评估结果。

## 五、主要接口说明

```text
GET    /news                  获取新闻列表，支持分类、关键词和分页
GET    /news/categories/all   获取新闻类别
GET    /news/{news_id}        获取新闻详情
POST   /summary               生成新闻摘要
POST   /favorite              添加收藏
DELETE /favorite              取消收藏
GET    /favorite              获取收藏列表
GET    /history               获取操作历史
POST   /feedback              提交摘要质量反馈
GET    /feedback/stats        获取反馈统计
GET    /health                后端健康检查
```

## 六、AI 摘要流程说明

系统摘要流程如下：

```text
新闻原文
-> 文本清洗
-> 分句
-> BERT-base-chinese 生成句向量
-> TextRank 计算句子重要性
-> 提取 Top-K 关键句
-> T5 Transformer 生成式摘要
-> 质量检查与长度约束
-> 返回抽取式摘要、生成式摘要和生成耗时
```

核心代码位置：

```text
backend/ai/summarizer.py
backend/services/summary_service.py
backend/routers/summary.py
```

训练代码位置：

```text
backend/ai/train.py
```

评估代码位置：

```text
backend/ai/predict.py
```

## 七、AI 提示词说明

本项目没有调用在线大语言模型 API，摘要生成主要依赖本地 Hugging Face Transformers 模型。系统中“提示词”主要指传入 T5 生成模型的任务前缀模板。

### 1. T5 摘要生成提示词模板

代码位置：

```text
backend/ai/summarizer.py
backend/ai/train.py
```

提示词模板：

```text
summarize: {新闻文本或TextRank关键句}
```

含义：

- `summarize:` 是 T5 模型的任务前缀，用于提示模型执行摘要生成任务。
- `{新闻文本或TextRank关键句}` 是待摘要内容。
- 在线推理时，系统优先将 TextRank 提取出的关键句输入 T5，以减少输入长度并提升生成速度。

示例：

```text
summarize: 人工智能技术正在加速应用于新闻编辑、医疗服务和智能制造等场景。多家企业表示，模型部署不仅需要关注准确率，也需要关注响应速度和用户反馈。
```

预期输出：

```text
本文介绍人工智能在多个行业中的应用，并强调模型部署需要兼顾准确率、响应速度和用户反馈。
```

### 2. 训练阶段伪标签生成说明

训练阶段使用 BERT + TextRank 为新闻生成伪摘要标签，再用伪标签微调 T5 模型。

训练样本输入：

```text
summarize: {新闻正文}
```

训练样本目标：

```text
{TextRank提取出的关键句摘要}
```

这样做的目的：

- THUCNews 原始数据没有人工摘要标签。
- TextRank 可从原文中自动提取高重要性句子。
- 将 TextRank 结果作为伪标签，可以构造摘要训练数据。
- T5 模型在伪标签上微调后，可生成更短、更自然的摘要文本。

### 3. TextRank 关键句抽取参数

TextRank 不使用自然语言提示词，而是使用算法参数控制摘要长度和排序逻辑。

主要参数：

```text
TEXTRANK_TOP_K = 5
TEXTRANK_DAMPING = 0.85
TEXTRANK_MAX_ITER = 100
TEXTRANK_CONVERGENCE = 1e-6
TEXTRANK_MIN_SENTENCE_LENGTH = 5
```

说明：

- `TEXTRANK_TOP_K` 控制抽取关键句数量。
- `TEXTRANK_DAMPING` 为 PageRank 阻尼系数。
- 系统通过 BERT 句向量相似度构建句子图，再用 TextRank 排序。

### 4. 摘要质量控制策略

系统对生成摘要做了基础质量控制：

- 摘要为空或过短时回退到 TextRank 摘要。
- 生成结果明显异常时回退到演示摘要或抽取式摘要。
- 摘要过长时按 `SUMMARY_MAX_LENGTH` 截断。
- 摘要与原文过于接近时重新压缩。
- 接口返回 `inference_time`，用于检查单篇摘要生成时间。

### 5. 用户反馈优化说明

用户可在 App 中对摘要质量进行评分并填写文字反馈。反馈数据会写入数据库中的 `feedback` 表。

相关接口：

```text
POST /feedback
GET  /feedback/stats
```

反馈字段包括：

```text
news_id
summary_id
rating
comment
created_at
```

当前系统已实现反馈采集和统计。后续可将低评分摘要加入人工复核集，将高评分摘要作为优质样本，用于下一轮模型微调，从而形成“用户反馈 -> 样本筛选 -> 模型再训练 -> 摘要质量提升”的优化闭环。

## 八、评估指标说明

系统目标指标：

```text
ROUGE-L >= 0.4
单篇摘要生成时间 < 1.5 秒
```

评估命令：

```bash
python -m backend.ai.predict --eval data/processed/test.json
```

评估输出建议保存为：

```text
evaluation_result.json
```

建议在答辩材料中展示：

- 平均 ROUGE-L
- 最大 ROUGE-L
- 最小 ROUGE-L
- 单篇平均生成耗时
- 单篇最大生成耗时
- 是否满足 `ROUGE-L >= 0.4`
- 是否满足 `单篇摘要生成时间 < 1.5 秒`

## 九、源码压缩包建议结构

课程要求压缩包命名格式：

```text
小组长学号-姓名-项目名称-代码.zip
```

建议压缩包至少包含：

```text
NewsMind/
  AppScope/
  entry/
  backend/
  scripts/
  data_preprocess.py
  requirements.txt
  README.md
  系统运行配置与AI提示词说明.md
```

可不放入 Git 仓库或压缩包的大文件：

```text
newsmind.db
data/THUCNews/
data/processed/
trained_models/
*.zip
*.pth
*.bin
*.h5
```

如现场验收使用本机运行，需要提前在本机准备好数据库、模型和数据目录。

