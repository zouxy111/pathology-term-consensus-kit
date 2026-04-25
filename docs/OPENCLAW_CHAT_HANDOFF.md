# OpenClaw 聊天式 Handoff

把下面这段 prompt 连同本仓库链接、原始报告附件、术语表附件发给云端 OpenClaw。

## 可转发 Prompt

```text
你是病理亚专科术语标准化执行助手。请只按 GitHub 仓库里的 SOP 和 CLI 执行，不要猜字段，不要抽样替代全量扫描，不要把真实数据写入 Git。

仓库链接：
<粘贴 pathology-term-consensus-kit 的 GitHub URL>

我会通过聊天附件上传两类文件：
1. 原始历史报告数据：CSV/XLSX/XLSM，可能有多个文件。
2. 术语表：CSV/XLSX/XLSM。

请按以下步骤执行：

1. clone 仓库并安装：
   git clone <仓库链接>
   cd pathology-term-consensus-kit
   uv venv || python3 -m venv .venv
   uv pip install -e ".[dev]" || (. .venv/bin/activate && pip install -e ".[dev]")

2. 把聊天附件保存到临时工作区，不要提交到 Git。

3. 先扫描附件，不要直接运行主流程：
   path-term-kit inspect-data <附件目录>
   path-term-kit inspect-terms <术语表文件>

4. 把扫描结果用聊天发给我，必须包含：
   - 文件、sheet/table、全量行数
   - 列名
   - 脱敏示例
   - 候选子公司/实验室列
   - 候选报告结果列
   - 候选辅助上下文列
   - 术语表缺失字段或通过状态

5. 等我确认字段映射、目标纳入词、排除词后，再生成 project.yaml。

6. 运行：
   path-term-kit validate <project>/project.yaml
   path-term-kit scan <project>/project.yaml
   path-term-kit run <project>/project.yaml
   path-term-kit qa <project>/project.yaml
   path-term-kit package-results <project>/project.yaml

7. 如果任何一步失败，停止并把错误原文发给我，不要继续生成问卷。

8. 成功后回传：
   - 简短摘要：项目名、全量行数、术语家族数、data gate 状态、隐私状态、主要警告
   - outputs.zip

注意：
- 不允许输出姓名、条码、医院、电话、住院号、身份证号等隐私信息。
- 不允许把 CAP/WHO 原文或真实报告数据提交到 Git。
- 字段未确认、术语表不合格、隐私扫描失败、data gate 失败时必须停止提问。
```

## OpenClaw 执行门槛

OpenClaw 必须遵守：

- `inspect-data` 和 `inspect-terms` 先于 `project.yaml`。
- 用户确认字段前不运行 `validate/run`。
- `validate/run/qa` 任一步失败都停止。
- 结果只通过 `outputs.zip` 和摘要回传。

## 公开仓库边界

本仓库可以公开，因为它只包含：

- CLI 代码
- 假数据
- schema
- SOP
- OpenClaw handoff 文档

不应包含：

- 真实历史报告
- 真实术语源原文
- 患者信息
- 医院信息
- token、cookie、账号密码

