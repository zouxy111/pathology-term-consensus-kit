# OpenClaw One-Shot Prompt

把下面整段话复制给云端 OpenClaw，再上传两个附件：历史报告数据和结构化术语表。

如果你不懂命令行，优先看仓库根目录的 `CHAT-ONLY-START-HERE.md`。

```text
请使用这个公开 GitHub 仓库完成病理术语标准化流程：
https://github.com/zouxy111/pathology-term-consensus-kit

我会上传两类附件：
1. 历史报告原始数据，可能是一个或多个 CSV/XLSX/XLSM。
2. 结构化术语表，CSV/XLSX/XLSM。注意：术语表不是 WHO/CAP 指南全文、PDF 原文或截图，而是包含 family_id、standard_name、patterns 等字段的表格。

请严格执行：
1. clone 仓库并轻量安装：
   git clone https://github.com/zouxy111/pathology-term-consensus-kit
   cd pathology-term-consensus-kit
   git checkout main
   uv venv || python3 -m venv .venv
   uv pip install -e . || (. .venv/bin/activate && pip install -e .)
   path-term-kit doctor
2. 保存附件到临时目录，不要提交到 Git。如果我上传的是 zip，先解压到临时目录。
3. 先运行：
   path-term-kit inspect-data <解压后的附件目录或报告附件目录>
   path-term-kit inspect-terms <术语表文件>
4. 把扫描结果发给我确认，必须包括：
   - 文件/sheet/table
   - 全量行数
   - 列名
   - 脱敏示例
   - 候选子公司/实验室列
   - 候选报告结果列
   - 候选辅助列
   - 自动跳过的疑似术语表
   - 术语表是否合格
5. 等我确认字段和纳排词后，用 `path-term-kit create-project` 生成配置，不要手写 project.yaml。
6. 再运行：
   path-term-kit validate <project>/project.yaml
   path-term-kit scan <project>/project.yaml
   path-term-kit run <project>/project.yaml
   path-term-kit qa <project>/project.yaml
   path-term-kit package-results <project>/project.yaml
7. 任一步失败就停止，不要猜，不要继续生成问卷。失败时按下面格式回复：
   执行停止，原因：
   - 失败步骤：
   - 错误原文：
   - 需要我补充/确认：
8. 成功后回传：
   - 简短摘要：项目名、全量行数、术语家族数、data gate 状态、隐私状态、主要警告
   - outputs.zip

禁止：
- 禁止抽样代替全量扫描。
- 禁止泄露姓名、电话、医院、条码、住院号、身份证号。
- 禁止把真实数据提交到 Git。
- 禁止在字段未确认时手写 project.yaml。
```
