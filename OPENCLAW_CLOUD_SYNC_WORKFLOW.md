# OpenClaw 云服务器 Git 同步说明

更新日期：2026-04-14

这份文档专门解决一个场景：

- 云服务器上 `finance-journal` 文件夹已经存在
- 需要通过 OpenClaw 执行命令完成拉取、切换分支与后续更新

本文默认路径是：

```bash
/home/admin/.openclaw/workspace/skills/finance-journal
```

默认远端约定是：

- `origin`：GitHub 开源仓
- `gitee`：Gitee 私有仓

默认分支约定是：

- `main`：公开核心代码分支
- `private-sync`：私有同步分支，允许携带 `_runtime`、交割单等个人数据

## 一、先判断当前目录属于哪种情况

先在云服务器上执行：

```bash
cd /home/admin/.openclaw/workspace/skills/finance-journal
pwd
ls -la
git status --short --branch
git remote -v
```

通常会落入下面三种情况之一。

### 情况 A：目录已经是 Git 仓库

如果 `git status` 和 `git remote -v` 都能正常输出，说明这个目录已经是仓库，可以直接走“更新”流程。

### 情况 B：目录存在，但不是 Git 仓库

如果提示：

```bash
fatal: not a git repository
```

说明这个目录只是普通文件夹，不带 `.git`。

这时最稳妥的方式不是强行在原目录里接管，而是：

1. 先备份旧目录
2. 再重新克隆

示例：

```bash
mv /home/admin/.openclaw/workspace/skills/finance-journal /home/admin/.openclaw/workspace/skills/finance-journal_backup_$(date +%Y%m%d_%H%M%S)
git clone -b private-sync git@gitee.com:shenshen-Gao/finance-journal.git /home/admin/.openclaw/workspace/skills/finance-journal
```

如果你要的是公开代码分支，把上面的 `private-sync` 改成 `main` 即可。

### 情况 C：目录已经是 Git 仓库，但远端不对或分支不对

例如：

- 当前 remote 没有 `gitee`
- 当前在 `main`，但你实际上要同步 `private-sync`
- 当前在 `private-sync`，但只是想拉公开代码

这种情况不用重建目录，直接修正 remote 和 branch 即可。

## 二、推荐的 OpenClaw 目标分支

在 OpenClaw / 云服务器上，通常建议明确区分两个使用目标。

### 1. 只要公开代码：用 `main`

适合：

- 只运行核心代码
- 不同步个人 `_runtime`
- 不希望服务器上保留交割单等隐私数据

### 2. 需要账本状态与私有数据同步：用 `private-sync`

适合：

- 希望服务器和本地共享 `_runtime`
- 需要同步私有交割单、日报产物、Obsidian 导出等
- 把 Gitee 当作私有同步中转站

## 三、首次把已有仓库切到目标分支

### 方案 A：切到私有同步分支 `private-sync`

先进入仓库：

```bash
cd /home/admin/.openclaw/workspace/skills/finance-journal
```

如果还没有 `gitee` remote，先补上：

```bash
git remote add gitee git@gitee.com:shenshen-Gao/finance-journal.git
```

拉远端分支信息：

```bash
git fetch --all --prune
```

如果本地还没有 `private-sync` 分支：

```bash
git checkout -b private-sync --track gitee/private-sync
```

如果本地已经有 `private-sync`：

```bash
git checkout private-sync
git pull --rebase gitee private-sync
```

### 方案 B：切到公开代码分支 `main`

```bash
cd /home/admin/.openclaw/workspace/skills/finance-journal
git fetch --all --prune
git checkout main
git pull --rebase origin main
```

如果你希望在服务器上统一从 Gitee 拉 `main`，也可以：

```bash
git checkout main
git pull --rebase gitee main
```

## 四、目录已经存在时，最常用的更新命令

### 1. 更新私有同步分支

这是最适合你当前“云服务器与 Gitee 私有仓交换数据”的命令组：

```bash
cd /home/admin/.openclaw/workspace/skills/finance-journal
git fetch --all --prune
git checkout private-sync
git pull --rebase gitee private-sync
```

### 2. 更新公开主分支

```bash
cd /home/admin/.openclaw/workspace/skills/finance-journal
git fetch --all --prune
git checkout main
git pull --rebase origin main
```

### 3. 如果只配了 Gitee，也可以统一用 Gitee

```bash
cd /home/admin/.openclaw/workspace/skills/finance-journal
git fetch --all --prune
git checkout main
git pull --rebase gitee main
```

## 五、OpenClaw 可直接执行的标准命令

下面这组命令适合直接交给 OpenClaw：

### 1. OpenClaw 更新私有账本分支

```bash
cd /home/admin/.openclaw/workspace/skills/finance-journal && \
git fetch --all --prune && \
git checkout private-sync && \
git pull --rebase gitee private-sync
```

### 2. OpenClaw 更新公开代码分支

```bash
cd /home/admin/.openclaw/workspace/skills/finance-journal && \
git fetch --all --prune && \
git checkout main && \
git pull --rebase origin main
```

### 3. OpenClaw 首次切到 `private-sync`

```bash
cd /home/admin/.openclaw/workspace/skills/finance-journal && \
git remote -v && \
git fetch --all --prune && \
git checkout -b private-sync --track gitee/private-sync
```

