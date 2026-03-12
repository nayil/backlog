## [DEV-4-4] 迁移兼容层实现

- **阶段：** 4
- **状态：** completed
- **时间：** 2026-03-11T23:00:00

### 输入
根据 TechLeader 技术方案（TL-2-1），实现模块 4：迁移兼容层（migration），将旧 `tasks.json` 数据迁移到新 SQLite 数据库。

### 输出

#### 改动说明

创建 `src/migration.py`，实现以下功能：

1. **`migrate_json_to_sqlite(json_path, db_path) -> int`**：主迁移函数
   - 读取旧 JSON 文件（格式为任务字典列表）
   - 逐条转换并通过 `BacklogRepository.create()` 写入 SQLite
   - 返回迁移条数
   - 异常处理：文件不存在、JSON 格式错误、内容非列表

2. **`_convert_task(task) -> BacklogItem`**：单条转换函数
   - 状态映射：`pending` → `TODO`，`completed` → `DONE`
   - 优先级保持一致（high/medium/low），无效值回退到 `MEDIUM`
   - 无分类字段或为空时设为默认分类 `"未分类"`

3. **CLI 入口**：`python migration.py <json_path> [db_path]`
   - `db_path` 默认为 `backlog.db`

#### 修改的文件
- **新增** `src/migration.py`

---
