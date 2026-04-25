# 初始化指南

## 1. 克隆仓库

```bash
git clone <your-repo-url>
cd pathology-term-consensus-kit
```

## 2. 先初始化项目骨架

这一步不需要安装依赖，适合弱模型先把配置框架搭好。

```bash
python scripts/bootstrap_project.py --out my_project
```

生成：

```text
my_project/
  project.yaml
  data/
  outputs/
```

## 3. 安装运行器

推荐：

```bash
uv venv
uv pip install -e ".[dev]"
```

没有 `uv` 时：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Docker 兜底：

```bash
docker build -t path-term-kit .
docker run --rm -v "$PWD":/work -w /work path-term-kit run examples/fake_subspecialty/project.yaml
```

如果已经安装过 CLI，也可以用：

```bash
path-term-kit init --out my_project
```

## 4. 放入数据

```text
my_project/
  project.yaml
  data/
    terms.csv
    reports_1.xlsx
    reports_2.csv
  outputs/
```

## 5. 配置 `project.yaml`

必须配置：

- `inputs.term_catalog`：术语底表路径。
- `inputs.reports`：历史报告文件列表。
- `field_mapping.company_field`：公司/实验室字段。
- `field_mapping.report_text_field`：最终报告文本字段。
- `companies`：问卷展示顺序。
- `target_filter.include_terms`：目标器官或亚专科关键词。
- `target_filter.exclude_terms`：非目标器官排除词。

建议配置：

- `inputs.reports[].expected_rows`：已知行数，用于 data gate 校验。
- `privacy.extra_patterns`：本机构特有条码、医院或编号格式。

## 6. 运行

```bash
path-term-kit validate my_project/project.yaml
path-term-kit scan my_project/project.yaml
path-term-kit run my_project/project.yaml
path-term-kit qa my_project/project.yaml
path-term-kit package-results my_project/project.yaml
```

如果 `run` 失败，先看：

- `outputs/scan_log.csv`
- `outputs/run_manifest.json`
- `outputs/privacy_report.json`

## 7. 术语底表格式

CSV/XLSX 均可，首行必须是字段名：

```csv
family_id,category,standard_name,source_basis,compatible_names,deprecated_or_discuss,patterns,priority,decision_question
```

`patterns` 支持：

- 普通关键词：`低级别上皮内瘤变|低级别异型增生`
- 正则：`regex:低.?级别.*瘤变`

## 8. 输出使用

- 会前先看 `deck_outline.html`。
- 证据复核看 `evidence.xlsx`。
- 发主任填写 `questionnaire.xlsx`。
- 对外发送前必须确认 `privacy_report.json` 为 `pass`。
- 聊天回传时优先发送 `outputs/outputs.zip`。
