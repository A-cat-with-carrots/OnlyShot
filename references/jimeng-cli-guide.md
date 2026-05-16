# dreamina CLI 集成详细指南（v0.6.0）

字节官方提供的面向 AGENT 的 CLI 工具包。本技能在 Phase 1 阶段 3.5（ref 图）+ Phase 2 阶段 4.C（视频出片）调用。

来源：字节官方《即梦 CLI 体验指南》v1.4.3（2026-05-07）

## v0.6.0 新增（必读）

> 来源：SD-002 EP01 实战 36 grid × 3 轮跑沉淀。

### `scripts/生成分镜图.py` 3 个新 flag

| flag | 作用 | 用法 |
|------|------|------|
| `--no-fingerprint` | 不 append `02_IP简报.md` 的视觉指纹（防 ref 风格词 `neutral/flat/NOT cinematic` 污染分镜图 dramatic 光） | 跑分镜图必加 |
| `--check-length` | 跑前预检 prompt 字数 > 1500（即梦 5.0 实测上限） | 长 prompt 项目必加 |
| `--check-sensitive` | 跑前扫反派词 / 暧昧词 / 中文敏感词（命中 warn 不阻断） | 反派戏 grid 必加 |

### 内置 default 调整

- `max_workers`：8 → **4**（降并发防即梦限流，长 prompt 8 并发必死）
- `timeout`：300 → **420s** + 加 2 次重试（即梦偶发慢响应）
- `--poll`：180 → **300s**

### 推荐跑法

```bash
# 标准跑（多 grid 批量）
python scripts/生成分镜图.py <项目> <ep> --candidates=1 --no-fingerprint --check-length --auto-pick-first

# 单 grid 4 候选（关键爆点 grid）
python scripts/生成分镜图.py <项目> <ep> <grid#> --candidates=4 --no-fingerprint

# 失败重跑（长 prompt 必单跑）
python scripts/生成分镜图.py <项目> <ep> <grid#> --candidates=1 --no-fingerprint
```

详见 `references/jimeng-failure-modes.md`（3 类 fail 区分 / 敏感词清单 / 字数上限）。

---

# 原 v0.2.0 内容（已沿用）

---

## v0.2.0 关键升级（必读）

### ⭐ 弃用 bash 提交，强制 Python subprocess

**原因**（SD-001 实战教训）：
bash `eval "dreamina multimodal2video --prompt='$full_prompt'"` 在 prompt 含中文 `「」`、`(@xxx_ref.png)`、`@`、半全角混合 字符时 **quoting 解析错误** → dreamina CLI 收到 malformed prompt → server 创建 task entry 但**不实际处理**：
- `list_task` 显示 querying（假活）
- 余额不扣
- 网页端「视频生成 → 全能参考」**看不到任务**
- 等 30+ 分钟仍 querying

**v0.2.0 修复**：
- 用 `python scripts/生成分集视频.py` 替代旧 `bash 生成分集视频.sh`
- subprocess args list 直接传 → 无 quoting 问题
- 自动 ref 完备性检查（regex 含全角 `）` stop 字符修复）
- 自动从 02_IP简报.md 抽视觉指纹 append

### multimodal2video 任务 stuck 排查

提交后立即 check `queue_status`：
```bash
dreamina query_result --submit_id=<sid> | grep queue_status
# 正常: "queue_status": "Generating"  → 真在跑
# 异常: 没字段 / "queue_length"=N    → stuck，重提
```

### 网页端任务可见性

`multimodal2video` = **「全能参考」**，在网页端：
- ✗ 默认「图生成」历史页**看不到**（user 容易误以为没提交）
- ✓ 在 **「视频生成 → 全能参考 → 历史记录」** tab

### 13 个失败模式

详见 `references/troubleshooting.md`。生视频前必读。

---

---

## 1. 安装（首次）

### 一行命令安装

```bash
curl -fsSL https://jimeng.jianying.com/cli | bash
```

支持平台：
- macOS（Intel / Apple Silicon）
- Linux x86_64 / arm64（v1.3.4 起支持 arm64）
- Windows（用 **Git Bash** 跑这条命令；不能用 PowerShell 直接跑）

### Windows 用户特别说明

Windows 上 dreamina 是 unix 工具，需要 Git Bash 环境：

1. 装 Git for Windows：https://git-scm.com/download/win
2. 装完打开「Git Bash」（不是 PowerShell / CMD）
3. 在 Git Bash 里跑安装命令
4. dreamina 二进制装到 `~/.dreamina_cli/bin/dreamina`
5. **重要**：把 `~/.dreamina_cli/bin/` 加到 PATH，或在 Claude Code Bash 工具里用绝对路径调

