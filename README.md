# 这个仓库不再更新

现行开奖检测在 [pc28-draw-skills](https://github.com/shuaiqideyu/pc28-draw-skills)。接口、Chrome 指纹、IPv6，以及全年夏令时（固定 UTC−7）都以那边为准。

下面是 2026-08 的旧采集程序，留作对照。其中「PlayNow 必须走代理」和「时间绑在 America/Vancouver」不要再照做。

# Keno → PC28（旧）

加拿大 Keno 彩票实时转化采集引擎。

将官方 Keno 开奖精准转换为加拿大 PC28，并完成入库与衍生计算：多源并发采集、事件驱动处理、PostgreSQL 幂等落库，开箱可部署。

| 项 | 说明 |
|---|---|
| 语言 | Python 3.11+（推荐 3.12 / 3.14） |
| 运行时 | `asyncio` + `httpx` + `psycopg 3` 连接池 |
| 存储 | PostgreSQL |
| 入口 | `python main.py` |

**作者**：[Telegram @yuuu](https://t.me/yuuu)

---

## 目录

- [功能介绍](#功能介绍)
- [系统架构](#系统架构)
- [数据源策略](#数据源策略)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [数据库](#数据库)
- [部署指南](#部署指南)
- [运行与运维](#运行与运维)
- [目录结构](#目录结构)
- [常见问题](#常见问题)
- [License](#license)

---

## 功能介绍

### 1. 多源 Keno 采集

| 通道 | 作用 | 代理 |
|---|---|---|
| PlayNow primary | 拉最新一期 + 下一期倒计时 | 必须 |
| PlayNow fallback | 拉最近 N 期，防漏期 | 必须 |
| pc28.help 备用 | 业务站 Keno JSON，PlayNow 不可达时兜底 | 不需要 |

- 同一期多路并发命中时，靠数据库 **UPSERT / ON CONFLICT** 幂等去重，不会重复触发下游。
- PlayNow 时间为 BC 时区，入库前统一转为 **Asia/Shanghai**。
- 20 球合法性校验（1–80），拒绝封盘期全 0 等伪开奖。

### 2. Keno → 加拿大 PC28 转换

官方口径：20 个号码升序后按固定位求和取模，得到三码与和值，写入 `number` 表，并计算大小、单双、龙虎、边中、极值、形态、组合等衍生字段。

### 3. 衍生处理器（4 路）

| 模块 | 能力 |
|---|---|
| **遗漏** | 60 项（和值 / 属性 / N 余数）遗漏更新；启动可全量回推校准 |
| **ABC 球遗漏** | A/B/C 三球各 18 项共 54 项遗漏 |
| **统计** | 当日命中次数增量统计；跨天自动重置 |
| **长龙** | 多维度长龙检测、活动状态与期望更新 |

共同契约：

- **事件优先**：采集入库后经内存事件总线即时唤醒处理器。
- **轮询兜底**：事件丢失或积压时按间隔补处理。
- **幂等消费**：`*_done` 标记 + advisory lock，避免双计与重复写。

### 4. 工程特性

- 连接池预热，降低首请求延迟
- HTTP 错误节流日志，避免刷屏
- 自适应轮询：发现新期后短间隔复查
- Ctrl+C / 取消任务时优雅停机（停采集 → 停处理器 → 关池）

---

## 系统架构

```text
                    ┌──────────────────────────────────────┐
                    │              main.py                 │
                    │     组装采集器 + 4 个处理器并并发运行   │
                    └──────────────────┬───────────────────┘
                                       │
          ┌────────────────────────────┼────────────────────────────┐
          ▼                            ▼                            ▼
   PlayNow primary              PlayNow fallback              pc28.help
   (代理 / nextdraw)            (代理 / latest/N)             (直连备用)
          │                            │                            │
          └────────────────────────────┼────────────────────────────┘
                                       ▼
                              KenoCollector
                     keno 表 ← 20 球 / countdown
                     number 表 ← PC28 + 衍生字段
                                       │
                              event_bus 广播
                                       │
        ┌──────────────┬───────────────┼───────────────┬──────────────┐
        ▼              ▼               ▼               ▼              │
   omission      abc_omission     statistics        dragon            │
   遗漏表           ABC 遗漏表       统计表           长龙表            │
        └──────────────┴───────────────┴───────────────┘──────────────┘
                                       │
                                 PostgreSQL
```

| 模块路径 | 职责 | 状态归属 |
|---|---|---|
| `modules/keno` | 三路采集、时区与 PC28 转换 | `keno` 写入；触发 `number` 写入 |
| `modules/lottery` | PC28 属性计算、`number` 仓储 | `number` |
| `modules/omission` | 遗漏计算与回推 | `omission` |
| `modules/abc_omission` | ABC 球遗漏 | `abc_omission` |
| `modules/statistics` | 当日统计 | `statistics` |
| `modules/dragon` | 长龙检测 | `dragon` |
| `shared` | 连接池、事件总线、处理器基类、日志 | 无业务表 |

跨模块只经公开入口；编排仅在 `main.py`。

---

## 数据源策略

1. **主路径**：PlayNow（需加拿大可达代理，推荐 `socks5`）。
2. **备用路径**：`https://pc28.help/api/keno.json?nbr=1`（已转 CN 时区的 20 球 + 倒计时）。
3. **冲突处理**：先到先写；后者冲突跳过。下游只在「首次成功写入 `number`」时收到事件。

> PlayNow 对多数非北美出口有 Akamai 拦截。未配置可用代理时，主源会失败，依赖备用源仍可运行，但时效与完整性取决于备用站。

---

## 环境要求

- Python **3.11+**
- PostgreSQL **14+**（本地 Docker / 本机安装 / 云 RDS 均可）
- 出网能力：
  - 访问 PlayNow：需要可用代理
  - 访问 pc28.help：普通 HTTPS 即可
- 操作系统：Linux / macOS（Windows 可用，建议 WSL2）

Python 依赖见 `requirements.txt`：

```text
httpx[http2,socks]
psycopg[binary]
psycopg-pool
python-dotenv
```

---

## 快速开始

```bash
# 1. 克隆
git clone git@github.com:shuaiqideyu/pc28keno.git
cd pc28keno

# 2. 虚拟环境
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. 配置
cp .env.example .env
# 编辑 .env：数据库、代理分段、确认 SSL

# 4. 建库建表（见下方「数据库」）
psql -h 127.0.0.1 -U postgres -d api -f sql/schema.sql

# 5. 启动
python main.py
```

看到类似日志即表示采集循环已启动：

```text
系统启动: Keno 采集 + 遗漏 + ABC球遗漏 + 统计 + 长龙
采集进入并发轮询 (playnow_primary + playnow_fallback + pc28_help)
```

---

## 配置说明

所有配置来自项目根目录 `.env`（**不要提交**）。模板：`.env.example`。

### PostgreSQL

| 变量 | 说明 | 本地示例 | 云 RDS 示例 |
|---|---|---|---|
| `DB_HOST` | 主机 | `127.0.0.1` | 实例地址 |
| `DB_PORT` | 端口 | `5432` | `5432` |
| `DB_NAME` | 库名 | `api` | `api` |
| `DB_USER` | 用户 | `postgres` | 云账号 |
| `DB_PASSWORD` | 密码 | 本地密码 | 云密码 |
| `DB_SSLMODE` | SSL | `disable` / `prefer` | 通常 `require` |

本地自建 PostgreSQL 即可运行，不强制云库。

### PlayNow 代理（分段填写）

程序自动拼成：`{协议}://{用户}:{密码}@{IP}:{端口}`。

| 变量 | 含义 | 示例 |
|---|---|---|
| `PLAYNOW_PROXY_SCHEME` | 协议 | `socks5` / `http` / `https` |
| `PLAYNOW_PROXY_USER` | 用户名（无认证留空） | `myuser` |
| `PLAYNOW_PROXY_PASSWORD` | 密码 | `mypass` |
| `PLAYNOW_PROXY_HOST` | 代理 IP 或域名 | `1.2.3.4` |
| `PLAYNOW_PROXY_PORT` | 端口 | `1080` |

### 数据源 URL

| 变量 | 默认含义 |
|---|---|
| `PLAYNOW_PRIMARY_URL` | PlayNow 最新一期接口 |
| `PLAYNOW_FALLBACK_URL` | PlayNow 最近 N 期接口 |
| `KENO_API_URL` | pc28.help 备用 Keno JSON |

### 日志

| 变量 | 说明 |
|---|---|
| `LOG_LEVEL` | 默认 `INFO`，排查可调 `DEBUG` |

---

## 数据库

首次部署执行：

```bash
createdb api                    # 或云控制台建库
psql -d api -f sql/schema.sql
```

`sql/schema.sql` 会创建业务表并初始化遗漏 / 统计 / 长龙的基础行（若脚本含种子数据）。若你已有同结构库，可跳过建表，仅保证表名与字段与代码一致。

核心表：

| 表 | 用途 |
|---|---|
| `keno` | 原始 20 球 + 倒计时 |
| `number` | PC28 开奖与衍生字段、各处理器 `*_done` |
| `omission` | 60 项遗漏 |
| `abc_omission` | 54 项 ABC 球遗漏 |
| `statistics` | 当日统计 |
| `dragon` | 长龙状态 |

---

## 部署指南

### A. 本地 / 开发机

1. 安装 PostgreSQL，创建库与表。
2. `.env` 中 `DB_HOST=127.0.0.1`，`DB_SSLMODE=disable`。
3. 填好代理分段（若要测 PlayNow）。
4. `python main.py` 前台运行；或用 `tmux` / `screen`。

### B. Linux 服务器（systemd 推荐）

```bash
# 代码目录示例
sudo mkdir -p /opt/pc28keno
sudo chown "$USER" /opt/pc28keno
cd /opt/pc28keno
git clone git@github.com:shuaiqideyu/pc28keno.git .
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env（生产库、代理、DB_SSLMODE=require 如用 RDS）
```

systemd 单元示例 `/etc/systemd/system/pc28keno.service`：

```ini
[Unit]
Description=pc28keno collector
After=network.target postgresql.service

[Service]
Type=simple
User=www
WorkingDirectory=/opt/pc28keno
Environment=PATH=/opt/pc28keno/.venv/bin
ExecStart=/opt/pc28keno/.venv/bin/python main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now pc28keno
sudo journalctl -u pc28keno -f
```

> 若使用宝塔等面板，请在面板内用项目虚拟环境启动 `python main.py`，**不要**污染系统全局 Python。生产启停建议由运维在面板/systemd 操作。

### C. 更新发布

```bash
cd /opt/pc28keno
git pull
source .venv/bin/activate
pip install -r requirements.txt
# 若有 SQL 迁移再执行
sudo systemctl restart pc28keno   # 或面板内重启对应进程
```

### D. 回滚

```bash
git log --oneline -5
git checkout <previous_commit>
sudo systemctl restart pc28keno
```

配置回滚：恢复上一份 `.env` 备份（部署前建议 `cp .env .env.bak.$(date +%Y%m%d)`）。

---

## 运行与运维

### 健康观察

- 日志中周期性出现 `[入库] draw_nbr=... PC28=...` 表示主链路正常。
- PlayNow 连续失败会节流告警；若仅备用源入库，检查代理连通性。
- 处理器启动时可能打印「启动回推」类日志，属正常校准。

### 建议监控项

| 指标 | 含义 |
|---|---|
| `keno` / `number` 最新 `draw_nbr` | 开奖是否在推进 |
| 最新开奖时间距现在 | 新鲜度（Keno 约数分钟一期） |
| 进程是否存活 | systemd / 面板状态 |
| PlayNow 错误日志频率 | 代理或上游是否异常 |

### 安全建议

- `.env` 权限：`chmod 600 .env`
- 勿把代理密码、数据库密码提交到 Git
- 数据库账号最小权限（DML + 必要 DDL）
- 公网不要暴露 PostgreSQL 端口

---

## 目录结构

```text
pc28keno/
├── main.py                 # 进程入口：采集 + 四处理器
├── requirements.txt
├── .env.example            # 配置模板（可提交）
├── sql/
│   └── schema.sql          # 建表与基础种子
├── modules/
│   ├── keno/               # 采集、转换、源站客户端
│   ├── lottery/            # number 与 PC28 计算
│   ├── omission/           # 遗漏
│   ├── abc_omission/       # ABC 球遗漏
│   ├── statistics/         # 当日统计
│   └── dragon/             # 长龙
└── shared/
    ├── config.py           # DB / 日志
    ├── db/connection.py    # 连接池与 SQL 工具
    ├── event_bus.py        # 开奖事件总线
    ├── base_processor.py   # 处理器基类
    ├── constants.py        # 遗漏/统计项常量
    └── logger.py
```

---

## 常见问题

**Q: 不配代理能否运行？**  
A: 可以，仅依赖 pc28.help 备用源；PlayNow 主源会报错（节流）。生产环境仍建议配置可用代理。

**Q: 本地 PostgreSQL 报 SSL 错误？**  
A: `.env` 设 `DB_SSLMODE=disable`（或 `prefer`）。云 RDS 一般用 `require`。

**Q: 重复部署会不会双写遗漏？**  
A: 同一库上跑多个 `main.py` 实例有风险；遗漏/统计虽有 advisory lock，仍建议 **单实例** 写入。

**Q: 如何只采数不跑衍生？**  
A: 当前版本入口固定四处理器。若只要采集，需改 `main.py` 处理器列表（自行维护分支）。

**Q: 时区如何处理？**  
A: PlayNow 按 America/Vancouver 解析再转上海时间；pc28.help 按已是 CN 时区直接入库。

---

## License

以 GitHub 仓库 License 设置为准。

**作者**：[Telegram @yuuu](https://t.me/yuuu)

---

## 致谢与声明

- PlayNow / BCLC Keno 为上游开奖来源；本项目仅做技术同步与衍生计算，请遵守当地法律法规与上游服务条款。
- pc28.help 为可选备用数据源，可用性以其站点为准。
- 本项目按「采集 + 衍生」后端设计，不包含投注、支付或前端展示。

---

## 贡献

欢迎 Issue / PR。提交前请确保：

1. 未包含 `.env` 或任何真实密钥  
2. `python -m py_compile main.py` 通过  
3. 变更说明写清「为什么」
