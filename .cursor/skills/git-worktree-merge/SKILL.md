---
name: git-worktree-merge
description: 将指定 worktree 分支合并到 master，引导解决冲突，合并后询问是否删除 worktree
---

# git-worktree-merge

将用户指定的 worktree 分支合并到当前项目的 master 分支，冲突时引导用户解决，合并完成后询问是否清理 worktree。

## Step 1：列出可用 worktree

运行：
```bash
git worktree list
```

展示所有 worktree 及对应分支。若只有主目录本身，告知用户当前无可合并的 worktree 分支，流程终止。

**询问用户：** "请输入要合并的 worktree 分支名（如 `dev/v0.2.0`）："

## Step 2：前置检查

```bash
git branch --show-current   # 确认当前分支
git status --porcelain       # 检查工作区是否干净
```

- 若不在 master/main，先执行 `git checkout master`
- 若工作区有未提交改动，**停止**并提示用户先执行 `git stash` 或提交改动

## Step 3：执行合并

```bash
git merge <branch-name> --no-ff -m "Merge branch '<branch-name>' into master"
```

## Step 4：冲突处理

若输出包含 `CONFLICT`：

1. 运行 `git status` 列出冲突文件
2. 提示用户：
   ```
   检测到合并冲突，请按以下步骤解决：
   1. 打开冲突文件，手动编辑 <<<<<<< / ======= / >>>>>>> 标记
   2. 解决每个文件后执行：git add <file>
   3. 所有冲突解决后执行：git commit
   4. 完成后告诉我继续
   ```
3. **等待用户确认**冲突已解决后再继续

## Step 5：验证合并结果

```bash
git log --oneline -5
git status
```

向用户展示最新提交记录，确认合并成功。

## Step 6：询问是否删除 worktree

询问用户：
> 合并完成！是否删除 worktree `<worktree-path>` 及分支 `<branch-name>`？（yes 确认，其他跳过）

**用户回答 yes：**
```bash
git worktree remove <worktree-path>
git branch -d <branch-name>
```
若 `-d` 失败（分支未完全合并），询问用户是否强制删除后改用 `git branch -D <branch-name>`。

**用户回答其他：** 保留 worktree，告知手动清理命令：
```bash
git worktree remove <worktree-path>
git branch -d <branch-name>
```

## 错误处理

| 情况 | 处理 |
|------|------|
| 分支不存在 | 重新列出可用分支，提示重新输入 |
| 工作区有未提交改动 | 停止，提示 `git stash` 或先提交 |
| 合并冲突 | 停止自动操作，引导用户手动解决 |
| worktree 目录不存在 | 跳过 `worktree remove`，仅删除分支 |

## 约束

- 合并目标固定为 `master`（或 `main`），禁止合并到其他分支
- 禁止使用 `--force` 强制覆盖
- 删除 worktree 前必须获得用户明确的 `yes` 确认

## 项目 worktree 路径约定

本项目 worktree 位于 `.worktrees/{ver}/`，分支命名为 `dev/{ver}`（如 `.worktrees/v0.2.0` → `dev/v0.2.0`）。
