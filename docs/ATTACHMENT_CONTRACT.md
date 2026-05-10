# 聊天附件协议

本协议用于用户把数据通过聊天软件发给云端 OpenClaw。真实数据只进入云端临时工作区，不进入 Git 仓库。

## 非技术用户上传前清单

发送给 OpenClaw 前，请确认：

- [ ] 已准备历史报告数据表，不是截图。
- [ ] 历史报告表里有子公司/实验室/机构列。
- [ ] 历史报告表里有最终报告结果或病理诊断文本列。
- [ ] 已准备结构化术语表，不是 WHO/CAP/PDF 原文全文。
- [ ] 术语表包含 `family_id`、`standard_name`、`patterns` 等必填字段。
- [ ] 文件格式是 `.csv`、`.xlsx` 或 `.xlsm`。
- [ ] 如果文件很多，已打包成一个 zip，并按 reports/ 与 terms/ 分目录。
- [ ] 已理解 OpenClaw 会先扫描并让你确认字段，字段确认前不会生成问卷。

## 用户需要上传什么

至少两类附件：

1. **原始历史报告数据**
   - 支持：`.csv`、`.xlsx`、`.xlsm`
   - 不建议：`.xls`，请先转成 `.xlsx` 或 `.csv`
   - 可以是一个或多个文件
2. **术语表**
   - 支持：`.csv`、`.xlsx`、`.xlsm`
   - 必须包含规定字段

建议命名：

```text
reports_2024_2026.xlsx
terms_subspecialty.csv
```

如附件很多，可以打包：

```text
attachments/
  reports/
    reports_1.xlsx
    reports_2.csv
  terms/
    terms.csv
```

注意：`path-term-kit inspect-data` 不直接读取 zip。OpenClaw 收到 zip 后必须先解压，再扫描解压后的目录。

## OpenClaw 必须先扫描

收到附件后，OpenClaw 先运行：

```bash
path-term-kit inspect-data <解压后的附件目录或报告附件目录>
path-term-kit inspect-terms <term_file>
```

`inspect-data` 必须向用户展示：

- 每个文件和 sheet/table
- 全量行数
- 列名
- 每列脱敏示例
- 候选子公司/实验室列
- 候选报告结果列
- 候选辅助上下文列
- 自动跳过的疑似术语表

用户确认前，OpenClaw 不得生成 `project.yaml`。

## 字段确认问题

OpenClaw 必须向用户确认：

```text
请确认以下字段：
1. 子公司/实验室列是哪一列？
2. 报告结果列是哪一列？
3. 哪些列只作为辅助上下文？
4. 本轮目标器官/亚专科纳入词有哪些？
5. 排除词有哪些？
6. 术语表是否就是本轮拍板范围？
```

如果用户说“不对”，OpenClaw 要重新展示候选列和脱敏示例，不得猜测。

## 生成配置

字段确认后，OpenClaw 应使用 `create-project` 自动生成配置，不要手写 YAML：

```bash
path-term-kit create-project \
  --out <project_dir> \
  --term-file <term_file> \
  --report-file <report_file> \
  --project-name "<项目名>" \
  --subspecialty "<亚专科>" \
  --company-field "<子公司/实验室列>" \
  --report-text-field "<报告结果列>" \
  --context-field "<辅助列>" \
  --include-term "<纳入词>" \
  --exclude-term "<排除词>"
```

如果用户没有提供公司列表，工具会从已确认的公司字段中自动推断。

## 术语表要求

术语表必须包含：

```csv
family_id,category,standard_name,source_basis,compatible_names,deprecated_or_discuss,patterns,priority,decision_question
```

缺字段时，OpenClaw 必须停止并要求用户补齐。

## 结果回传

完成后，OpenClaw 回传：

- 聊天摘要：项目名、全量行数、术语家族数、data gate、隐私状态、警告
- 附件：`outputs.zip`

`outputs.zip` 应包含：

- `evidence.xlsx`
- `questionnaire.xlsx`
- `deck_outline.md`
- `deck_outline.html`
- `run_manifest.json`
- `privacy_report.json`
- `scan_log.csv`
