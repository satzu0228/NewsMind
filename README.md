# NewsMind - 智能新闻摘要 App

NewsMind 是一个基于 HarmonyOS ArkTS 的中文新闻自动摘要系统。系统使用 THUCNews 清华新闻语料库作为数据来源，后端基于 Hugging Face Transformers 实现 BERT 句向量表示、TextRank 关键句抽取和 T5 Transformer 生成式摘要，客户端支持新闻分类浏览、关键词搜索、全文查看、收藏、摘要生成和摘要质量反馈。

## 技术栈

- 客户端：HarmonyOS 6.1.1 / API 24 / ArkTS
- 后端：FastAPI / SQLAlchemy / SQLite
- AI 模型：PyTorch / Hugging Face Transformers
- 摘要流程：BERT-base-chinese + TextRank + Chinese T5
- 数据集：THUCNews
- 评估指标：ROUGE-L、单篇摘要生成耗时、用户评分反馈

## 项目结构

```text
NewsMind/
├── AppScope/                 # HarmonyOS 应用全局配置
├── entry/                    # ArkTS App 主模块
│   └── src/main/ets/
│       ├── api/              # 后端接口封装
│       ├── components/       # 通用组件
│       ├── models/           # 前端数据模型
│       └── pages/            # 首页、详情页、收藏页、反馈页等
├── backend/                  # FastAPI 后端
│   ├── ai/                   # BERT、TextRank、T5、训练和评估
│   ├── routers/              # API 路由
│   ├── services/             # 业务逻辑
│   └── models/               # 数据库模型
├── scripts/                  # 数据导入、数据库重建、演示数据脚本
├── data/                     # THUCNews 与处理后数据，本地大文件不入库
├── data_preprocess.py        # THUCNews 预处理脚本
├── requirements.txt          # Python 后端依赖
└── 系统运行配置与AI提示词说明.md
```

## 已实现功能

- 新闻列表、分类筛选、关键词搜索和分页加载
- 基于 SQLite FTS5 的完整数据全文检索
- 新闻详情与全文查看
- 一键生成抽取式摘要和生成式摘要
- 收藏、取消收藏、收藏列表
- 阅读历史和摘要生成历史
- 摘要评分与文字反馈
- ROUGE-L 评估函数、模型评估脚本和生成耗时统计
- 系统运行配置与 AI 提示词说明文档

## 后端运行

建议先创建 Python 虚拟环境，再安装依赖：

```bash
pip install -r requirements.txt
```

启动后端服务：

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

启动后可访问：

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/health
```

App 默认后端地址在 `entry/src/main/ets/api/ApiConfig.ets` 中配置。模拟器通常使用 `http://10.0.2.2:8000` 访问电脑本机后端；真机调试时需要改成电脑局域网 IP。

## THUCNews 数据准备

项目支持两种数据准备方式。

### 方式一：从原始 THUCNews 重建完整数据库

将 THUCNews 原始数据放到：

```text
data/THUCNews/
```

目录结构示例：

```text
data/THUCNews/
├── 体育/
├── 娱乐/
├── 家居/
├── 教育/
├── 科技/
└── ...
```

执行：

```bash
python scripts/rebuild_news_db_from_raw.py
```

该脚本会从原始 THUCNews 目录读取新闻，重建 `newsmind.db`，并创建 `news_fts` 全文检索表。完整数据量较大时推荐使用这个方式。

### 方式二：生成训练/验证/测试 JSON

执行预处理脚本：

```bash
python data_preprocess.py
```

脚本会尝试下载 THUCNews，并生成：

```text
data/processed/train.json
data/processed/val.json
data/processed/test.json
data/processed/statistics.json
```

如需将处理后的 JSON 导入数据库，可启动后端后调用：

```text
POST http://127.0.0.1:8000/admin/import-data
```

注意：该接口适合小规模或预处理数据导入。完整 THUCNews 数据验收时，推荐使用 `scripts/rebuild_news_db_from_raw.py`。

## 模型训练与评估

训练摘要模型：

```bash
python -m backend.ai.train
```

训练脚本会使用 BERT + TextRank 为新闻生成伪摘要标签，并微调 T5 生成式摘要模型。默认保存目录：

```text
trained_models/t5_summarizer_best/
```

后端启动时会优先加载该微调模型。若该目录不存在，系统会进入 TextRank 快速摘要模式，保证 App 本地演示可以运行；训练出微调模型后，无需修改 App，后端会自动启用 T5 生成式摘要。

评估 ROUGE-L 与推理耗时：

```bash
python -m backend.ai.predict --eval data/processed/test.json
```

项目目标：

```text
ROUGE-L >= 0.4
单篇摘要生成时间 < 1.5 秒
```

建议将最终评估输出截图，或整理为 `evaluation_result.json`，用于课程报告、PPT 和现场验收展示。

## App 运行

1. 使用 DevEco Studio 打开项目根目录。
2. 确认后端服务已启动。
3. 检查 `entry/src/main/ets/api/ApiConfig.ets` 中的 `BASE_URL`。
4. 启动 HarmonyOS 模拟器或连接真机。
5. 选择 `entry` 模块运行 App。

## 主要接口

```text
GET    /news                  新闻列表，支持分类、关键词和分页
GET    /news/categories/all   新闻类别
GET    /news/{news_id}        新闻详情
POST   /summary               生成摘要
POST   /favorite              添加收藏
DELETE /favorite              取消收藏
GET    /favorite              收藏列表
GET    /history               操作历史
POST   /feedback              提交摘要反馈
GET    /feedback/stats        反馈统计
GET    /health                后端健康检查
```

## AI 提示词与说明文档

本项目没有调用在线大语言模型 API，摘要生成主要依赖本地 Hugging Face Transformers 模型。T5 生成模型使用的任务前缀模板为：

```text
summarize: {新闻文本或TextRank关键句}
```

课程提交要求中的“系统运行配置与 AI 提示词说明”已单独整理在：

```text
系统运行配置与AI提示词说明.md
```

该文档包含运行环境、启动步骤、数据与模型路径、AI 摘要流程、T5 提示词模板、TextRank 参数、反馈优化说明和源码压缩包建议结构。

## 验收说明

本项目采用 ArkTS 实现 App 端，满足“使用 ArkTS 或仓颉语言编写”的要求；NLP 模型服务采用 Python + Hugging Face Transformers 实现，便于加载 BERT、T5 等预训练模型。系统端到端流程为：

```text
THUCNews -> 文本清洗 -> BERT 句向量 -> TextRank 关键句 -> T5 生成摘要 -> App 分类展示与反馈
```

答辩或录制视频前请重点确认：

- 已准备并导入 THUCNews 数据，首页不再只显示初始演示数据。
- 后端能正常启动并访问 `/docs`、`/health`。
- App 能拉取新闻、搜索新闻、生成摘要、收藏新闻和提交反馈。
- `trained_models/t5_summarizer_best/` 存在时，后端会优先加载微调模型。
- 已跑出 ROUGE-L 与耗时评估结果。
- 压缩包中包含 `系统运行配置与AI提示词说明.md`。

