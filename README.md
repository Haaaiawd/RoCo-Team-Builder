# RoCo Team Builder

> **复古冒险者手账风 AI 配队助手**
> 
> 一个面向公网用户的垂类 AI 产品，专注于精灵配队场景，提供截图识别、资料卡片、多模态交互等能力。

---

## 🚀 快速启动（≤ 10 分钟）

### 前置要求
- Docker Desktop（Windows/Mac）或 Docker Compose（Linux）
- OpenRouter API Key（或其他 OpenAI 兼容 Provider 的 API Key）

### 启动步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/your-org/roco.git
   cd roco
   ```

2. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入你的 ROCO_PROVIDER_API_KEY
   ```

3. **启动服务**
   ```bash
   docker-compose up -d
   ```

4. **等待服务就绪**（约 30-60 秒）
   ```bash
   docker-compose logs -f
   # 等待看到 "Application startup complete"
   ```

5. **访问 Web UI**
   ```
   http://localhost:3000
   ```

6. **配置内置连接**（首次使用）
   - 在 Web UI 中进入 Settings → Connections
   - 添加 OpenAI 兼容连接
   - Base URL: `http://agent-backend:8000/v1`
   - API Key: 使用 .env 中的 ROCO_PROVIDER_API_KEY

7. **开始使用**
   - 选择模型（如 `roco-agent`）
   - 发送配队请求或上传截图

8. **（可选）配置 BYOK**
   - 在 Web UI 中进入 Settings → Direct Connections
   - 添加你自己的 OpenAI 兼容 Provider

9. **查看日志**
   ```bash
   docker-compose logs agent-backend
   docker-compose logs web-ui
   ```

10. **停止服务**
    ```bash
    docker-compose down
    ```

---

## 📁 项目结构

```
roco/
├── src/
│   ├── web-ui-shell/          # Web UI 壳层定制
│   ├── agent_backend/         # Agent 后端
│   ├── data_layer/            # 数据层
│   └── spirit_card/           # 精灵卡片生成器
├── .anws/                     # 架构文档
├── tests/                     # 测试文件
├── docker-compose.yml         # Docker Compose 配置
├── .env.example              # 环境变量示例
└── README.md                  # 本文件
```

---

## 🔧 开发指南

### 安装依赖
```bash
# Python 依赖
cd src/agent_backend
pip install -r requirements.txt

# 前端依赖（如需修改 Web UI）
cd src/web-ui-shell
npm install
```

### 运行测试
```bash
# 后端测试
cd src/agent_backend
pytest

# 前端测试（当前尚未配置测试环境）
# 详见 src/web-ui-shell/README.md
```

---

## 📖 架构文档

详细的架构设计文档位于 `.anws/v2/` 目录：
- `01_PRD.md` — 产品需求文档
- `02_ARCHITECTURE_OVERVIEW.md` — 架构总览
- `03_ADR/` — 架构决策记录
- `04_SYSTEM_DESIGN/` — 系统设计文档
- `05_TASKS.md` — 任务清单

---

## 🎨 视觉风格

产品采用"复古冒险者手账风"视觉设计：
- 炭黑侧栏 + 撕纸边缘
- 羊皮纸主区 + 地图纹理
- 暖金高亮 + 虚线内框
- 用户气泡纸贴片效果
- Agent 文本书写风格

详见：`src/web-ui-shell/branding/theme-override.css`

---

## 🐳 部署

### 生产部署
```bash
# 使用生产配置
docker-compose -f docker-compose.yml up -d
```

### 健康检查
```bash
# Agent Backend
curl http://localhost:8000/healthz

# Web UI
curl http://localhost:3000
```

---

## 📝 许可证

MIT License

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request。

---

## 📧 联系方式

- 项目主页: https://github.com/your-org/roco
- 问题反馈: https://github.com/your-org/roco/issues