如果本地已经有该分支，这条命令会失败；那就改用：

```bash
cd /home/admin/.openclaw/workspace/skills/finance-journal && \
git fetch --all --prune && \
git checkout private-sync && \
git pull --rebase gitee private-sync
```

## 六、如果服务器目录里已经有本地改动

先检查：

```bash
cd /home/admin/.openclaw/workspace/skills/finance-journal
git status --short
```

如果输出不为空，说明服务器本地已经改过文件。

这时不要直接 `git pull --rebase`，建议先暂存：

```bash
git stash push -u -m "openclaw-before-sync"
git pull --rebase gitee private-sync
git stash pop
```

如果你更新的是 `main`，把分支名改成 `main` 即可。

适合 OpenClaw 的完整写法：

```bash
cd /home/admin/.openclaw/workspace/skills/finance-journal && \
git status --short && \
git stash push -u -m "openclaw-before-sync" && \
git pull --rebase gitee private-sync && \
git stash pop
```

注意：

- `stash pop` 可能出现冲突
- 如果服务器上不应该有手工改动，最好先查清这些改动再继续

## 七、如果本地分支不存在，如何补建

### 补建 `private-sync`

```bash
cd /home/admin/.openclaw/workspace/skills/finance-journal
git fetch gitee --prune
git checkout -b private-sync --track gitee/private-sync
```

### 补建 `main`

如果本地没有 `main`，但远端有：

```bash
cd /home/admin/.openclaw/workspace/skills/finance-journal
git fetch origin --prune
git checkout -b main --track origin/main
```

如果你希望跟踪 Gitee 的 `main`：

```bash
git fetch gitee --prune
git checkout -b main --track gitee/main
```

## 八、如果远端没配好，怎么补

查看当前 remote：

```bash
git remote -v
```

如果缺少 Gitee：

```bash
git remote add gitee git@gitee.com:shenshen-Gao/finance-journal.git
```

如果缺少 GitHub：

```bash
git remote add origin git@github.com:Topps-2025/finance-journal.git
```

如果 remote 地址写错了：

```bash
git remote set-url gitee git@gitee.com:shenshen-Gao/finance-journal.git
git remote set-url origin git@github.com:Topps-2025/finance-journal.git
```

## 九、最常见报错与处理

### 1. `destination path ... already exists and is not an empty directory`

说明你在一个非空目录上直接执行了 `git clone`。

处理方式：

- 目录如果已经是仓库，就不要再 clone，直接 `git fetch` / `git pull`
- 目录如果不是仓库，先备份旧目录，再重新 clone

### 2. `fatal: not a git repository`

说明目录没有 `.git`。

处理方式：

- 备份旧目录
- 重新 clone 到原路径

### 3. `error: pathspec 'private-sync' did not match any file(s) known to git`

说明本地没有这个分支。

处理方式：

```bash
git fetch --all --prune
git checkout -b private-sync --track gitee/private-sync
```

### 4. `Please commit your changes or stash them before you merge`

说明服务器本地有未提交改动。

处理方式：

```bash
git status --short
git stash push -u -m "openclaw-before-sync"
git pull --rebase gitee private-sync
git stash pop
```

### 5. SSH 拉取失败

先检查 SSH：

```bash
ssh -T git@gitee.com
```

如果还没配公钥，先生成并上传到 Gitee：

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
cat ~/.ssh/id_ed25519.pub
```

## 十、推荐给 OpenClaw 的固定提示词

你可以在 OpenClaw 里直接下这种指令：

### 更新私有分支

```text
进入 /home/admin/.openclaw/workspace/skills/finance-journal，检查 git 状态；如果当前目录已经是仓库，则切到 private-sync 并从 gitee/private-sync 执行 git pull --rebase 更新；如果本地有未提交改动，先 stash 再更新。
```

### 更新公开主分支

```text
进入 /home/admin/.openclaw/workspace/skills/finance-journal，检查 git 状态；切到 main，并从 origin/main 执行 git pull --rebase 更新；如果当前目录不是 git 仓库，先告诉我再处理。
```

### 首次接管已有目录

```text
检查 /home/admin/.openclaw/workspace/skills/finance-journal 是否为 git 仓库；如果不是，先备份旧目录，再从 gitee 克隆 private-sync 分支到原路径。
```

## 十一、你当前场景的最推荐做法

如果这台云服务器主要用于和 Gitee 私有仓同步账本数据，最推荐固定使用：

```bash
cd /home/admin/.openclaw/workspace/skills/finance-journal
git fetch --all --prune
git checkout private-sync
git pull --rebase gitee private-sync
```

如果第一次切分支失败，再补一次：

```bash
git fetch --all --prune
git checkout -b private-sync --track gitee/private-sync
```

## 十二、结论

文件夹已经存在时，原则上不要重复 `git clone`。

优先按下面逻辑处理：

1. 先判断是不是 Git 仓库
2. 是仓库就直接 `fetch + checkout + pull`
3. 有本地改动就先 `stash`
4. 不是仓库就先备份旧目录，再重新 clone

对于你的用途：

- 云服务器同步私有账本：优先 `private-sync`
- 云服务器只更新开源代码：优先 `main`

这样最适合让 OpenClaw 稳定执行更新拉取。
