# NewsMind - 智能新闻摘要 App

NewsMind 是一个基于 HarmonyOS ArkTS 的新闻摘要应用。系统使用 THUCNews 新闻语料库作为数据来源，后端基于 HuggingFace Transformers 实现 BERT 句向量、TextRank 关键句抽取和 Transformer Seq2Seq 生成式摘要，App 端支持新闻分类浏览、全文查看、收藏、摘要生成和摘要质量反馈。

## 技术栈

- App: HarmonyOS 6.1.1 / API 24 / ArkTS
- 后端: FastAPI / SQLAlchemy / SQLite
- 模型: PyTorch / HuggingFace Transformers
- 摘要流程: BERT-base-chinese + TextRank + Chinese T5
- 数据集: THUCNews
- 评估指标: ROUGE-L、单篇摘要生成耗时、用户评分反馈

## 项目结构

```text
NewsMind/
├── AppScope/                 # HarmonyOS 应用全局配置
├── entry/                    # ArkTS App 主模块
│   └── src/main/ets/
│       ├── api/              # 后端接口封装
│       ├── components/       # 通用组件
│       ├── models/           # 前端数据模型
│       └── pages/            # 首页、详情页、收藏页等
├── backend/                  # FastAPI 后端
│   ├── ai/                   # BERT、TextRank、T5、训练和评估
│   ├── routers/              # API 路由
│   ├── services/             # 业务逻辑
│   └── models/               # 数据库模型
├── data/                     # THUCNews 与处理后数据
├── data_preprocess.py        # THUCNews 预处理脚本
└── requirements.txt          # Python 后端依赖
```

## 已实现功能

- 新闻列表、分类筛选、关键词搜索
- 新闻详情与全文查看
- 一键生成抽取式摘要和生成式摘要
- 收藏、取消收藏、收藏列表
- 阅读历史和摘要生成历史
- 摘要评分与文字反馈
- ROUGE-L 评估脚本和生成耗时统计

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

执行预处理脚本：

```bash
python data_preprocess.py
```

脚本会尝试下载 THUCNews 并生成处理后的数据文件：

```text
data/processed/train.json
data/processed/val.json
data/processed/test.json
```

如果自动下载失败，请手动下载 THUCNews，并将原始数据放到：

```text
data/THUCNews/
```

数据处理完成后，启动后端并调用导入接口：

```text
POST http://127.0.0.1:8000/admin/import-data
```

## 模型训练与评估

训练摘要模型：

```bash
python -m backend.ai.train
```

训练脚本会使用 BERT + TextRank 为新闻生成伪摘要标签，并微调 T5 生成式摘要模型。默认保存目录：

```text
trained_models/t5_summarizer_best/
```

后端启动时会优先加载该微调模型。若该目录不存在，系统会进入 TextRank 快速摘要模式，保证 App 本地演示可以快速运行；训练出微调模型后，无需修改 App，后端会自动启用 T5 生成式摘要。

评估 ROUGE-L 与推理耗时：

```bash
python -m backend.ai.predict --eval data/processed/test.json
```

项目目标：

```text
ROUGE-L >= 0.4
单篇摘要生成时间 < 1.5 秒
```

建议将最终评估输出截图或整理为 `evaluation_result.json`，用于课程报告和答辩展示。

## App 运行

1. 使用 DevEco Studio 打开项目根目录。
2. 确认后端服务已启动。
3. 根据运行环境检查 `ApiConfig.ets` 中的 `BASE_URL`。
4. 连接 HarmonyOS 设备或启动模拟器。
5. 点击 Run 运行 App。

## 主要接口

```text
GET    /news                  新闻列表
GET    /news/categories/all   新闻类别
GET    /news/{news_id}        新闻详情
POST   /summary               生成摘要
POST   /favorite              添加收藏
DELETE /favorite              取消收藏
GET    /favorite              收藏列表
GET    /history               操作历史
POST   /feedback              提交摘要反馈
GET    /feedback/stats        反馈统计
```

## 验收说明

本项目采用 ArkTS 实现 App 端，满足“使用 ArkTS 或仓颉语言编写”的要求；NLP 模型服务采用 Python + HuggingFace Transformers 实现，便于加载 BERT、T5 等预训练模型。系统端到端流程为：

```text
THUCNews -> 文本清洗 -> BERT 句向量 -> TextRank 关键句 -> T5 生成摘要 -> App 分类展示与反馈
```

答辩前请重点确认：

- 已生成并导入 THUCNews 处理后数据
- 后端能正常启动并访问 `/docs`
- App 能拉取新闻、生成摘要、收藏和提交反馈
- 已跑出 ROUGE-L 与耗时评估结果
- README、报告或 PPT 中包含最终指标截图
