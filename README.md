# ai-short-drama

> **Refined AI Short Drama IP Creation Skill for Claude Code**
> 一句"粗糙想法" → 可直接喂给即梦/Seedance 2.0 出片的完整短剧 IP 包

[![Skill](https://img.shields.io/badge/Claude-Skill-blueviolet)](https://docs.anthropic.com/en/docs/claude-code)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)]()

---

## 它是什么

把你扔过去的一句话——

> "奶奶 80 大寿当天宣布断亲"

——变成可以**直接复制粘贴到即梦**就能出片的整套短剧 IP：

- **市场情报扫描**（搜近 30 天红果/番茄/抖音热什么、避开衰退题材）
- **IP 简报**（题材原型 + 对标作品 + 核心钩子 + 重复爽点公式 + 集数定价）
- **节奏地图**（每集每个 beat 精确到秒：cold_open / twist / satisfaction / cliffhanger）
- **设定圣经**（角色弧光 + 视觉母题 + 反差点 + 即梦 ref prompt）
- **逐集脚本**（冷开场 + 节奏标记 + 中文对白 + 潜台词 + 音效配方）
- **9 宫格分镜 JSON**（每格含完整即梦 `jimeng_prompt`）
- **镜头清单**（导演表）
- **批量生成包**（剪映拼接规范）
- **批判 refine**（6 维度自评 + 必改清单 + 平台审核扫描）

不是"AI 编剧助手"。是 **爆款短剧产品经理 + 编剧 + 分镜师 + 制片** 的合体角色。

---

## 为什么做它

短剧赛道现在月活 1.7 亿、人均 101 分钟/天（红果 2026 数据），平台审核三轮拉高，"粗制滥造剧本"已经赚不到钱了。

市面上的 AI 短剧 skill 普遍存在：

| 通病 | 本 skill 改进 |
|------|--------------|
| 直接进入第 1 集，不看市场 | 强制阶段 0 **市场情报扫描**（WebSearch + 反同质化建议）|
| 没有节奏地图 | `beat_sheet.json` 精确到秒级，10 种 beat 类型枚举 |
| 没有情绪曲线建模 | 每集 0-10 分情绪强度 + 不允许连续 3 集 < 6 |
| 角色档案空壳 | 弧光（起/拐/终）+ 视觉母题 + 反差点强制 |
| 一次出稿走人 | 阶段 5 **6 维度自我批判** + 必改清单 |
| 路径写死 | 自动检测 cwd，可移植 |
| 集数硬性 25、字幕硬关 | 集数可配（默认 24）、字幕用中文括号（短剧实际带字幕）|

---

## 安装

### 方法 1：克隆到 Claude Code 全局 skills 目录

```bash
# Windows
git clone https://github.com/<your-username>/ai-short-drama-skill "$env:USERPROFILE\.claude\skills\ai-short-drama"

# macOS / Linux
git clone https://github.com/<your-username>/ai-short-drama-skill ~/.claude/skills/ai-short-drama
```

### 方法 2：作为项目本地 skill

```bash
cd <your-project>
mkdir -p .claude/skills
git clone https://github.com/<your-username>/ai-short-drama-skill .claude/skills/ai-short-drama
```

重启 Claude Code（或新开会话），技能自动加载。

---

## 用法

在 Claude Code 里说一句：

```
> 我想做一部短剧：奶奶 80 大寿宣布断亲，背后是 30 年前家族秘密
```

技能自动触发，按 5 阶段流程跑：

```
阶段 0：市场情报扫描          ─┐
阶段 1：IP 7 维度定位          ├─→ 每阶段停下让你确认
阶段 2：故事架构 + 节奏地图    │
阶段 3：设定圣经                │
阶段 4：逐集脚本 + 9 宫格分镜  │
阶段 5：批判 refine            ─┘
```

每阶段产出独立文件，最终目录：

```
SD-001_dqnn/
├── ip_brief.md
├── full_script.md
├── beat_sheet.json
├── character_bible.md
├── scene_bible.md
├── prop_bible.md
├── episodes/
│   ├── EP01/
│   │   ├── script.md
│   │   ├── storyboard.json
│   │   ├── shot_list.md
│   │   └── jimeng_batch.md
│   └── ... (EP02-EP24)
└── critique.md
```

---

## 即梦 / Seedance 2.0 出片对接

每个分镜的 `jimeng_prompt` 已按即梦官方 7 要素拼好（**主体+细节+背景+运动+风格+情感+镜头**），开箱即用：

- ✅ `(@角色名_ref.png)` 引用全能参考
- ✅ 每段强声明「同一角色服装/发型不变」防脸跳
- ✅ 视觉风格关键词每段重写（即梦每段独立生成）
- ✅ 9:16 竖屏强制
- ✅ 字幕用中文括号
- ✅ 排除项模板（防多宫格出现在画面、防水印、防字幕错乱）

每集额外产 `jimeng_batch.md`：18 段 prompt 顺序排好 + 上传 ref 图清单 + 剪映拼接规范 + 故障排查表。

---

## 5 阶段速览

### 阶段 0：市场情报扫描
- 搜红果排行榜 / 番茄改编榜 / 抖音热点
- 标出用户题材的当前位置（蓝海 / 红海 / 衰退）
- 衰退题材直接告诉用户并给替代方向

### 阶段 1：IP 7 维度定位
1. 题材原型（主+副，从 30+ 原型库选）
2. 目标受众（性别/年龄/平台/付费意愿）
3. 对标 IP（"X 的设定 + Y 的节奏"）
4. **核心钩子**（≤ 25 字一句话）
5. **重复爽点公式**（触发 + 主角动作 + 对方反应）
6. 集数与定价（免费 24-30 / 付费 60-100，第 10 集首付费）
7. 基调与视觉

### 阶段 2：故事架构
- N 集 beat sheet
- 节奏地图（10 种 beat 类型枚举）
- 情绪曲线
- 伏笔账本（setup ↔ payoff 双向追踪）

### 阶段 3：设定圣经
- 角色 ≤ 6（每个含弧光 + 视觉母题 + 反差点 + 标志动作 + 口头禅 + 服装表 + 即梦 ref prompt）
- 场景 ≤ 5（出现 ≥ 3 集才收）
- 道具 ≤ 5（有剧情/象征意义才收）

### 阶段 4：逐集脚本 + 分镜
- 冷开场（前 3-5 秒逐字写）
- 节奏标记（`[钩子]` `[爽点]` `[反转]` `[卡点]`）
- 中文对白 ≤ 15 字/句 + 潜台词
- 9 宫格分镜 JSON（每格 14 字段含完整 `jimeng_prompt`）
- 镜头清单（导演表）

### 阶段 5：批判 refine（不要跳）
- 黄金 3 秒钩子强度
- 可预测度
- 同质化风险（对比近 30 天爆款）
- 爽点密度
- 角色辨识度
- 付费点强度

每项扣分 ≥ 3 → 必须在原文件打补丁。

---

## 文件结构

```
ai-short-drama/
├── SKILL.md                          # 主入口（5 阶段编排）
├── references/
│   ├── market-pulse.md               # 阶段 0 深度
│   ├── ip-strategy.md                # 阶段 1 深度
│   ├── archetype-catalog.md          # 短剧角色 / 题材原型库
│   ├── story-architecture.md         # 阶段 2 深度
│   ├── character-design.md           # 阶段 3 深度
│   ├── scripting-craft.md            # 阶段 4A 深度
│   ├── storyboard-craft.md           # 阶段 4B 深度
│   ├── jimeng-handoff.md             # 即梦 / Seedance 2.0 对接
│   ├── critic-checklist.md           # 阶段 5 深度
│   └── schemas.md                    # 所有 JSON 结构
├── assets/templates/                 # 10 份模板
└── evals/evals.json                  # 测试用例 + 18 条断言
```

---

## 路径处理

技能自动选择项目目录：

1. 用户当前在某项目里且有 `projects/` 子目录 → 用 `<cwd>/projects/`
2. 用户明确指定 → 用指定路径
3. 都没有 → 创建 `<cwd>/short-drama-projects/` 并告诉用户

**绝不** 写死 `/data/dongman/` 这类绝对路径。

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
| 都市脑洞 + 响指系统 | 🔥 男频天花板 |
| 都市修真种田 | 🔥 完读 Top3 |
| 悬疑民俗 / 风水 | 🔥 上升黑马 |
| 赘婿逆袭 | 🔻 已饱和 |

详见 [`references/market-pulse.md`](references/market-pulse.md)。

---

## 贡献

PR 欢迎。重点方向：

- 增加题材原型库（特别是男频、漫剧、出海 TikTok）
- 优化即梦 / Seedance 2.0 prompt 模板
- 更新市场情报快照（每月一次）
- 添加测试用例

---

## 致谢

灵感参考：[zhaihao118/Micro-Drama-Skills](https://github.com/zhaihao118/Micro-Drama-Skills)

本 skill 在其基础上增加了：市场情报扫描、节奏地图、原型库、批判 refine、可移植路径、即梦专项 prompt 模板。

---

## License

MIT — 见 [LICENSE](LICENSE)
