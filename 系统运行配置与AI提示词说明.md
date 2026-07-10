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


## 五、AI 提示词说明

本节中的“AI 提示词”是开发过程中用于指导 AI 辅助完成项目设计、代码实现、模块拆分和阶段交付的开发指令。本项目运行阶段不调用在线大语言模型 API，新闻摘要生成由 Python 后端中的本地 NLP 模型和算法流程完成。

### 1. 开发提示词正文

```text
你是一位资深HarmonyOS开发工程师、Python后端工程师、AI算法工程师和系统架构师。

请帮我完整设计并逐步实现一个真实可运行的HarmonyOS移动应用项目。

项目名称：

《NewsMind——基于自然语言处理的智能新闻文章自动摘要系统设计与实现》

项目最终架构：

HarmonyOS移动APP（ArkTS前端）

⇅ REST API

Python后端（FastAPI）

⇅

BERT + TextRank + Transformer摘要模型

⇅

THUCNews数据集

注意：

ArkTS只负责前端页面和接口调用

Python负责：

- 数据处理
- 模型训练
- 摘要生成
- 数据库
- API

不要将AI模型放在ArkTS端运行。

━━━━━━━━━━━━━━━
【技术栈】
━━━━━━━━━━━━━━━

前端：

- HarmonyOS NEXT
- ArkTS
- ArkUI
- Stage模型
- Navigation
- Axios
- Preferences

后端：

- Python
- FastAPI
- SQLAlchemy
- SQLite

AI：

- HuggingFace Transformers
- BERT
- TextRank
- Transformer Seq2Seq

数据集：

THUCNews

━━━━━━━━━━━━━━━
【第一阶段：数据集处理（优先完成）】
━━━━━━━━━━━━━━━

下载THUCNews后：

请先完成数据预处理流程：

1.读取THUCNews数据集

目录示例：

THUCNews/

├── 科技
├── 体育
├── 财经
├── 娱乐
├── 教育
├── 时政

2.文本清洗：

实现：

- 去HTML标签
- 去特殊字符
- 去空白字符
- 去URL
- 去重复数据

3.中文分词：

使用：

jieba

4.停用词处理：

去除停用词

5.构建训练集：

输出：

train.json

格式：

{
    "category":"科技",
    "content":"新闻正文"
}

6.划分数据集：

训练集：

70%

验证集：

15%

测试集：

15%

7.统计数据：

输出：

- 各类别数量
- 平均文本长度
- 最大长度
- 最小长度

8.数据可视化：

生成：

- 类别分布图
- 文本长度分布图

要求：

输出完整Python代码

文件名：

data_preprocess.py

必须可直接运行

添加中文注释

━━━━━━━━━━━━━━━
【第二阶段：AI摘要模块】
━━━━━━━━━━━━━━━

实现：

新闻文本

↓

文本清洗

↓

BERT向量表示

↓

TextRank提取关键句

↓

Transformer生成摘要

↓

ROUGE-L评估

要求：

ROUGE-L≥0.4

单篇摘要时间：

<1.5秒

输出：

完整训练代码：

train.py

完整预测代码：

predict.py

模型保存代码：

save_model.py

━━━━━━━━━━━━━━━
【第三阶段：Python后端】
━━━━━━━━━━━━━━━

使用：

FastAPI

设计接口：

GET /news

GET /news/{id}

POST /summary

POST /favorite

DELETE /favorite

GET /history

POST /feedback

输出：

请求参数

JSON返回格式

完整代码

━━━━━━━━━━━━━━━
【第四阶段：HarmonyOS前端】
━━━━━━━━━━━━━━━

APP名称：

NewsMind

页面：

1 首页

功能：

- 新闻分类
- 搜索
- 新闻列表
- 下拉刷新

2 新闻详情页

功能：

- 正文展示
- 一键生成摘要
- 收藏
- 分享

3 收藏页

4 我的页面

使用：

- ArkTS
- ArkUI
- Navigation
- Tabs
- List
- Grid

输出完整：

页面代码

组件代码

接口调用代码

文件名必须标明

━━━━━━━━━━━━━━━
【项目目录结构】
━━━━━━━━━━━━━━━

NewsMind

├── frontend
│   ├── pages
│   ├── components
│   ├── api
│   └── utils

├── backend
│   ├── routers
│   ├── models
│   ├── services
│   ├── ai
│   └── database

├── data
│   └── THUCNews

├── trained_models

└── docs

━━━━━━━━━━━━━━━
【输出要求】
━━━━━━━━━━━━━━━

1 不允许伪代码

2 每个文件标注文件名

3 每段代码添加中文注释

4 每完成一步暂停

5 从第一阶段数据处理开始

6 不允许跳步骤
```

### 2. 提示词作用说明

该提示词用于约束 AI 辅助开发时的项目方向和交付顺序，重点包括：

- 明确 NewsMind 的总体架构为 HarmonyOS ArkTS 前端、FastAPI 后端和 Python AI 摘要模块。
- 明确 ArkTS 只负责页面展示和 REST API 调用，AI 模型、数据库、训练和摘要生成均放在 Python 后端。
- 明确开发顺序从 THUCNews 数据预处理开始，再实现摘要模块、后端接口和前端页面。
- 明确每个阶段需要输出真实可运行代码，避免只给伪代码或跳过关键实现。


