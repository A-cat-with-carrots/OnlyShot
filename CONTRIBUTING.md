# 参与贡献 / Contributing

> English: PRs and issues are welcome in Chinese or English. Keep scripts dependency-free (Python 3.10+ standard library), never commit API keys or generated media, and follow the third-party service rules below if your change calls a paid API.

欢迎提 issue 和 PR。下面几条是合并前会看的东西。

## 提 PR 前

- 本地跑一遍：`python -m py_compile scripts/*.py`；脚本带 `--self-test` 的跑一遍自检（不联网、不扣费）。
- 不提交生成产物（`SD-*/`、`projects/`、图片、视频，`.gitignore` 已经挡了一部分）和任何密钥。
- 脚本优先只用标准库，需要 Python 3.10+；调外部命令用参数列表（`subprocess.run([...])`），不拼 shell 字符串（中文 prompt 会出问题，见 `references/troubleshooting.md`）。
- 文档用中文；新增的市场数据、平台规则写清出处和日期，查不到出处的数字不写。

## 接入第三方服务（付费 API、外部平台）

参照 #5（Sonilo 配乐）的做法：

1. **可选**：不改默认流程，原来的手动做法保留。
2. **密钥只走环境变量**，不写进代码、配置和仓库；报错信息里不打印密钥。
3. **写明费用和授权**：怎么计费、免费档能用多少、免费档能不能商用、商用要哪一档，并注明「以对方条款为准」和查询日期。
4. **写明数据去向**：会把什么（剧本、图片、成片）上传到哪里。
5. **带离线自检**：`--self-test` 不联网、不扣费，覆盖请求拼装和结果解析。
6. **说明关联**：如果你在这家服务的团队工作，请在 PR 里说一声。

## 内容

- 示例和模板里不放真人肖像、受版权保护的角色、商标。
- 题材和平台规则会变，市场情报类内容请标注日期。

## 作品分享

用 OnlyShot 做出了作品，欢迎用「作品分享」模板开 issue。
