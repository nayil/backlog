## [DEV-4-1] 实现数据模型层（model 模块）

- **阶段：** 4
- **状态：** completed
- **时间：** 2026-03-11T22:35:00

### 输入
根据 TechLeader 技术方案 [TL-2-1]，实现模块 1：数据模型层。要求定义 Status 枚举、Priority 枚举、BacklogItem dataclass，含 to_dict() / from_dict() 方法。

### 输出

创建了 `src/models.py`，包含以下内容：

1. **`Status` 枚举** — `TODO`, `IN_PROGRESS`, `DONE`（值为 `"todo"`, `"in_progress"`, `"done"`）
2. **`Priority` 枚举** — `HIGH`, `MEDIUM`, `LOW`（值为 `"high"`, `"medium"`, `"low"`）
3. **`BacklogItem` dataclass** — 字段：
   - `title: str`（必填）
   - `description: str`（默认空串）
   - `status: Status`（默认 TODO）
   - `category: str`（默认空串）
   - `priority: Priority`（默认 MEDIUM）
   - `id: Optional[int]`（默认 None，由数据库分配）
   - `created_at: Optional[datetime]`（自动设为当前时间）
   - `updated_at: Optional[datetime]`（自动设为当前时间）
4. **`to_dict()`** — 将 dataclass 转为字典，枚举转为字符串值，datetime 转为 ISO 格式
5. **`from_dict(cls, data)`** — 类方法，从字典构建 BacklogItem，处理缺失字段的默认值

#### 修改的文件
- **新增** `src/models.py`

---
