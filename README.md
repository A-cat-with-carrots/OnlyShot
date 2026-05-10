# ai-short-drama

> **Industrial-grade AI Short Drama Production Skill for Claude Code**
> 一句"粗糙想法" → 工业级 5 步流程 → 可发红果/抖音的完整短剧（剧本 + 分镜图 + 视频段 + 剪辑包）

[![Skill](https://img.shields.io/badge/Claude-Skill-blueviolet)](https://docs.anthropic.com/en/docs/claude-code)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)
[![Version](https://img.shields.io/badge/Version-v0.3.0-orange)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)]()

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

不是"AI 编剧助手"。是 **爆款短剧产品经理 + 编剧 + 分镜师 + 制片 + 出片工程师** 的合体角色。

---

## 为什么做它

短剧赛道月活 1.7 亿、人均 101 分钟/天（红果 2026 数据）。AI 短剧的真正瓶颈不在剧本，在**出片质量**。

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
| 路径写死 | 自动检测 cwd，可移植 |

---

## 安装

### 方法 1：克隆到 Claude Code 全局 skills 目录

```bash
# Windows
git clone https://github.com/A-cat-with-carrots/ai-short-drama-skill "$env:USERPROFILE\.claude\skills\ai-short-drama"

# macOS / Linux
git clone https://github.com/A-cat-with-carrots/ai-short-drama-skill ~/.claude/skills/ai-short-drama
```

### 方法 2：作为项目本地 skill

```bash
cd <your-project>
mkdir -p .claude/skills
git clone https://github.com/A-cat-with-carrots/ai-short-drama-skill .claude/skills/ai-short-drama
```

### 依赖

- **Claude Code**（Windows / macOS / Linux）
- **dreamina CLI**（即梦官方 AGENT 工具，用于 ref 图 + 视频生成）：
  ```bash
  curl -fsSL https://jimeng.jianying.com/cli | bash
  dreamina login
  ```
  Windows 用户在 Git Bash 跑（不是 PowerShell）

重启 Claude Code（或新开会话），技能自动加载。

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
┌─ Phase 1.5：分镜图（v0.3.0 工业级核心）⭐ 新 ──────┐
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
│  4A：python scripts/生成分集视频.py              │
│       auto 模式按文件存在自动选 4 模               │
│  4B：用户在剪映拼接 + 配音 + BGM + 字幕            │
└──────────────────────────────────────────────────┘
```

每阶段产出独立文件，最终目录：

```
SD-001_<slug>/
├── 01_市场情报.md
├── 02_IP简报.md           ← 含视觉指纹（脚本自动 append 到所有 prompt）
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
    │   └── 视频段/       ← Phase 2 产物
    │       ├── 段01.mp4
    │       └── ...
    └── ... (EP02-EP24)
```

---

## 即梦 / Seedance 2.0 出片对接

每个分镜的 `jimeng_prompt` 已按 v0.3.0 工业级标准拼好（**镜头分段 + 角色细节 + 道具材质 + 物理动效 + 字幕规格 + 视觉指纹**），开箱即用：

- ✅ **300-500 字镜头级 prompt**（含动作物理 / 表情拆帧 / 灯光色温 / 字幕字体）
- ✅ `(@角色_ref.png)` 引用 + 全角中文 `）` regex 兼容（v0.2.0 修）
- ✅ **视觉指纹自动 append**（脚本读 02_IP简报.md 抽取，每段强制风格一致）
- ✅ **ref 完备性预检**（生视频前自动扫描，缺图就 exit 1）
- ✅ 9:16 竖屏强制 + 字幕中文括号 + AIGC 标识
- ✅ **multimodal2video stuck 自动检测**（提交后 check `queue_status=Generating`，否则 fallback list_task 找回 submit_id）

每集额外产 `即梦批量包.md`：36 段 prompt 顺序排好 + ref 引用清单 + 剪映拼接规范 + 故障排查表（13 失败模式）。

---

## 工业级 5 步流程速览

### Step 1：剧本（LLM）
红果必爆 7 招校准 + 36 grid × 4-10s 变奏 + 24 集精华版

### Step 2：分镜（grid + 动作 + 对白）
每 grid 含 `_duration` / `video_mode` / `first_frame_path` / `last_frame_path`

### Step 3：分镜图（v0.3.0 工业级核心）
```bash
python scripts/生成分镜图.py <项目目录> 01 --candidates=2
# 36 grid × 2 候选 = 72 张 × 3 积分 = 216 积分 ≈ ¥15
```
人工选图：`mv grid01_候选3.png grid01.png`

### Step 4：视频段（4 模 auto 选）
```bash
python scripts/生成分集视频.py <项目目录> 01 5    # B 试水前 5 段
python scripts/生成分集视频.py <项目目录> 01      # 全跑
```

### Step 5：剪辑
剪映 9:16 / 1080×1920 / 30fps + 配音（豆包 TTS）+ BGM（Suno）+ SFX（剪映音效库）+ AIGC 标识

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
├── README.md
├── LICENSE
├── references/
│   ├── market-pulse.md                # 阶段 0 深度
│   ├── ip-strategy.md                 # 阶段 1 深度
│   ├── archetype-catalog.md           # 短剧角色 / 题材原型库
│   ├── story-architecture.md          # 阶段 2 深度
│   ├── character-design.md            # 阶段 3 深度
│   ├── scripting-craft.md             # 阶段 4A 深度
│   ├── storyboard-craft.md            # 36 grid × 4-10s 变奏（v0.2.0）
│   ├── storyboard-frames-craft.md     # 分镜图工艺 + 4 模选择（v0.3.0 ⭐）
│   ├── jimeng-cli-guide.md            # dreamina CLI 集成指南
│   ├── jimeng-handoff.md              # 即梦 / Seedance 2.0 对接
│   ├── visual-consistency-sop.md      # 视觉一致性方法论
│   ├── critic-checklist.md            # 阶段 5 深度
│   ├── cliche-detector.md             # 反套路检测器
│   ├── genre-flavors.md               # 5 流派定调
│   ├── red-fruit-data.md              # 红果实战数据
│   ├── v21-97-percent-rules.md        # 红果必爆 7 招 + 24 集校准 ⭐
│   ├── troubleshooting.md             # 13 失败模式 + 解法 ⭐
│   └── schemas.md                     # 所有 JSON 结构
├── scripts/
│   ├── 生成分镜图.py                  # Phase 1.5 - 每 grid 1-4 张候选 ⭐ v0.3.0
│   ├── 生成分集视频.py                # Phase 2 - 4 模 auto 选 ⭐ v0.3.0
│   ├── ref完备性检查.py               # 生视频前预检 ⭐ v0.2.0
│   ├── 派生分集文件.py                # 从分镜.json 派生即梦批量包/镜头清单
│   ├── extract_prompts.py             # 视觉指纹抽取
│   ├── setup-jimeng.sh                # dreamina CLI 安装
│   ├── 生成分集视频.sh                # 旧 bash（deprecated）
│   └── 生成参考图.sh                  # ref 图批量生成
├── assets/templates/                  # 12 份模板（项目元数据 + 分镜.json + 9 圣经/剧本）
└── evals/evals.json                   # 测试用例 + 18 条断言
```

---

## 默认参数（v0.3.0）

| 项 | 默认值 | 来源 |
|----|--------|------|
| 单集时长 | **180-195s** | 红果实测最优（不严卡 180）|
| 集数 | **24 集精华** / 72 集（常规） | 24 集省成本 + 紧凑爆点 |
| 单集分镜数 | **36 grid × 4-10s 变奏** | multimodal2video 最低 4s |
| 时长变奏分布 | 4×11 + 5×14 + 6×5 + 7×3 + 8-10×3 | v2.1 红果必爆铁律 |
| 视频比例 | **9:16 竖屏** | 红果/抖音/快手统一 |
| 视频默认模式 | **image2video**（基于分镜图） | v0.3.0 工业级核心 |
| 字幕 | **开**（中文括号包 + AIGC 标识）| 红果强制 |
| ref 库目标 | **80-150 张**（工业级）| 含动作/表情/场景多角度/道具细节 |
| 单 prompt 字数 | **300-500 字** | 含动作物理 + 表情拆帧 + 灯光 + 字幕规格 |
| 分镜图候选数 | 关键 grid 4 / 标准 2 / 过渡 1 | v0.3.0 默认 |
| 流派 | 互动选 | 红果纯爽 / 精品悬疑 / 漫剧奇观 / 沙雕轻喜 / 年代爽剧 |

---

## 13 失败模式（已沉淀解法）

| # | 问题 | 解法 |
|---|------|------|
| 1 | bash eval 中文/特殊字符 quoting → multimodal task 假死 | Python subprocess args list |
| 2 | awk seg_num UTF-8 字节切错（"段 �"） | substr 整段 + gsub 去非数字 |
| 3 | multimodal stuck 任务无报错 | 提交后 check queue_status，fallback list_task |
| 4 | ref 引入新元素无新 ref | `ref完备性检查.py` 强制预检 |
| 5 | regex 漏全角中文 `）` | 加 `）` 到 stop 字符 |
| 6 | Python stdout UTF-8 截断 | `sys.stdout.reconfigure(encoding='utf-8')` |
| 7 | Win Store python3 stub | `python || python3` + verify |
| 8 | --poll exit code 异常 | 不依赖 exit code，看文件落盘 |
| 9 | 风格漂移 | 视觉指纹自动 append |
| 10 | 多视图重复 | "4 distinct angles, no duplicate views" |
| 11 | 文字 vs 乱码混淆 | 文字 OK，乱码才是问题，去无意义数字 |
| 12 | 角色名误删 | 工牌 / 字幕 / 对白点名 |
| 13 | 网页端 multimodal 不可见 | 在「视频生成 → 全能参考 → 历史」tab |

详见 [`references/troubleshooting.md`](references/troubleshooting.md)。

---

## 版本历史

### v0.3.0（2026-05-08）⭐ 当前
- 加 Phase 1.5 分镜图层（修改成本 3 积分 vs 视频 55 积分 = 18 倍便宜）
- 4 模视频生成（image2video / frames2video / multiframe2video / multimodal2video auto 选）
- 关键 grid 首尾帧锁定（爆点/反派/心声）
- ref 5-8 最优（不塞 9 → 注意力分散）
- @ 指令显式职责语法
- 新增 `生成分镜图.py` + `storyboard-frames-craft.md`

### v0.2.0（2026-05-08）
- bash → Python subprocess（避中文 prompt quoting 任务静默丢弃）
- 36 grid × 4-10s 变奏（替代 60 × 3s 死板）
- 红果必爆 7 招校准（对抗式开场 / 30s 爆破 / 60s 爽点 / 90s 反转 / 120s 爽点 / 150s 钩子 / 180s 倒计时）
- 工业级 ref 库 80-150 张（动作 / 表情 / 多角度 / 道具细节）
- 单 prompt 300-500 字（动作物理 / 表情拆帧 / 灯光 / 字幕规格）
- 13 失败模式 + 自动 ref 预检 + multimodal stuck 自动检测
- 新增 `troubleshooting.md` + `v21-97-percent-rules.md` + 3 个 Python 脚本

### v0.1.x（2026-04）
- 初版 5 阶段创作流程（市场情报 → IP 简报 → 故事架构 → 设定圣经 → 批判）
- 60 grid × 3s 默认
- 5 流派定调（红果纯爽 / 精品悬疑 / 漫剧奇观 / 沙雕轻喜 / 年代爽剧）
- 反套路检测 + 自我批判

---

## 路径处理

技能自动选择项目目录：

1. 用户当前在某项目里且有 `projects/` 子目录 → 用 `<cwd>/projects/`
2. 用户明确指定 → 用指定路径
3. 都没有 → 创建 `<cwd>/short-drama-projects/` 并告诉用户

**绝不**写死 `/data/dongman/` 这类绝对路径。

---

## 当前已知热点参考（2026 年 5 月）

> 技能每次开始都会联网更新，下表仅供静态参考。

### 女频（占红果 81.7%）

| 题材 | 状态 |
|------|------|
| 老年女性觉醒/复仇 | 🔥 上升 |
| 重生复仇 + 商战 | 🔥 稳定爆款 |
| 神医/相师/命格 | 🔥 上升 |
| 离婚追妻火葬场 | 🟡 平稳 |
| 霸总虐恋（纯虐） | 🔻 衰退 |
| 穿越宫斗（无新意） | 🔻 衰退 |

### 男频

| 题材 | 状态 |
|------|------|
| **职场反 PUA + 系统流** | 🔥 新兴黑马（v0.3.0 SD-001 实战）|
| 都市脑洞 + 响指系统 | 🔥 男频天花板 |
| 都市修真种田 | 🔥 完读 Top3 |
| 悬疑民俗 / 风水 | 🔥 上升黑马 |
| 赘婿逆袭 | 🔻 已饱和 |

详见 [`references/market-pulse.md`](references/market-pulse.md) + [`references/red-fruit-data.md`](references/red-fruit-data.md)。

---

## 贡献

PR 欢迎。重点方向：

- 增加题材原型库（特别是男频、漫剧、出海 TikTok）
- 优化即梦 / Seedance 2.0 prompt 模板（Phase 1.5 分镜图工艺）
- 4 模视频生成的 best practice 沉淀
- 更新市场情报快照（每月一次）
- 添加测试用例

---

## 致谢

- 原始灵感：[zhaihao118/Micro-Drama-Skills](https://github.com/zhaihao118/Micro-Drama-Skills)
- 工业级方法论参考：腾讯云《AI漫剧制作流程深度解析》/ 即梦官方 CLI 体验指南
- 7 招红果必爆铁律：woshipm 业界硬数据 + 红果 TOP100 EP01 拆解
- dreamina CLI 集成：字节跳动即梦官方 AGENT 工具

本 skill 在原始灵感基础上增加了：
- 工业级 5 步流程（剧本 → 分镜 → **分镜图** → 视频 → 剪辑）
- 4 模视频生成自动选（image2video / frames2video / multiframe2video / multimodal2video）
- 红果必爆 7 招校准（v2.1）
- 13 失败模式沉淀（troubleshooting.md）
- 工业级 ref 库标准（80-150 张）
- 单 prompt 300-500 字镜头级
- bash → Python subprocess（避中文 quoting 任务静默丢弃）
- 36 grid × 4-10s 变奏

---

## License

MIT — 见 [LICENSE](LICENSE)
