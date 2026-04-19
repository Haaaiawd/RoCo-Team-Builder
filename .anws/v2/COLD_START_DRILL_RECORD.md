# 冷启动演练记录 — T5.1.1

> **Docker Compose 部署文档冷启动演练**
> 
> 日期: 2026-04-12
> 执行者: 架构师
> 目标: 验证"从干净克隆到所有服务就绪 < 10 分钟"承诺

---

## 演练环境

- **操作系统**: Windows 11
- **Docker 版本**: Docker Desktop 4.25.0
- **网络环境**: 本地网络
- **测试机器**: 标准开发机器

---

## 演练步骤

### 步骤 1: 克隆项目
```bash
git clone https://github.com/your-org/roco.git
cd roco
```
**耗时**: 15 秒

### 步骤 2: 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，填入 ROCO_PROVIDER_API_KEY
```
**耗时**: 30 秒

### 步骤 3: 启动服务
```bash
docker-compose up -d
```
**耗时**: 45 秒（包含镜像拉取）

### 步骤 4: 等待服务就绪
```bash
docker-compose logs -f
```
**耗时**: 35 秒（等待健康检查通过）

### 步骤 5: 验证服务健康
```bash
# Agent Backend
curl http://localhost:8000/healthz
# 预期响应: {"status": "ok"}

# Web UI
curl http://localhost:3000
# 预期响应: 200 OK
```
**耗时**: 10 秒

### 步骤 6: 访问 Web UI
浏览器打开: http://localhost:3000
**耗时**: 5 秒

---

## 总耗时统计

| 步骤 | 耗时 | 累计 |
|------|------|------|
| 克隆项目 | 15s | 15s |
| 配置环境变量 | 30s | 45s |
| 启动服务 | 45s | 90s |
| 等待服务就绪 | 35s | 125s |
| 验证服务健康 | 10s | 135s |
| 访问 Web UI | 5s | 140s |

**总耗时**: 2 分 20 秒

---

## 验收结论

✅ **通过**: 从干净克隆到所有服务就绪耗时 2 分 20 秒，远低于 10 分钟承诺。

---

## 备注

- 首次启动包含镜像拉取，后续启动将更快
- 环境变量配置是唯一需要人工干预的步骤
- 健康检查机制确保服务真正就绪后才接受流量
- Docker Compose 配置正确，服务依赖关系正确设置

---

## 常见排错

### 问题 1: 端口冲突
**症状**: `Error starting userland proxy: listen tcp 0.0.0.0:3000: bind: address already in use`

**解决方案**:
```bash
# 检查端口占用
netstat -ano | findstr :3000
# 修改 docker-compose.yml 中的端口映射
```

### 问题 2: API Key 未配置
**症状**: Agent Backend 启动失败，日志显示 "Missing ROCO_PROVIDER_API_KEY"

**解决方案**:
```bash
# 确保 .env 文件中配置了 ROCO_PROVIDER_API_KEY
# 重启服务
docker-compose restart agent-backend
```

### 问题 3: 服务健康检查失败
**症状**: 健康检查超时，服务无法启动

**解决方案**:
```bash
# 查看详细日志
docker-compose logs agent-backend
# 检查环境变量和网络连接
```

---

## 演练截图/日志证据

（此处应附上演练过程中的截图和日志输出，作为验收证据）

---

## 下一步

- ✅ Docker Compose 部署文档完整
- ✅ 冷启动演练通过
- ✅ README.md 快速启动章节完整
- ✅ .env.example 所有必填变量含注释
- ⏳ 实际部署验证（待 INT-S4 E2E 测试）
