# 系统选择助手

通过「硬件探测 + 深度问卷 + 交互小测」，在 **72 个候选系统**（Windows 11、macOS、
67 个 Linux 发行版、3 个 BSD）中给出带解释的混合排名，输出 Top3、雷达图、逐维度
理由，并支持分享链接、公开统计与后台导出。

## 技术栈

- 前端：Vue 3 + Vite + TypeScript + Pinia + Vue Router + ECharts + Tailwind CSS v4
- 后端：Flask + SQLite（标准库 `sqlite3`，无 ORM）
- 依赖管理：Python 用 [`uv`](https://docs.astral.sh/uv/)，前端用 `npm`

## 快速开始

需要两个终端。首次运行先装依赖：

```bash
# 后端（本机没有 pip，用 uv 建虚拟环境）
cd backend
uv venv .venv --python 3.14
uv pip install --python .venv/bin/python flask flask-cors pytest

# 前端
cd ../frontend
npm install
```

启动开发服务器：

```bash
# 终端 1：后端，监听 127.0.0.1:5000
cd backend && .venv/bin/python run.py

# 终端 2：前端，监听 127.0.0.1:5173，并把 /api 代理到后端
cd frontend && npm run dev
```

打开 <http://127.0.0.1:5173>。

## 生产构建

前端构建产物由 Flask 直接托管，只需要跑一个进程：

```bash
cd frontend && npm run build          # 产出 frontend/dist
cd ../backend && .venv/bin/python run.py
```

当 `frontend/dist/index.html` 存在时，后端会自动接管 `/` 与所有前端路由
（未命中的路径回落到 SPA）。

## 配置

全部通过环境变量覆盖，默认值见 `backend/app/config.py`：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `SYSCHOICE_DB` | `backend/data/app.db` | SQLite 数据库路径 |
| `SYSCHOICE_ADMIN_TOKEN` | `syschoice-admin` | 后台管理令牌 |
| `SYSCHOICE_SECRET` | `dev-only-secret` | IP 哈希加盐用，生产环境务必修改 |
| `SYSCHOICE_RATE_MAX` | `30` | `/api/assess` 每个 IP 的窗口内请求上限 |
| `SYSCHOICE_RATE_WINDOW` | `60` | 限流窗口（秒） |
| `SYSCHOICE_CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | 允许的前端来源 |

## 接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查与版本 |
| GET | `/api/quiz` | 问卷定义（5 段 28 题）与维度 |
| GET | `/api/catalog` | 软件目录、情景题、命令行题、候选摘要（**不含答案**） |
| POST | `/api/assess` | 提交答卷，返回 Top3、完整排行、雷达数据并落库 |
| GET | `/api/result/<share_code>` | 按分享码读取历史结果 |
| GET | `/api/stats` | 公开统计 |
| GET | `/api/admin/sessions` | 会话列表（需 `X-Admin-Token`，支持分页与 `q` 搜索） |
| GET | `/api/admin/sessions/<id>` | 单条会话详情 |
| GET | `/api/admin/export.csv` | 导出 CSV（需 `X-Admin-Token`） |

## 评分模型

1. 问卷、命令行小测、情景题与软件自检共同推导出用户向量 `u[9]`、每个维度的权重与
   画像特征（设备类型、技术水平、折腾意愿、游戏强度、办公/创作/开发需求、隐私需求、
   稳定偏好、预算敏感、安全兴趣、服务器兴趣、Apple 生态）。
2. 基础分是加权维度相似度：`Σ w[d] · (1 − |u[d] − c[d]| / 100) / Σ w[d]`。
3. 乘以 `gates` 惩罚系数（例如 macOS 在非 Apple 设备上 ×0.35，树莓派系统在非开发板
   上 ×0.25，服务器发行版对桌面玩家降权）。
4. 叠加「必备软件」兼容性惩罚（`native / good / web / partial / none`，`none` 强惩罚）
   与标签加成，归一化为 0–100 的匹配度。
5. 理由文案由「贡献最大的维度 + 未满足项 + 候选自带的优缺点」生成，全程可解释。

## 测试

```bash
# 后端：候选数据完整性、评分确定性、gate 惩罚、鉴权、CSV 导出、限流
cd backend && .venv/bin/python -m pytest -q

# 前端单元测试：流程状态机、硬件探测降级、i18n
cd frontend && npm test

# 端到端：完整走查 + 分享链接 + 统计页 + 后台，含桌面与移动视口
cd frontend && npx playwright install chromium   # 首次
cd frontend && npx playwright test
```

## 目录结构

```
backend/
  app/
    data/        # 维度、候选库、问卷、软件目录、命令行题、情景题
    services/    # scoring.py 评分、reasons.py 理由生成
    api/         # public.py 公开接口、admin.py 后台接口
    db.py        # SQLite schema 与查询
  tests/
frontend/
  src/
    views/       # 起始页 / 硬件 / 问卷 / 小测 / 结果 / 统计 / 后台
    components/  # 步骤导轨、匹配度条、雷达图
    stores/      # Pinia 流程状态
    i18n/        # 预留多语言结构（当前仅 zh-CN）
  e2e/
```
