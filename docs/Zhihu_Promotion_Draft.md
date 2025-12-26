# 知乎宣传草稿：ACM Scholar Agent

---

## 标题选项

1. **开源神器！一键搜索下载 ACM 论文，还能 AI 问答 | Open Notebook**
2. **科研人必备：免费搜索 ACM 论文 + AI 阅读助手，开源可自部署**
3. **告别论文下载难题！ACM Scholar Agent 让学术研究更高效**

---

## 正文

### 🎯 痛点：科研人的论文管理困境

作为科研工作者，你是否遇到过这些问题？

- 🔍 **找论文难** - ACM 数字图书馆没有好用的搜索 API
- 💰 **下载要钱** - 很多论文需要付费或机构订阅
- 📚 **管理混乱** - 下载的 PDF 散落各处，找不到重点
- 🤖 **阅读费时** - 一篇论文几十页，快速理解核心内容很难

**现在，这些问题都有解决方案了！**

---

### 🚀 ACM Scholar Agent：你的学术研究助手

我基于开源项目 **Open Notebook** 开发了 **ACM Scholar Agent**，专门解决学术论文的搜索、下载和阅读问题。

#### ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 🔍 **智能搜索** | 通过 OpenAlex API 搜索 ACM 论文，自动过滤开放获取版本 |
| 📥 **一键下载** | 自动从 arXiv 等可信源下载 PDF，无需手动操作 |
| 📖 **内容提取** | 自动解析 PDF，提取文本内容并建立索引 |
| 💬 **AI 问答** | 基于论文内容与 AI 对话，快速理解核心观点 |

#### 🎬 演示视频

👉 [点击观看 Demo](https://drive.google.com/file/d/1xPVI2EUEtvbNSVgpg4eQ4xNrG4IyGrD2/view)

---

### 💡 为什么选择 ACM Scholar Agent？

#### 1️⃣ 完全免费 & 开源

- 基于 MIT 协议开源
- 搜索功能无需任何 API Key
- 可自行部署，数据完全私有

#### 2️⃣ 专注 ACM + 计算机科学

- 精准过滤 ACM 出版物
- 聚焦计算机科学领域
- 优先返回高引用论文

#### 3️⃣ 智能 PDF 源选择

- 自动识别可下载的开放获取版本
- 优先从 arXiv、PubMed Central 等可信源下载
- 避免付费墙和下载限制

#### 4️⃣ 与 AI 深度集成

- 支持 DeepSeek、OpenAI、Ollama 等多种 LLM
- 基于论文内容的精准问答
- 本地部署 Ollama 可实现完全离线使用

---

### 🛠️ 快速开始

#### 项目地址

🔗 **GitHub**: https://github.com/hongping-zh/open-notebook

#### 环境要求

- Python 3.10+
- Node.js 18+
- SurrealDB

#### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/hongping-zh/open-notebook.git
cd open-notebook

# 2. 安装后端依赖
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -e .

# 3. 安装前端依赖
cd frontend
npm install

# 4. 启动服务
# 终端1: surreal start --user root --pass root file:data/surreal
# 终端2: python run_api.py
# 终端3: cd frontend && npm run dev

# 5. 打开浏览器访问 http://localhost:3000
```

#### 详细安装指南

📖 [完整测试指南](https://github.com/hongping-zh/open-notebook/blob/main/docs/ACM_AGENT_TESTING_GUIDE.md)

---

### 📸 功能截图

**搜索论文**
- 输入关键词，如 "Large Language Models"
- 自动返回 ACM 开放获取论文列表
- 显示标题、年份、期刊、引用数

**一键添加**
- 点击 "+ Add" 即可下载论文
- 自动提取 PDF 内容
- 建立向量索引，支持语义搜索

**AI 问答**
- 问："这篇论文的主要贡献是什么？"
- AI 基于论文内容给出精准回答
- 支持多轮对话深入讨论

---

### 🤝 参与贡献

这个项目正在积极开发中，欢迎：

- ⭐ **Star** 项目支持
- 🐛 提交 **Issue** 反馈问题
- 🔧 提交 **PR** 贡献代码
- 💬 分享使用体验

---

### 📬 联系方式

- **GitHub**: https://github.com/hongping-zh/open-notebook
- **原项目**: https://github.com/lfnovo/open-notebook
- **PR #354**: https://github.com/lfnovo/open-notebook/pull/354

---

### 🏷️ 标签建议

`#开源` `#学术研究` `#论文管理` `#ACM` `#AI助手` `#RAG` `#知识管理` `#科研工具` `#LLM应用`

---

## 结语

如果你是科研工作者、学生或对学术论文管理有需求的朋友，欢迎试用 **ACM Scholar Agent**！

有任何问题或建议，欢迎在评论区交流，或直接在 GitHub 提 Issue。

**让我们一起让学术研究更高效！** 🚀

---

*本项目基于 Open Notebook 开发，感谢原作者 @lfnovo 的开源贡献。*
