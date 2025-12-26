# Railway + Vercel 部署指南

本指南帮助你将 Open Notebook + ACM Agent 部署到云端。

## 架构概览

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Vercel        │     │   Railway       │     │   Railway       │
│   (Frontend)    │────▶│   (Backend)     │────▶│   (SurrealDB)   │
│   Next.js       │     │   FastAPI       │     │   Database      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 费用

| 服务 | 免费额度 |
|------|----------|
| Vercel | 100GB 带宽/月 |
| Railway | $5/月 (约 500 小时运行时间) |

---

## 第一步：注册账户

### 1.1 Railway
1. 打开 https://railway.app
2. 点击 "Login with GitHub"
3. 授权 GitHub 访问

### 1.2 Vercel
1. 打开 https://vercel.com
2. 点击 "Sign Up with GitHub"
3. 授权 GitHub 访问

---

## 第二步：部署 SurrealDB (Railway)

### 2.1 创建新项目
1. 登录 Railway Dashboard
2. 点击 "New Project"
3. 选择 "Deploy a Template"
4. 搜索 "SurrealDB" 并选择
5. 点击 "Deploy"

### 2.2 配置 SurrealDB
部署后，进入 SurrealDB 服务设置：

**Variables（环境变量）**:
```
SURREAL_USER=root
SURREAL_PASS=your_secure_password
```

### 2.3 获取连接信息
1. 点击 SurrealDB 服务
2. 进入 "Settings" → "Networking"
3. 记录 Public URL，格式类似：
   ```
   surrealdb-production-xxxx.up.railway.app
   ```

---

## 第三步：部署 Backend (Railway)

### 3.1 从 GitHub 部署
1. 在同一个 Railway 项目中
2. 点击 "New Service" → "GitHub Repo"
3. 选择 `hongping-zh/open-notebook`
4. Railway 会自动检测 `railway.toml` 配置

### 3.2 配置环境变量
在 Backend 服务的 Variables 中添加：

```
# API 配置
API_HOST=0.0.0.0
API_PORT=5055
API_RELOAD=false

# SurrealDB 连接（使用 Railway 内部网络）
SURREAL_URL=ws://surrealdb.railway.internal:8000/rpc
SURREAL_USER=root
SURREAL_PASSWORD=your_secure_password
SURREAL_NAMESPACE=open_notebook
SURREAL_DATABASE=production

# LLM API Key（可选，用于 Chat 功能）
DEEPSEEK_API_KEY=sk-your-key-here
```

### 3.3 获取 Backend URL
部署完成后，记录 Public URL：
```
https://open-notebook-production-xxxx.up.railway.app
```

---

## 第四步：部署 Frontend (Vercel)

### 4.1 导入项目
1. 登录 Vercel Dashboard
2. 点击 "Add New" → "Project"
3. 选择 `hongping-zh/open-notebook`
4. **重要**：设置 Root Directory 为 `frontend`

### 4.2 配置环境变量
在 Vercel 项目设置中添加：

```
API_URL=https://open-notebook-production-xxxx.up.railway.app
NEXT_PUBLIC_API_URL=https://open-notebook-production-xxxx.up.railway.app
```

### 4.3 部署
点击 "Deploy"，等待构建完成。

---

## 第五步：验证部署

### 5.1 测试 Backend API
```bash
curl https://your-backend-url.railway.app/api/health
```

### 5.2 测试 ACM Agent
```bash
curl "https://your-backend-url.railway.app/api/agent/acm/search?query=deep+learning&limit=3"
```

### 5.3 访问 Frontend
打开 Vercel 提供的 URL，如：
```
https://open-notebook-xxx.vercel.app
```

---

## 常见问题

### Q: Railway 免费额度用完怎么办？
A: Railway 提供 $5/月免费额度。如果用完，可以：
- 升级到付费计划
- 使用 Render.com 作为替代

### Q: 如何更新部署？
A: 推送代码到 GitHub 后，Railway 和 Vercel 会自动重新部署。

### Q: CORS 错误怎么解决？
A: 确保 Backend 的 CORS 配置允许 Vercel 域名。

---

## 相关链接

- [Railway 文档](https://docs.railway.app/)
- [Vercel 文档](https://vercel.com/docs)
- [SurrealDB 文档](https://surrealdb.com/docs)