或用本技能的 setup 脚本：

```bash
bash scripts/setup-jimeng.sh
```

### 验证安装

```bash
dreamina --version
# 期望输出：dreamina v1.4.2 或更高
```

---

## 2. 登录

### 第一次登录

```bash
dreamina login
```

会自动拉浏览器去授权（用即梦账号登录）。如果浏览器没拉起：

```bash
dreamina login --debug
```

会打印调试信息和回调地址。

登录态存：`~/.dreamina_cli/credential.json`

### 检验登录态

```bash
dreamina user_credit
```

返回 JSON 含余额信息 → 登录成功。

报错或返回空 → 登录失效，重跑 `dreamina login`。

### 切换账号

```bash
dreamina relogin
```

清现有凭证 + 重启登录流程。

### 完全清空

```bash
dreamina logout
```

---

## 3. 核心命令

### 3.1 `text2image` 文生图（Phase 1 阶段 3.5 用）

```bash
dreamina text2image \
  --prompt="80 岁中国老年女性，灰白发髻，暗红色锦缎对襟唐装，9:16 半身像" \
  --ratio=9:16 \
  --resolution_type=2k \
  --download_dir=./ref图/角色/ \
  --poll=60
```

**关键参数**：

| 参数 | 取值 | 说明 |
|------|------|------|
| `--prompt` | 字符串 | 提示词（必填）|
| `--ratio` | `1:1` / `16:9` / `9:16` / `4:3` 等 | 比例（短剧 ref 用 9:16）|
| `--resolution_type` | `1k` / `2k` | 分辨率（ref 图建议 2k）|
| `--download_dir` | 路径 | 自动下载目录 |
| `--poll` | 秒数 | 同步等待，建议 60 |
| `--seed` | 整数 | 随机种子（同种子可复现）|

返回：JSON 含 `submit_id`、`task_status`、下载链接、本地保存路径。

### 3.2 `image2image` 图生图

用于角色不同服装/姿势：

```bash
dreamina image2image \
  --images=./ref图/角色/周翠英_ref.png \
  --prompt="同一角色，换成深色羊毛大衣，街头雪景" \
  --ratio=9:16 \
  --resolution_type=2k \
  --download_dir=./ref图/角色/ \
  --poll=60
```

`--images` 是复数参数，支持多张（最多 10 张）。

### 3.3 `text2video` 文生视频

```bash
dreamina text2video \
  --prompt="奶奶推开蛋糕，露出底下的红头法律文件" \
  --duration=3 \
  --ratio=9:16 \
  --video_resolution=720P \
  --poll=60
```

**注意**：短剧 Phase 2 主要用 image2video（基于角色 ref），不用 text2video。

### 3.4 `image2video` 图生视频（Phase 2 阶段 4.C 用）

```bash
dreamina image2video \
  --image=./ref图/角色/周翠英_ref.png \
  --prompt="奶奶推开蛋糕慢推，特写慢推" \
  --duration=3 \
  --video_resolution=720p \
  --poll=60
```

`--image` 是单数（首帧参考）。**ratio 自动从输入图推**（角色 ref 9:16 → 输出 9:16），不要写 `--ratio`。

**duration 取值**（按 `image2video -h`）：
- `3.0/3.0fast/3.0pro`：3-10s ← skill 默认走这一档
- `3.5pro`：4-12s
- `seedance2.0` 系列：4-15s
- 不指定 model_version → 用默认（推荐留空）

**skill 统一用 `--duration=3`**：60 grid × 3s = 180s ✓ 与分镜.json 节奏完全对齐。剪映拼接时不需要重采样。

**注**：image2video 不下载视频，必须配合 `query_result --submit_id=<ID> --download_dir=<dir>` 拉视频。`生成分集视频.sh` 脚本已封装这个流程。

### 3.5 `query_result` 查异步任务

如果没用 `--poll` 或 poll 超时，会返回 `submit_id`：

```bash
dreamina query_result --submit_id=<ID> --download_dir=./视频段/
```

### 3.6 `list_task` 查历史

```bash
dreamina list_task                          # 全部
dreamina list_task --gen_status=success     # 仅成功的
dreamina list_task --submit_id=<ID>         # 按 ID 筛
```

---

## 4. 本技能集成方式

### Phase 1 阶段 3.5：批量生 ref

skill 在阶段 3 完成 3 份圣经后，自动：

1. 检测 dreamina 装没装、登没登
2. 读 3 份圣经末尾的「即梦 ref 生成包」段
3. 提取每个角色 / 场景 / 道具的 prompt
4. 在 Bash 工具里逐个调 `dreamina text2image`
5. 落到 `<项目>/ref图/{角色,场景,道具}/`

