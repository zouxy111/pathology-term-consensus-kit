# OpenClaw One-Shot Prompt

把下面整段话复制给云端 OpenClaw，再上传两个附件：历史报告数据和术语表。

```text
请使用这个公开 GitHub 仓库完成病理术语标准化流程：
https://github.com/zouxy111/pathology-term-consensus-kit

我会上传两类附件：
1. 历史报告原始数据，可能是一个或多个 CSV/XLSX/XLSM。
2. 术语表，CSV/XLSX/XLSM。

请严格执行：
1. clone 仓库并安装。
2. 保存附件到临时目录，不要提交到 Git。
3. 先运行：
   path-term-kit inspect-data <附件目录>
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
5. 等我确认字段和纳排词后，用 `path-term-kit create-project` 生成配置。
6. 再运行：
   path-term-kit validate <project>/project.yaml
   path-term-kit scan <project>/project.yaml
   path-term-kit run <project>/project.yaml
   path-term-kit qa <project>/project.yaml
   path-term-kit package-results <project>/project.yaml
7. 任一步失败就停止，把错误原文发给我，不要猜，不要继续生成问卷。
8. 成功后回传简短摘要和 outputs.zip。

禁止：
- 禁止抽样代替全量扫描。
- 禁止泄露姓名、电话、医院、条码、住院号、身份证号。
- 禁止把真实数据提交到 Git。
- 禁止在字段未确认时手写 project.yaml。
```

