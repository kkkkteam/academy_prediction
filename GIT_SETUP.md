# Git 仓库设置说明

## 本地仓库已创建

项目已经初始化为 Git 仓库并完成了首次提交。

## 连接到远程仓库

### 方法 1: GitHub

1. **在 GitHub 上创建新仓库**
   - 访问 https://github.com/new
   - 仓库名称：例如 `student-performance-prediction`
   - 选择 Public 或 Private
   - **不要**初始化 README、.gitignore 或 license（我们已经有了）

2. **连接本地仓库到远程**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/student-performance-prediction.git
   git branch -M main
   git push -u origin main
   ```

### 方法 2: GitLab

1. **在 GitLab 上创建新项目**
   - 访问 https://gitlab.com/projects/new
   - 项目名称：例如 `student-performance-prediction`
   - 选择可见性级别

2. **连接本地仓库到远程**
   ```bash
   git remote add origin https://gitlab.com/YOUR_USERNAME/student-performance-prediction.git
   git branch -M main
   git push -u origin main
   ```

### 方法 3: 其他 Git 服务

根据你使用的 Git 服务提供商，按照他们的文档添加远程仓库。

## 当前提交的文件

以下文件已提交到仓库：
- ✅ 所有 Python 源代码文件
- ✅ README.md 和文档
- ✅ requirements.txt
- ✅ 示例文件
- ✅ .gitignore

以下文件**未提交**（已在 .gitignore 中排除）：
- ❌ 模型文件 (*.pkl) - 文件太大
- ❌ 数据文件 (Data/) - 敏感数据
- ❌ 分析输出 (analysis_output/)
- ❌ 虚拟环境 (.venv/)
- ❌ 临时文件

## 后续提交

当你修改代码后，使用以下命令提交：

```bash
# 查看更改
git status

# 添加更改的文件
git add <文件名>
# 或添加所有更改
git add .

# 提交更改
git commit -m "描述你的更改"

# 推送到远程仓库
git push
```

## 注意事项

1. **模型文件**：训练好的模型文件 (.pkl) 不会提交到仓库。如果需要，可以：
   - 使用 Git LFS (Large File Storage)
   - 或单独存储在其他位置

2. **数据文件**：实际的学生数据文件不应提交到公共仓库（隐私保护）

3. **环境变量**：如果有敏感配置，使用环境变量或配置文件（不提交到仓库）
