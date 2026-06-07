# WorkBuddy 工作流编排器 & 运营仪表盘 — 问题清单与解决方案

> 生成日期：2026-06-07 | 版本 v1.0

---

## 一、已解决的问题

| # | 问题描述 | 原因 | 解决方案 | 状态 |
|---|---------|------|---------|------|
| 1 | Demo HTML 双击打不开 | `file://` 协议下浏览器阻止加载外部CDN资源（Chrome安全策略） | 启动HTTP服务器托管文件，通过 `http://localhost:8080` 访问 | ✅ 已解决 |
| 2 | Python HTTP服务器启动超时 | `python -m http.server` 在前台运行不返回，导致工具超时 | 改用 `start` 命令后台启动，或使用 `npx serve` | ✅ 已解决 |
| 3 | FastAPI后端依赖编译失败 | `pydantic-core` 需要Rust/C++编译器，Windows缺少工具链 | 方案A：用Flask替代（但仍有emoji编码问题）→ 方案B：纯前端方案+Python桥接 | ✅ 已绕过 |
| 4 | Windows GBK编码问题 | 后端Python代码含emoji，控制台输出时GBK编码报错 | 移除emoji字符，保留纯文本输出 | ✅ 已解决 |

---

## 二、当前待解决的问题

| # | 问题描述 | 优先级 | 影响范围 | 建议方案 |
|---|---------|--------|---------|---------|
| 5 | 仪表盘数据为模拟数据，非真实数据 | 🔴 高 | KPI驾驶舱、成本追踪面板 | 需连接 `orchestrator.py` 和 `data_monitor.py` 获取真实数据 |
| 6 | 工作流编辑器无法保存/加载工作流配置 | 🔴 高 | 工作流编排器 | 需添加 LocalStorage 持久化存储，支持导出/导入JSON |
| 7 | 跨平台数据抓取依赖Playwright，需登录态 | 🟡 中 | 多平台数据总览 | 复用 `3_auto_publish.py` 的登录态，定时抓取 |
| 8 | 缺少用户认证/权限控制 | 🟡 中 | 所有Web模块 | 内网使用可暂缓，外网需添加简单Token认证 |
| 9 | 无持久化数据库，重启丢失数据 | 🟡 中 | KPI历史趋势 | 使用SQLite存储（参考 `ai_super_employee.py` 的 `video_data.db`） |
| 10 | 前端无响应式断线重连 | 🟢 低 | 所有Web模块 | 添加fetch重试机制 + WebSocket心跳（可选） |
| 11 | Seedance/火山引擎API费用无自动统计 | 🟡 中 | 成本追踪面板 | 在API调用处添加日志记录，定期汇总 |
| 12 | 异常预警阈值硬编码 | 🟢 低 | 异常预警面板 | 将阈值配置外化到 `config.json` |

---

## 三、集成方案：Web仪表盘 ↔ orchestrator.py

### 3.1 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    浏览器 (Web 仪表盘)                        │
│  ┌───────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │KPI驾驶舱  │ │成本追踪  │ │多平台总览│ │工作流编排器  │  │
│  └─────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘  │
│        │              │            │               │         │
│        └──────────────┴────────────┴───────────────┘         │
│                         │ HTTP JSON API                      │
└─────────────────────────┼───────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────┐
│           integration_bridge.py (端口8100)                    │
│  ┌──────────────────────┴───────────────────────────────┐   │
│  │  GET /api/kpi    →  get_kpi_data()                   │   │
│  │  GET /api/cost   →  get_cost_data()                  │   │
│  │  GET /api/alerts →  get_alerts()                     │   │
│  │  GET /api/status →  get_api_status()                 │   │
│  │  POST /api/workflow/run → run_workflow()             │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                          │                                   │
│                  调用 orchestrator.py                        │
│                  读取 config.json                            │
│                  读取 publish_history.json                   │
│                  扫描 final_videos/ 目录                     │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────┐
│                  orchestrator.py (核心引擎)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │文案生成  │→ │视频制作  │→ │自动发布  │→ │数据监控   │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 启动步骤

```bash
# 步骤1：启动集成桥接（一次性）
cd D:\WB_Workflow
C:\Users\Confu\AppData\Local\Programs\Python\Python314\python.exe integration_bridge.py --port 8100

# 步骤2：浏览器访问
# http://localhost:8100/            → 统一仪表盘
# http://localhost:8100/api/status  → 系统状态API
# http://localhost:8100/api/kpi     → KPI数据API

# 步骤3（可选）：触发工作流
curl -X POST http://localhost:8100/api/workflow/run \
  -H "Content-Type: application/json" \
  -d '{"product":"测试产品","method":"concat","dry_run":true}'
```

### 3.3 API端点说明

| 端点 | 方法 | 说明 | 示例响应 |
|------|------|------|---------|
| `/api/status` | GET | 系统运行状态、文件统计 | `{"status":"running","files":{"final_videos":{"file_count":8}}}` |
| `/api/kpi` | GET | 多平台KPI指标 | `{"summary":{"total_views":123456},"platforms":{...}}` |
| `/api/cost` | GET | API费用明细 | `{"current_month":{"total_cost":580},"services":[...]}` |
| `/api/alerts` | GET | 异常预警列表 | `{"alerts":[{"level":"danger","title":"..."}]}` |
| `/api/workflow/run` | POST | 触发工作流执行 | `{"success":true,"stdout":"..."}` |

---

## 四、待交付文件清单

| 文件 | 路径 | 状态 | 说明 |
|------|------|------|------|
| 工作流编排器Demo | `D:\WB_Workflow\workflow_editor_demo.html` | ✅ 已创建 | React+ReactFlow 可视化编排 |
| 统一仪表盘 | `D:\WB_Workflow\dashboard_unified.html` | ✅ 已创建 | KPI+成本+多平台+预警+编排 |
| 集成桥接脚本 | `D:\WB_Workflow\integration_bridge.py` | ✅ 已创建 | JSON API桥接orchestrator.py |
| HTTP服务器 | `http://localhost:8080` | ✅ 运行中 | npx serve 托管前端文件 |
| 集成桥接服务 | `http://localhost:8100` | ⏳ 待启动 | Python API服务 |

---

## 五、下一步行动建议

| 优先级 | 行动 | 预计耗时 |
|--------|------|---------|
| 🔴 P0 | 启动 `integration_bridge.py`，验证仪表盘能获取真实数据 | 2分钟 |
| 🔴 P0 | 在仪表盘中添加"从API加载"按钮，切换演示/真实数据 | 10分钟 |
| 🟡 P1 | 工作流编辑器添加保存/加载/导出功能（LocalStorage） | 30分钟 |
| 🟡 P1 | 连接 `ai_super_employee.py` 的 SQLite 数据库获取历史趋势 | 20分钟 |
| 🟢 P2 | 添加每日自动化任务：自动抓取数据并更新仪表盘 | 15分钟 |
| 🟢 P2 | 添加自动刷新功能（每30秒更新KPI卡片） | 10分钟 |
