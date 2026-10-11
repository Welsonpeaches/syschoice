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

两个服务都监听双栈（`::`），所以下面这些地址都能用；局域网或用 IPv6 访问时换成这台机器的
实际地址即可：

- <http://127.0.0.1:5173> 、 <http://[::1]:5173>
- <http://127.0.0.1:5000> 、 <http://[::1]:5000>

只想让本机访问可以设置 `VITE_DEV_HOST=127.0.0.1` 与 `SYSCHOICE_HOST=127.0.0.1`。

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
| `SYSCHOICE_HOST` | `::` | 后端监听地址，`::` 为 IPv4/IPv6 双栈 |
| `VITE_DEV_HOST` | `::` | 前端开发服务器监听地址 |

## 可选：接入模型写点评

结果页支持一段由模型撰写的说明。**默认关闭**；不配置时结果页完全正常，只是少一个面板。

```bash
export SYSCHOICE_LLM_API_KEY=sk-...
export SYSCHOICE_LLM_BASE_URL=https://api.openai.com/v1   # 任何 OpenAI 兼容接口都可以
export SYSCHOICE_LLM_MODEL=gpt-4o-mini
cd backend && .venv/bin/python run.py
```

接口契约：`POST /api/result/<share_code>/insight` 生成一次并写库缓存，重复调用直接返回缓存。
提示词只包含已经算好的排名、维度与理由，模型没有机会改变结论，也不会看到原始答卷。
未配置时该接口返回 `503`，上游报错返回 `502`。

## 反馈数据与「用模型打分」的路线

结果页底部会让用户回答「最后装了哪个、用起来怎么样」，存在 `feedback` 表，并随
`/api/admin/export.csv` 一起导出（`chosen_name`、`satisfaction`、`feedback_note` 三列）。

**当前为什么不直接训练一个打分模型**：项目没有任何真实标签，唯一可用的标签就是上面这张表，
而现在它还是空的。用规则去生成合成标签再训练，只会把同一套人工先验换个不可解释的形式学回来，
同时丢掉现在每条推荐都带得出来的维度级理由。所以现阶段正确做法是：

1. 保留手写的确定性打分器，它是可解释、可测试、可直接改权重的。
2. 持续收集 `feedback`（装机结果 + 满意度），这是唯一真实的监督信号。
3. 等每条候选累积到足够样本后，再把它当作 learning-to-rank 问题：候选的特征是现有九维向量与
   gate 结果，标签来自满意度，用成对排序损失去拟合维度权重 `w[d]`；打分器结构不变，
   只是把人工权重换成拟合权重，理由文案依旧可用。

另一个更早可做、且不需要用户标签的方向：现在九维向量里的数值（例如「Ubuntu 易用性 = 85」）是
手工填的，这部分才是整条链路里最主观的一环。它可以用公开数据来估计，例如软件仓库存量、
ProtonDB 游戏兼容比例、硬件支持列表、发行版维护活跃度，先让候选向量本身更客观。

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
