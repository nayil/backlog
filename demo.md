# Claude Code 多 Agent 协同演示指南

## 项目结构

```
multi-agents-demo/
├── CLAUDE.md          # 多 Agent 工作流配置（Claude Code 自动读取）
├── demo.md            # 本演示指南
└── src/
    └── task_manager.py  # 示例代码（有意留了改进空间）
```

## 演示前准备

1. 确保已安装 Claude Code CLI
2. 在项目根目录启动 Claude Code：
   ```bash
   cd multi-agents-demo
   claude
   ```

## 演示场景

### 场景 1：并行分析与开发（展示并行 dispatch）

输入以下 prompt：

```
请对 src/task_manager.py 进行代码审查和改进。
使用多 agent 协同模式：让 Analyst agent 分析代码问题，同时让 Developer agent 改进代码结构。
```

**预期效果：**
- Master 拆解任务
- 并行 dispatch Analyst 和 Developer 两个 subagent
- Analyst 输出问题清单和评分
- Developer 输出改进建议/代码
- Master 汇总两者结果

### 场景 2：串行协同（展示 agent 间反馈传递）

```
请先让 Analyst agent 分析 src/task_manager.py 的所有问题，
然后将分析报告交给 Developer agent 逐一修复。
最后再让 Analyst 复查修复结果。
```

**预期效果：**
- Master 先 dispatch Analyst
- 拿到分析报告后，传递给 Developer
- Developer 根据报告修复代码
- 再次 dispatch Analyst 复查
- Master 汇总整个流程

### 场景 3：功能添加协同

```
我想给 task_manager 添加一个"任务分组"功能。
请用多 agent 模式：
- Analyst 评估当前代码结构是否支持这个功能
- Developer 实现这个功能
```

**预期效果：**
- Analyst 评估可行性和建议的实现方式
- Developer 实现功能
- Master 协调两者，确保实现符合分析建议

## 观察要点

演示时重点关注：

1. **任务拆解**：Master 如何将一个大任务拆分给不同 agent
2. **并行执行**：两个 agent 同时工作，提高效率
3. **信息传递**：Analyst 的分析结果如何传递给 Developer
4. **结果汇总**：Master 如何整合多个 agent 的输出
5. **闭环反馈**：Developer 修改后，Analyst 再次验证

## 自定义

你可以修改 `CLAUDE.md` 中的 Agent 角色定义来改变行为：
- 调整 Analyst 的分析维度
- 调整 Developer 的改进策略
- 添加更多 Agent 角色（如 Tester、Documenter）