或用脚本一键跑：

```bash
bash scripts/生成参考图.sh <项目目录>
```

### Phase 2 阶段 4.C：批量出片

skill 在用户选定要出片的集后，自动：

1. 读 `分集/第XX集_<集名>/即梦批量包.md` 的 60 段 prompt
2. 每段独立调 `dreamina image2video`，传入对应角色 ref
3. 视频段落到 `分集/第XX集_<集名>/视频段/段01.mp4 ... 段60.mp4`
4. 失败段记录到 `分集/第XX集_<集名>/失败段.log` 让用户重跑

或用脚本一键跑：

```bash
bash scripts/生成分集视频.sh <项目目录> <集编号>
```

---

## 5. 成本估算（参考）

实际价格以 `dreamina user_credit` 返回为准。下面是大致估算：

| 任务 | 成本 |
|------|------|
| text2image 2K 9:16 | ~¥0.5-1 / 张 |
| image2image 2K 9:16 | ~¥0.5-1 / 张 |
| image2video 5s 720P | ~¥2-5 / 段 |
| image2video 3s 720P | ~¥1-3 / 段 |

### Phase 1 阶段 3.5 总成本

- 6 角色 × ¥1 = ¥6
- 5 场景 × ¥1 = ¥5
- 5 道具 × ¥1 = ¥5
- **合计约 ¥16**

如果有不满意重跑（约 1-3 张），加 ¥3。**Phase 1 总 ref 图成本 ≤ ¥20**。

### Phase 2 单集出片成本

- 60 段 × 3s × ¥2/段 = **¥120 / 集**（粗估）
- 72 集全出 = ¥8640

所以 Phase 2 必须按集解锁，不能一次出全部。

---

## 6. 故障排查

| 现象 | 应对 |
|------|------|
| `dreamina: command not found` | 路径没加 PATH，用绝对路径 `~/.dreamina_cli/bin/dreamina` |
| 登录卡住 | `dreamina login --debug`，看回调地址 |
| `user_credit` 返回错误 | 登录态失效，`dreamina relogin` |
| 任务一直 `querying` | 用 `query_result --submit_id` 异步查询 |
| 提示余额不足 | 充值，或换免费配额账号 |
| 角色脸跳 | 改 `image2video` 的 `--image` 用更高质量 ref，prompt 加「保持参考图一致」3 次 |
| Windows curl 报错 | 用 Git Bash，不要用 PowerShell |
| Mac M 系列芯片报错 | 装最新版（v1.3.4 起 arm64 原生支持）|

日志位置：`~/.dreamina_cli/logs/`

排查时把日志 + 命令 + 报错描述提供给字节研发 [张成 / 彭一鸿]。

---

## 7. 本地文件说明

| 文件 | 作用 |
|------|------|
| `~/.dreamina_cli/config.toml` | 环境配置 |
| `~/.dreamina_cli/credential.json` | 登录凭证（不要提交 git）|
| `~/.dreamina_cli/tasks.db` | 本地任务记录（SQLite）|
| `~/.dreamina_cli/logs/` | 运行日志 |

`.gitignore` 应排除 `~/.dreamina_cli/`（实际就是用户主目录，不在项目里，无需排除）。

但项目内的 `ref图/` 和 `分集/*/视频段/` 包含 PNG / MP4 文件，体积大，建议加 `.gitignore`：

```gitignore
# 二进制大文件，不进 git
ref图/**/*.png
ref图/**/*.jpg
分集/**/视频段/**/*.mp4
```

---

## 8. 安全 + 法务注意

- dreamina CLI 用账号登录，凭证存本地 — 不要把 `credential.json` 上传 git / 公开
- 生成的图 / 视频版权归即梦用户协议 — 商用前看协议
- 红果上线必须加 AIGC 标识（2026 强制）
- 涉政 / 涉医 / 极端恶心内容会被即梦审核拦截 — 提示词不要碰

---

## 9. 版本记录

- v1.4.2（2026-04-22）：修复多图上传超时
- v1.4.1（2026-04-17）：登录方式更新
- v1.3.5（2026-04-16）：多对话工作空间（Session）
- v1.3.4（2026-04-10）：Linux arm64 支持
- v1.3.3（2026-04-07）：超清图任务排队修复
- v1.3.2（2026-04-05）：seedance2.0fast_vip 通道
- v1.3.1（2026-04-04）：自动更新检测

每月跑 `dreamina --version` 比对最新版，及时更新。
