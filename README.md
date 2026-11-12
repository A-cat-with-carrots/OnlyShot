# OnlyShot：AI 短剧工业流水线（Claude Code Skill）

> 一句「粗糙想法」→ 市场情报 → 剧本 → 分镜 → 分镜图 → 视频段 → 自动初剪 → 上线前检查，出一集能发红果、抖音的竖屏短剧。
> Industrial-grade AI short drama pipeline for Claude Code · [English](README_EN.md)

[![Skill](https://img.shields.io/badge/Claude-Skill-blueviolet)](https://docs.anthropic.com/en/docs/claude-code)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)
[![Version](https://img.shields.io/badge/Version-v0.7.0-orange)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)]()

https://github.com/user-attachments/assets/187a23e5-1b51-47d8-83d2-3b529b44157c

---

## 30 秒看懂

- **是什么**：一个 Claude Code skill（技能名 `ai-short-drama`）。你说一句题材，它带你走完短剧的创作和出片，每一步都落成文件。
- **和别的短剧 skill 不一样**：不止写剧本。接即梦 dreamina 真出图出片；先出分镜图再出视频（改一张图 3 积分，改一段视频 55 积分）；沉淀了 17 种即梦失败模式；最后自动拼成带字幕和 AI 标识的初剪。
- **怎么装**：`git clone https://github.com/A-cat-with-carrots/OnlyShot ~/.claude/skills/ai-short-drama`，重开 Claude Code。
- **一集大概花多少**：按 2026-05 实测单价，一集 193 秒约 2,230 积分（分镜图 36 张约 108 + 视频约 2,120），约合 ¥160。跑之前加 `--dry-run` 先看这一集的预估，不花钱。
- **没有即梦也能用**：剧本、设定、分镜和每段 prompt 都不需要 dreamina，见下面的「轻量模式」。
- **上线要合规**：2026-09-01 起 AI 微短剧每集要有 AI 标识，`拼接初剪.py` 自动加；上线前清单见 [`references/compliance-2026.md`](references/compliance-2026.md)。

---

## 它是什么

把你扔过去的一句话——

> "996 程序员重生为哮天犬，开局触发反 PUA 系统"

——变成可以**直接发红果/抖音**的整套短剧成品：

**Phase 1：创作**
- **市场情报扫描**（搜近 30 天红果/番茄/抖音热什么、避开衰退题材）
- **IP 简报 + 故事架构 + 设定圣经**（角色弧光 + 视觉母题 + 反差点）
- **节奏地图**（每 grid 精确到秒：cold_open / twist / satisfaction / cliffhanger）
- **逐集脚本**（24 集精华 / 36 grid × 4-10s 变奏 / 中文对白 + 潜台词）
- **工业级 ref 库**（80-150 张：每角色 5-8 张含动作/表情，每场景 3-5 张多角度，关键道具 30-50 张）

**Phase 1.5：分镜图**（v0.3.0 工业级核心）
- 每 grid 1-4 张候选关键帧（text2image，3 积分/张）
- 静态图先确认构图 → 满意才出视频（修改成本是视频的 1/18）
- 关键 grid（爆点/反派/心声）生首尾帧 → frames2video 锁死过渡

**Phase 2：出片**
- 4 模视频生成（auto 按文件存在自动选）
  - `image2video`（默认主用 80%）：分镜图首帧 + 动作 prompt
  - `frames2video`（关键爆点 10%）：首帧 + 尾帧 → AI 插值
  - `multiframe2video`（复杂动作 5%）：2-20 关键帧一镜到底
  - `multimodal2video`（fallback 5%）：9 image + 3 video + 3 audio
- dreamina CLI 集成（multimodal2video 全能参考 / Seedance 2.0 Fast VIP / 9:16 / 720p）
- **自动初剪**（v0.7.0）：按分镜顺序拼成一集，对白字幕、每集 AI 标识自动加
- **上线前检查**（v0.7.0）：AI 标识、备案类别、原创、授权（按 2026 年的新规）

不是"AI 编剧助手"。是 **爆款短剧产品经理 + 编剧 + 分镜师 + 制片 + 出片工程师** 的合体角色。

---

## 为什么做它

微短剧用户约 8.5 亿（广电总局，2026-09）；DataEye 预估 2026 年微短剧加 AI 剧漫剧市场超过 1210 亿元，其中 AI 剧和漫剧超过 400 亿（2026-08）。AI 短剧的真正瓶颈不在剧本，在**出片质量**和**上线合规**。

市面上的 AI 短剧 skill 普遍存在：

| 通病 | 本 skill 改进 |
|------|--------------|
| 跳过市场扫描直接写剧本 | 强制阶段 0 **市场情报扫描**（WebSearch + 反同质化建议）|
| 节奏全凭感觉 | `节奏地图.json` 精确到秒级，**红果必爆 7 招**校准（对抗式开场 / 30s 爆破 / 60s 爽点 / 90s 反转 / 120s 爽点 / 150s 钩子 / 180s 倒计时）|
| 全 5s 死板节奏 | **36 grid × 4-10s 变奏**（4×11 + 5×14 + 6×5 + 7×3 + 8-10×3）|
| 只出剧本不出视频 | 集成 dreamina CLI，**4 模视频生成**自动按文件存在选 |
| **直接 prompt → 视频，构图随机** | **加 Phase 1.5 分镜图层**：分镜图 = 视频首帧（image2video），构图固定 |
| **修改成本高（视频 55 积分/段）** | **分镜图 3 积分/张 = 1/18 成本**，先改图再出视频 |
| ref 库 5-20 张随便糊 | **工业级 80-150 张**（动作/表情/场景多角度/道具细节）|
| 单 prompt 100 字泛泛而谈 | **300-500 字镜头级**（动作物理/表情拆帧/灯光/字幕规格/物体材质）|
| bash 调 dreamina 中文 quoting 假死 | **Python subprocess args list**（避免 server 静默丢弃任务）|
| 角色档案空壳 | 弧光（起/拐/终）+ 视觉母题 + 反差点强制 |
| 一次出稿走人 | 阶段 5 **6 维度自我批判** + 必改清单 |
| 剪辑和 AI 标识全靠手工 | **`拼接初剪.py` 一键初剪**：对白字幕、每集 AI 角标、元数据隐式标识自动加（v0.7.0） |
| 路径写死 | 自动检测 cwd，可移植 |

---

## 安装

### 方法 1：装到 Claude Code 全局 skills 目录

```bash
# macOS / Linux / Windows Git Bash
git clone https://github.com/A-cat-with-carrots/OnlyShot ~/.claude/skills/ai-short-drama

# Windows PowerShell
git clone https://github.com/A-cat-with-carrots/OnlyShot "$env:USERPROFILE\.claude\skills\ai-short-drama"
```

### 方法 2：只在某个项目里用

```bash
cd <your-project>
mkdir -p .claude/skills
git clone https://github.com/A-cat-with-carrots/OnlyShot .claude/skills/ai-short-drama
```

重启 Claude Code（或新开会话），技能自动加载。升级：在技能目录里 `git pull`。

### 依赖

| 依赖 | 用在哪 | 什么时候要 |
|---|---|---|
| Claude Code | 全部 | 必须 |
| Python 3.10+ | `scripts/` 下的脚本 | 出图出片、初剪 |
| dreamina CLI（即梦官方） | ref 图、分镜图、视频段 | 出图出片；轻量模式不要 |
| ffmpeg（带 libass，常见完整版都带） | `拼接初剪.py` | 初剪 |

dreamina 安装和登录（2026-04 起是 OAuth 设备登录：终端打印一个地址和验证码，在浏览器里授权）：

```bash
curl -fsSL https://jimeng.jianying.com/cli | bash    # Windows 在 Git Bash 里跑
dreamina login
dreamina user_credit                                   # 看得到余额就是登录好了
```

认准官方地址 `jimeng.jianying.com/cli`。详见 [`references/jimeng-cli-guide.md`](references/jimeng-cli-guide.md)。

### 轻量模式：不装 dreamina 也能用

只想要剧本和分镜，或者习惯在即梦网页端出片：

1. 照常跟技能走完 Phase 1（市场情报、IP 简报、剧本、节奏地图、设定圣经、批判），这些只要 Claude Code；
2. 每集写好 `分镜.json` 后，跑 `python scripts/派生分集文件.py 分集/第01集_<集名>/分镜.json`，得到 `即梦批量包.md`（每段一条现成的 prompt）；
3. 把 prompt 粘到即梦网页端（或别的视频模型）出片，下载的片段按 `视频段/段01.mp4、段02.mp4……` 放好；
4. 装了 ffmpeg 就跑 `python scripts/拼接初剪.py <项目目录> 01 --allow-missing`，拼成带字幕和 AI 标识的初剪。

---

## 用法

在 Claude Code 里说一句：

```
> 我想做一部短剧：996 程序员重生为哮天犬，开局触发反 PUA 系统
```

技能自动触发，按工业级 5 步流程跑：

```
┌─ Phase 1：创作（成本低，反复迭代）─────────────────┐
│  阶段 0：市场情报扫描                              │
│  阶段 1：IP 简报（5 子步）                         │
│  阶段 2：故事架构 + 节奏地图（4 子步）             │
│  阶段 3：设定圣经（4 子步）                        │
│  阶段 3.5：ref 图自动生成（dreamina text2image）   │
│  阶段 5：批判 refine                              │
└──────────────────────────────────────────────────┘
                      ↓
┌─ Phase 1.5：分镜图（v0.6.0 工业级核心）⭐ ──────────┐
│  3A：写该集分镜.json（v0.3.0 字段：video_mode +   │
│       first_frame_path + last_frame_path）         │
│  3B：python scripts/ref完备性检查.py              │
│  3C：python scripts/生成分镜图.py（每 grid        │
│       1-4 张候选关键帧 = 视频首帧）                │
│  3D：人工选图（grid01_候选3.png → grid01.png）    │
│  3E：关键 grid 生首尾帧（gridXX_首.png + 尾.png） │
└──────────────────────────────────────────────────┘
                      ↓
┌─ Phase 2：出片（成本高，按集解锁）────────────────┐
│  4C：python scripts/生成分集视频.py --dry-run     │
│       先看预估积分，再正式跑（auto 选 4 模）       │
│  4D：python scripts/拼接初剪.py → 初剪.mp4        │
│       字幕 + AI 角标 + 元数据标识自动加            │
│       配乐（可选 Sonilo）→ 剪映精修               │
│  4E：上线前检查（compliance-2026.md）             │
└──────────────────────────────────────────────────┘
```

每阶段产出独立文件，最终目录：

```
SD-001_<slug>/
├── 01_市场情报.md
├── 02_IP简报.md           ← 含视觉指纹（ref 阶段 append；v0.6.0 起分镜图阶段用 --no-fingerprint 关闭）
├── 03_完整剧本.md         ← 24 集精华 + v2.1 7 招校准
├── 04_节奏地图.json       ← 每集 beats + 7 招节点
├── 05_角色圣经.md
├── 06_场景圣经.md
├── 07_道具圣经.md
├── 08_自我批判.md
├── ref图/                 ← 工业级 80-150 张
│   ├── 角色/             (5-8 张/角色：基础 + 动作 + 表情)
│   ├── 场景/             (3-5 张/场景：多角度 + 多光线)
│   └── 道具/             (30-50 张：关键道具全角度)
└── 分集/
    ├── 第01集_<集名>/
    │   ├── 剧本.md
    │   ├── 分镜.json     ← 含 video_mode + first_frame_path + last_frame_path
    │   ├── 镜头清单.md
    │   ├── 即梦批量包.md
    │   ├── 分镜图/       ← v0.3.0 新增（Phase 1.5 产物）
    │   │   ├── grid01_候选1.png
    │   │   ├── grid01_候选2.png
    │   │   ├── grid01.png        ← 用户选定（视频首帧）
    │   │   ├── grid05_首.png     ← 关键 grid 首帧
    │   │   ├── grid05_尾.png     ← 关键 grid 尾帧
    │   │   └── ...
    │   ├── 视频段/       ← Phase 2 产物
    │   │   ├── 段01.mp4
    │   │   └── ...
    │   ├── 初剪.mp4      ← v0.7.0 自动初剪（字幕 + AI 标识）
    │   └── 10_上线前检查.md
    └── ... (EP02-EP24)
```

---

## 即梦 / Seedance 2.0 出片对接

每个分镜的 `jimeng_prompt` 已按 v0.6.0 工业级 8 段 SOP 拼好（**CHARACTER / BACKGROUND / ACTION / SCENE / CAMERA / LIGHT / TEXT / STYLE**），开箱即用：

- ✅ **prompt 字数自动控制 ≤ 1500 字符**（即梦 5.0 实测上限；ref 段 300-500 字，分镜图段 1200-1500 字）
- ✅ `(@角色_ref.png)` 引用 + 全角中文 `）` regex 兼容（v0.2.0 修）
- ✅ **视觉指纹分阶段隔离**（ref 阶段 append `neutral/flat`；分镜图阶段用 `--no-fingerprint` 关闭，防 ref 风格词污染 dramatic 光，v0.6.0）
- ✅ **NOT humans 子句自动加**（每个主角单独 STYLE 段，防即梦 5.0 拟物化 → chibi 人体偏置）
- ✅ **敏感词预检**（`--check-sensitive` 扫反派词 / 暧昧词 / 中文敏感词，命中 warn，v0.6.0）
- ✅ **ref 完备性预检**（生视频前自动扫描，缺图就 exit 1）
- ✅ 9:16 竖屏 + 对白字幕 + 每集 AI 标识（`拼接初剪.py` 自动加，2026-09-01 起的要求）
- ✅ **multimodal2video stuck 自动检测**（提交后 check `queue_status=Generating`，否则 fallback list_task 找回 submit_id）

每集额外产 `即梦批量包.md`：36 段 prompt 顺序排好 + ref 引用清单 + 剪映拼接规范 + 故障排查表（v0.6.0 共 17 失败模式：v0.2.0 基础设施 13 + v0.6.0 即梦内容 4）。

---

## 工业级 5 步流程速览

### Step 1：剧本（LLM）
红果必爆 7 招校准 + 36 grid × 4-10s 变奏 + 24 集精华版

### Step 2：分镜（grid + 动作 + 对白）
每 grid 含 `_duration` / `video_mode` / `first_frame_path` / `last_frame_path`

### Step 3：分镜图（v0.6.0 工业级核心）
```bash
# 标准跑（推荐）
python scripts/生成分镜图.py <项目目录> 01 --candidates=1 --no-fingerprint --check-length --auto-pick-first
# 36 grid × 1 候选 = 36 张 × 3 积分 = 108 积分 ≈ ¥7.7

# 关键爆点单 grid 4 候选
python scripts/生成分镜图.py <项目目录> 01 13 --candidates=4 --no-fingerprint
```
v0.6.0 必加 flag：
- `--no-fingerprint`：防 ref 风格词 `neutral/flat/NOT cinematic` 污染分镜图 dramatic 光
- `--check-length`：跑前 prompt > 1500 字 warn（即梦 5.0 硬上限）
- `--check-sensitive`：扫反派词 / 暧昧词 / 中文敏感词

人工选图：`mv grid01_候选3.png grid01.png`

### Step 4：视频段（4 模 auto 选）
```bash
python scripts/生成分集视频.py <项目目录> 01 --dry-run   # 先看每段走哪种模式、缺哪些 ref、预估积分（不花钱）
python scripts/生成分集视频.py <项目目录> 01 5           # 试水前 5 段
python scripts/生成分集视频.py <项目目录> 01             # 全跑
python scripts/生成分集视频.py <项目目录> 01 --model-version seedance2.0fast   # 没开即梦会员时
```

### Step 5：剪辑
先一键拼初剪（v0.7.0）：

```bash
python scripts/拼接初剪.py <项目目录> 01   # → 初剪.mp4（1080×1920，对白字幕，全程「AI生成」角标，元数据 AIGC）+ 初剪.srt
```

再按需配音（豆包 TTS 等）、配乐，进剪映精修（9:16 / 1080×1920 / 30fps）。配乐也可以按成片自动生成（可选，Sonilo）：

```bash
python scripts/生成配乐.py 分集/第01集_<集名>/初剪.mp4               # 配乐：跟剪辑点和情绪走，时长自动对齐
python scripts/生成配乐.py 分集/第01集_<集名>/视频段/段13.mp4 --sfx   # 音效：关键段按画面生成
```

Sonilo 是第三方付费服务（由 Sonilo 团队贡献）：成片会上传到 Sonilo 处理；免费档仅限个人非商用，发平台变现要 Pro 及以上，以 Sonilo 条款为准。4 个示例 + 题材 prompt 模板速查表见 [`references/sonilo-audio-guide.md`](references/sonilo-audio-guide.md)。

上线前按 [`references/compliance-2026.md`](references/compliance-2026.md) 过一遍：每集 AI 标识、备案类别、原创、授权。

---

## 4 模视频生成选择矩阵

| 模式 | 触发条件 | 占比 | 用途 |
|------|---------|------|------|
| **image2video** | `分镜图/gridXX.png` | 80% | 默认主用 - 分镜图作首帧 + 动作 prompt |
| **frames2video** | `分镜图/gridXX_首.png` + `gridXX_尾.png` | 10% | 关键爆点 - 首帧 + 尾帧锁定过渡 |
| **multiframe2video** | `分镜图/gridXX_帧1.png` ~ `帧N.png`（≥2） | 5% | 复杂动作 - 一镜到底 |
| **multimodal2video** | 无分镜图 fallback | 5% | 多 ref 综合（角色 + 场景 + 道具同时锁定）|

---

## 红果必爆 7 招（每集必上）

| 招 | 节点 | 落地 |
|----|------|------|
| **招 1：对抗式开场** | 0-3s | 角色被外力施压（甩咖啡/耳光/砸杯/推搡），不要自残式（吐血/晕倒）|
| **招 2：30s 爆破点** | 25-32s | 视觉/物理冲击（踢飞 / 玻璃碎 / 雷劈）+ 必爆鼓点 |
| **招 3：60s 第 1 爽点** | 55-65s | 小赢（点头 / 表扬 / 反派愣 / 模块解锁）|
| **招 4：90s 第 2 反转** | 85-95s | 隐藏信息揭露（伏笔显形 / 反派起疑）|
| **招 5：120s 第 2 爽点** | 115-125s | 大赢（升职 / 反派打脸 / 联盟成立）|
| **招 6：150s 终极钩子** | 145-160s | 反派狠话 / 主角神秘瞳孔 / 心声穿透 |
| **招 7：180s 倒计时** | 终结前 4-9s | 屏幕红色倒计时数字 + 字幕「未完待续」|

详见 [`references/v21-97-percent-rules.md`](references/v21-97-percent-rules.md)（24 集校准模板）。

---

## 文件结构

```
ai-short-drama/
├── SKILL.md                           # 主入口（5 步流程编排）
├── README.md / README_EN.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── .github/                           # issue 模板 + Actions 离线检查
├── references/
│   ├── market-pulse.md                # 阶段 0 深度
│   ├── ip-strategy.md                 # 阶段 1 深度
│   ├── archetype-catalog.md           # 短剧角色 / 题材原型库
│   ├── story-architecture.md          # 阶段 2 深度
│   ├── character-design.md            # 阶段 3 深度
│   ├── scripting-craft.md             # 阶段 4A 深度
│   ├── storyboard-craft.md            # 36 grid × 4-10s 变奏（v0.2.0，v0.6.0 prompt 模板部分废弃）
│   ├── storyboard-frames-craft.md     # 分镜图工艺 + 4 模选择（v0.3.0）
│   ├── storyboard-frame-industrial.md # ⭐ v0.6.0 分镜图 8 段 SOP（CHARACTER/BACKGROUND/ACTION/SCENE/CAMERA/LIGHT/TEXT/STYLE）
│   ├── ref-prompt-industrial.md       # ⭐ v0.6.0 ref 工艺 6 段 identity block
│   ├── jimeng-failure-modes.md        # ⭐ v0.6.0 即梦 5.0 故障排查 + 敏感词清单
│   ├── jimeng-cli-guide.md            # dreamina CLI 集成指南（v0.7.0 加模型现状：CLI 限制 / Seedance 2.5 / 可灵 4.0）
│   ├── jimeng-handoff.md              # 即梦 / Seedance 2.0 对接
│   ├── visual-consistency-sop.md      # 视觉一致性方法论（v0.6.0 已大幅瘦身归档）
│   ├── critic-checklist.md            # 阶段 5 深度
│   ├── cliche-detector.md             # 反套路检测器
│   ├── genre-flavors.md               # 7 流派定调（v0.4.0 加 F 抽象拟人流，v0.7.0 加 G AI 仿真人流）
│   ├── red-fruit-data.md              # 红果实战数据
│   ├── v21-97-percent-rules.md        # 红果必爆 7 招 + 24 集校准
│   ├── troubleshooting.md             # 13 失败模式 + 解法
│   ├── sonilo-audio-guide.md          # Sonilo AI 配乐/音效指南（阶段 4.D 可选，4 示例 + 题材模板）
│   ├── compliance-2026.md             # ⭐ v0.7.0 上线前合规（AI 标识 / 备案分类 / 原创 / 肖像声音）
│   └── schemas.md                     # 所有 JSON 结构
├── scripts/
│   ├── 生成分镜图.py                  # Phase 1.5 - 每 grid 1-4 张候选（v0.7.0 加 --dry-run）
│   ├── 生成分集视频.py                # Phase 2 - 4 模 auto 选（v0.7.0 加 --dry-run / --model-version）
│   ├── 拼接初剪.py                    # ⭐ v0.7.0 阶段 4.D - 视频段 → 初剪（字幕 + AI 标识）
│   ├── ref完备性检查.py               # 生视频前预检 ⭐ v0.2.0
│   ├── 派生分集文件.py                # 从分镜.json 派生即梦批量包/镜头清单
│   ├── 生成配乐.py                    # 阶段 4.D 可选 - Sonilo 配乐/音效（按成片生成）
│   ├── extract_prompts.py             # 视觉指纹抽取
│   ├── setup-jimeng.sh                # dreamina CLI 安装
│   ├── 生成分集视频.sh                # 旧 bash（deprecated）
│   └── 生成参考图.sh                  # ref 图批量生成
├── assets/templates/                  # 模板（项目元数据、分镜.json、圣经、剧本、上线前检查）
└── evals/evals.json                   # 测试用例 + 18 条断言
```

---

## 默认参数（v0.7.0）

| 项 | 默认值 | 来源 |
|----|--------|------|
| 单集时长 | **180-195s** | 红果实测最优（不严卡 180）|
| 集数 | **24 集精华** / 72 集（常规） | 24 集省成本 + 紧凑爆点 |
| 单集分镜数 | **36 grid × 4-10s 变奏** | multimodal2video 最低 4s |
| 时长变奏分布 | 4×11 + 5×14 + 6×5 + 7×3 + 8-10×3 | v2.1 红果必爆铁律 |
| 视频比例 | **9:16 竖屏** | 红果/抖音/快手统一 |
| 视频默认模式 | **image2video**（基于分镜图） | v0.3.0 工业级核心 |
| 字幕 / AI 标识 | **开**：对白字幕 + 每集全程 AI 角标 + 元数据隐式标识 | 《微短剧发展管理办法》2026-09-01 起 |
| ref 库目标 | **80-150 张**（工业级）| 含动作/表情/场景多角度/道具细节 |
| 单 prompt 字数 | **ref 段 300-500 字 / 分镜图段 1200-1500 字** | v0.6.0 区分（即梦硬上限 1500） |
| 分镜图候选数 | 关键 grid 4 / 标准 1-2（v0.6.0 实测单跑通过率高） | v0.6.0 |
| 出片前 | `--dry-run` 先看预估积分 | v0.7.0 |
| 流派 | 互动选 | 红果纯爽 / 精品悬疑 / 漫剧奇观 / 沙雕轻喜 / 年代爽剧 / 抽象拟人 / **AI 仿真人（v0.7.0 新）** |

---

## 17 失败模式（已沉淀解法）

**v0.2.0 基础设施层（13 模式）**：

| # | 问题 | 解法 |
|---|------|------|
| 1 | bash eval 中文/特殊字符 quoting → multimodal task 假死 | Python subprocess args list |
| 2 | awk seg_num UTF-8 字节切错（"段 �"） | substr 整段 + gsub 去非数字 |
| 3 | multimodal stuck 任务无报错 | 提交后 check queue_status，fallback list_task |
| 4 | ref 引入新元素无新 ref | `ref完备性检查.py` 强制预检 |
| 5 | regex 漏全角中文 `）` | 加 `）` 到 stop 字符 |
| 6 | Python stdout UTF-8 截断 | `sys.stdout.reconfigure(encoding='utf-8')` |
| 7 | Win Store python3 stub | `python \|\| python3` + verify |
| 8 | --poll exit code 异常 | 不依赖 exit code，看文件落盘 |
| 9 | 风格漂移（ref 阶段） | 视觉指纹自动 append（仅 ref 阶段，分镜图阶段用 `--no-fingerprint`） |
| 10 | 多视图重复（ref 阶段） | "4 distinct angles, no duplicate views"（仅 ref 阶段适用） |
| 11 | 文字 vs 乱码混淆 | 文字 OK，乱码才是问题，去无意义数字 |
| 12 | 角色名误删 | 工牌 / 字幕 / 对白点名 |
| 13 | 网页端 multimodal 不可见 | 在「视频生成 → 全能参考 → 历史」tab |

**v0.6.0 即梦内容层（4 模式）** — 详见 [`references/jimeng-failure-modes.md`](references/jimeng-failure-modes.md)：

| # | 问题 | 解法 |
|---|------|------|
| 14 | prompt > 1500 字 → `ret=1046 InvalidNode` | 严守 ≤ 1500，理想 1200-1400 |
| 15 | 反派词 / 暧昧词 → `generation failed`（内容审核） | sinister → moody / blush on cheeks → rose tint |
| 16 | 视觉指纹 `neutral/flat` 污染分镜图 dramatic 光 | 分镜图阶段 `--no-fingerprint` |
| 17 | ref 库工艺偏置（古建筑必出 chibi 人体） | 前期 IP 设计阶段避坑：选玻璃塔 / 简单几何，避复杂古建筑 |

详见 [`references/troubleshooting.md`](references/troubleshooting.md)（v0.2.0 13 模式）+ [`references/jimeng-failure-modes.md`](references/jimeng-failure-modes.md)（v0.6.0 4 模式 + 反派词替换表 + 4 grid case）。

---

## 版本

当前 **v0.7.0**（2026-11-10），完整记录见 [`CHANGELOG.md`](CHANGELOG.md)。v0.7.0 主要变化：

- `scripts/拼接初剪.py`：视频段一键拼成初剪，字幕、AI 角标、元数据标识自动加
- 上线前合规：`references/compliance-2026.md` + 阶段 4.E + `10_上线前检查.md`（按 2026 年 6 月、7 月、11 月的新规整理）
- 出片脚本 `--dry-run` 先看预估积分；视频脚本 `--model-version`，没开即梦会员也能跑
- 第 7 流派 G AI 仿真人流；dreamina 指南加模型现状（Seedance 2.5、可灵 4.0、CLI 限制）
- 合并 Sonilo 配乐 / 音效（#5，第三方付费服务，可选）
- 英文 README、issue 模板、CONTRIBUTING、GitHub Actions 离线检查

---

## 路径处理

技能自动选择项目目录：

1. 用户当前在某项目里且有 `projects/` 子目录 → 用 `<cwd>/projects/`
2. 用户明确指定 → 用指定路径
3. 都没有 → 创建 `<cwd>/short-drama-projects/` 并告诉用户

**绝不**写死 `/data/dongman/` 这类绝对路径。

---

## 当前已知热点参考（2026-11 更新）

> 技能每次开始都会联网更新（阶段 0），下表只作静态参考，引用前看日期。

**真人剧题材**（DataEye《2026 上半年真人微短剧数据报告》，按播放增量，2026-08-26）：

| 位置 | 题材 |
|---|---|
| 最多 | 现代、都市日常、打脸虐渣 |
| 其次 | 逆袭、现代言情、总裁、大女主 |
| 单部回报高（潜力） | 大男主、马甲、闪婚 |

**其他信号**（二手报道，口径不一）：

- 「黑帮」「神豪」这类中腰部题材供给少、热度高；甜宠、霸总、逆袭的通用模板供给过剩（DataEye 上半年）
- AI 剧在玄幻、科幻这类视觉特效题材上更受关注；红果漫剧榜「发配边关」系列三季同时进前 20（2026-07）
- 平台扶持往漫剧和 AI 仿真人剧走；官方要求「扶持真人剧，规范 AI 剧」（广电总局 2026-11-05）

**本项目实战过的**：职场反 PUA + 系统流（SD-001 重生哮天犬）、城市拟人恋综（SD-002）。

详见 [`references/market-pulse.md`](references/market-pulse.md) + [`references/red-fruit-data.md`](references/red-fruit-data.md)。

---

## 贡献

PR 和 issue 都欢迎，先看 [`CONTRIBUTING.md`](CONTRIBUTING.md)（接第三方付费服务有六条规矩）。issue 有三个模板：问题报告、功能建议、作品分享。

重点方向：

- 题材原型库（男频、漫剧、AI 仿真人、出海 TikTok）
- Seedance 2.5 / 可灵 4.0 的 30 秒多镜头出片接入
- 4 模视频生成的 best practice、新的失败模式
- 市场情报快照（每月一次，带出处和日期）
- 测试用例

---

## 致谢

- 原始灵感：[zhaihao118/Micro-Drama-Skills](https://github.com/zhaihao118/Micro-Drama-Skills)
- 工业级方法论参考：腾讯云《AI漫剧制作流程深度解析》/ 即梦官方 CLI 体验指南
- 7 招红果必爆铁律：woshipm 业界硬数据 + 红果 TOP100 EP01 拆解
- dreamina CLI 集成：字节跳动即梦官方 AGENT 工具
- 配乐 / 音效脚本：Sonilo 团队（[#5](https://github.com/A-cat-with-carrots/OnlyShot/pull/5)）

本 skill 在原始灵感基础上增加了：
- 工业级 5 步流程（剧本 → 分镜 → **分镜图** → 视频 → 剪辑）
- 4 模视频生成自动选（image2video / frames2video / multiframe2video / multimodal2video）
- 红果必爆 7 招校准（v2.1）
- 17 失败模式沉淀（v0.2.0 基础设施 13 + v0.6.0 即梦内容 4）
- 工业级 ref 库标准（80-150 张）
- 分镜图 8 段 prompt SOP（v0.6.0）：CHARACTER/BACKGROUND/ACTION/SCENE/CAMERA/LIGHT/TEXT/STYLE
- ref 6 段 identity block（v0.6.0）：IDENTITY/BODY/FACE/ATTIRE/LAYOUT/STYLE
- 即梦 5.0 故障排查 + 敏感词清单（v0.6.0）：3 类 fail 区分 + 1500 字硬上限 + 反派词替换表
- ref 库工艺偏置铁律（v0.6.0）：现代摩天楼易拟物 / 古建筑必出 chibi 人体
- bash → Python subprocess（避中文 quoting 任务静默丢弃）
- 36 grid × 4-10s 变奏
- F 抽象拟人流（v0.4.0）、G AI 仿真人流（v0.7.0）：7 流派定调
- 自动初剪 + 上线前合规（v0.7.0）

---

## License

MIT — 见 [LICENSE](LICENSE)
