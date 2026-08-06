# Progress

## 历史索引
- 2026-06-27 整理数据流程 / 优化处理能力
- 2026-07-12 整理项目规则
- 2026-07-20 更新 DeepSeek 密钥并同步生产配置（预测模块已删除）
- 2026-07-30 抽出开奖采集技术摘录包

## 2026-08-05 - Task: 开源瘦身 + 分段 env

### What was done

- 采集固定 PlayNow primary / fallback + pc28.help；删除 BCLC、第三方兜底与 AI 预测。
- 删临时 zip；新增 `README.md` / `.env.example`；`.env` 不再进库。
- 代理改为分段：`SCHEME/USER/PASSWORD/HOST/PORT`；DB 增加 `DB_SSLMODE`（本地/云可切换）。
- 清理死代码与冗长注释；`progress` 收敛。

### Testing

- `py_compile` 通过；代理拼接与 `DB_SSLMODE` 加载断言通过。

### Notes

- 模板：`.env.example`；本地密钥：`.env`。
- 回滚：按 git 历史还原。

## 2026-08-05 - Task: 公开仓库 pc28keno + 企业级 README

### What was done

- 编写企业级 `README.md`（功能 / 架构 / 配置 / 部署 / 运维 / FAQ）。
- 新增 `sql/schema.sql` 建表与种子数据。
- 创建公开仓库 `shuaiqideyu/pc28keno` 并推送。

### Testing

- `py_compile` 与代理分段加载此前已通过；本轮以仓库创建与推送验收。

### Notes

- 旧私有仓 `api_python` 可保留为备用 remote；公开仓不含 `.env`。
