# NewsMind - 新闻摘要助手

基于 HarmonyOS 的智能新闻摘要应用，帮助用户快速获取新闻要点。

## 技术栈

- **平台**: HarmonyOS 6.1.1 (API 24)
- **语言**: ArkTS
- **构建工具**: Hvigor (DevEco Studio)
- **Bundle**: `com.newsmind.app`

## 项目结构

```
NewsMind/
├── AppScope/           # 应用全局配置和资源
│   └── app.json5       # 应用包名、版本号、图标等
├── entry/              # 主模块
│   └── src/main/
│       ├── ets/        # ArkTS 源代码
│       │   ├── entryability/  # Ability 入口
│       │   └── pages/         # 页面
│       └── module.json5       # 模块配置
├── build-profile.json5 # 构建配置
├── hvigor/             # Hvigor 构建配置
└── oh-package.json5    # 依赖管理
```

## 开始开发

### 环境要求

- [DevEco Studio](https://developer.huawei.com/consumer/cn/deveco-studio/) (6.0+)
- HarmonyOS SDK (API 24)

### 克隆项目

```bash
git clone https://github.com/satzu0228/NewsMind.git
cd NewsMind
```

用 DevEco Studio 打开项目目录即可开始开发。

### 构建运行

在 DevEco Studio 中：
1. 连接 HarmonyOS 设备或启动模拟器
2. 点击 **Run** 按钮运行应用

## 分支策略

- `main` - 稳定发布分支
- `develop` - 开发主分支
- `feature/*` - 功能开发分支
- `fix/*` - 问题修复分支

## 团队成员

| 角色 | GitHub |
|------|--------|
| 项目负责人 | [@satzu0228](https://github.com/satzu0228) |

## 许可证

MIT License
