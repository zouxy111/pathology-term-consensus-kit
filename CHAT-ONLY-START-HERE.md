# Chat-Only Start Here

如果你只通过飞书、Telegram、微信或其他聊天软件使用云端 OpenClaw，**不需要在本地安装任何东西**。

你只需要做三件事：

1. 复制下面的提示词发给云端 OpenClaw。
2. 上传历史报告数据附件。
3. 上传术语表附件。

OpenClaw 会先扫描附件并在聊天里向你确认字段；字段确认前，它不应该生成结果。

## 你需要准备的附件

### 1. 历史报告数据

支持：

- `.csv`
- `.xlsx`
- `.xlsm`

建议包含这些列：

- 子公司/实验室/机构列
- 最终报告结果或病理诊断文本列
- 可选：送检材料、诊断、部位、标本等辅助上下文列

### 2. 术语表

支持：

- `.csv`
- `.xlsx`
- `.xlsm`

术语表必须是结构化表格，不是 WHO/CAP 指南全文、PDF 原文或散乱截图。至少应包含以下字段：

```csv
family_id,category,standard_name,source_basis,compatible_names,deprecated_or_discuss,patterns,priority,decision_question
```

### 3. 文件命名建议

```text
reports_2024_2026.xlsx
terms_subspecialty.csv
```

文件很多时可以打包上传：

```text
attachments.zip
  reports/
    reports_1.xlsx
    reports_2.csv
  terms/
    terms.csv
```

如果上传的是 `attachments.zip`，OpenClaw 必须先解压，再对解压后的目录运行扫描命令；不要直接把 zip 文件传给 `inspect-data`。

## 复制给 OpenClaw 的提示词

```text
请使用这个公开 GitHub 仓库完成病理术语标准化流程：
https://github.com/zouxy111/pathology-term-consensus-kit

我会上传两类附件：
1. 历史报告原始数据，可能是一个或多个 CSV/XLSX/XLSM。
2. 结构化术语表，CSV/XLSX/XLSM。

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
5. 等我确认字段、目标纳入词、排除词后，用 `path-term-kit create-project` 生成配置。
6. 再运行：
   path-term-kit validate <project>/project.yaml
   path-term-kit scan <project>/project.yaml
   path-term-kit run <project>/project.yaml
   path-term-kit qa <project>/project.yaml
   path-term-kit package-results <project>/project.yaml
7. 任一步失败就停止，用下面格式回复我，不要猜，不要继续生成问卷：
   执行停止，原因：
   - 失败步骤：
   - 错误原文：
   - 需要我补充/确认：
8. 成功后回传：
   - 简短摘要：项目名、全量行数、术语家族数、data gate、隐私状态、主要警告
   - outputs.zip

禁止：
- 禁止抽样代替全量扫描。
- 禁止泄露姓名、电话、医院、条码、住院号、身份证号。
- 禁止把真实数据提交到 Git。
- 禁止在字段未确认时手写 project.yaml。
```

## 正常聊天流程示例

```text
用户：请用这个仓库帮我做胃病理术语共识，我上传了 reports.xlsx 和 terms.csv。

OpenClaw：我会先扫描附件，不会直接生成结果。请稍等。

OpenClaw：扫描结果如下：
- 历史报告文件：reports.xlsx
- 全量行数：122537
- 候选子公司/实验室列：最终检测子公司
- 候选报告结果列：单一结果
- 候选辅助列：送检材料、诊断
- 术语表：通过，术语家族数 36

请确认：
1. 子公司/实验室列是否是「最终检测子公司」？
2. 报告结果列是否是「单一结果」？
3. 辅助列是否使用「送检材料、诊断」？
4. 纳入词有哪些？例如：胃、胃窦、胃体
5. 排除词有哪些？例如：食管、肠

用户：确认。纳入词：胃、胃窦、胃体。排除词：食管、肠。

OpenClaw：收到。我将生成 project.yaml 并运行 validate、scan、run、qa、package-results。完成后回传摘要和 outputs.zip。
```

## 你最终会收到什么

成功后，OpenClaw 应回传：

- 聊天摘要：项目名、全量行数、术语家族数、data gate 状态、隐私状态、主要警告
- `outputs.zip`

`outputs.zip` 应包含：

- `evidence.xlsx`
- `questionnaire.xlsx`
- `deck_outline.md`
- `deck_outline.html`
- `run_manifest.json`
- `privacy_report.json`
- `scan_log.csv`

如果 OpenClaw 没有先向你确认字段，或者字段未确认就直接生成结果，请让它停止并重新从 `inspect-data` / `inspect-terms` 开始。
