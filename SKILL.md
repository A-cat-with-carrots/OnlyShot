---
name: ai-short-drama
description: 精细化 AI 短剧 IP 创作技能（v0.6.0）。三阶段架构：Phase 1 创作（剧本+ref图，反复迭代）→ Phase 1.5 分镜图（每 grid 1-4 张候选静态图 = 视频首帧，工业级核心层）→ Phase 2 出片（按集解锁，4 模自动选）。v0.6.0 关键升级：① ref 库工艺偏置铁律（现代摩天楼易拟物，古建筑必出 chibi 人体，前期 IP 设计阶段就要避坑）② 即梦 5.0 失败模式 + 敏感词清单（3 类 fail 区分 / prompt 1500 字硬上限 / 反派词替换表 / 暧昧词清单）③ 分镜图 8 段 prompt 模板（CHARACTER/BACKGROUND/ACTION/SCENE/CAMERA/LIGHT/TEXT/STYLE）+ NOT humans 子句必加。沿用 v0.3.0 升级：Phase 1.5 分镜图层、4 模视频、ref 5-8 最优。v0.2.0：bash → Python subprocess、36 grid × 4-10s 变奏、红果必爆 7 招、工业级 ref 库 80-150 张、单 prompt 300-500 字。务必触发：用户提到短剧、微短剧、竖屏剧、AI 短剧、AI 漫剧、剧本创作、分镜、即梦/Seedance 出片、红果/番茄/抖音 IP 改编、爽剧、重生、穿越、赘婿、追妻、神医相师、AI 漫剧奇观、或"帮我做一部短剧"类请求。
---

# AI 短剧精细化 IP 创作 v0.6.0

## v0.6.0 changelog（2026-05-16）

> SD-002《城市恋综》EP01 36 grid × 3 轮（v2.5/v2.6/v2.7）跑 + 全审反推。从「16/36 灾难级一致性破损」修到「0 灾难 / 60% ≥4 分」+ 沉淀 2 个工业级 SOP。

### 关键升级

- ⭐ **`references/storyboard-frame-industrial.md`** v0.3.0：分镜图工艺 SOP
  - 8 段 prompt 模板（CHARACTER/BACKGROUND/ACTION/SCENE/CAMERA/LIGHT/TEXT/STYLE）
  - **NOT humans 子句必加**：每个主角单独 `Xxx body IS [arch] architecture NOT a human wearing X NOT a human with headpiece`
  - **ref 库工艺偏置铁律**：现代摩天楼易拟物 / 古建筑必出 chibi 人体
  - 多角色 SOP：1 主角 ref + N 文字 silhouette + bokeh blur
  - 戏剧光词库（25+ 关键词）+ 红果级首帧 10 条 checklist
  - 11 节完整文档（含 EP01 v2.7 实测验证 grid13/21/22 全 5/5）

- ⭐ **`references/jimeng-failure-modes.md`** v0.1.0（新）：即梦 5.0 失败模式 + 敏感词全清单
  - **3 类 fail 完全区分**：InvalidNode（字数超） / generation failed（审核） / 无 image_url（网络）
  - **prompt 字数硬上限：1500 字符**（实测分布表）
  - **反派词替换表**：sinister/menacingly/dark intent → moody/leaning/quiet
  - **暧昧词清单**：blush/cheeks/extreme close-up → rose tint/medium shot
  - **并发 vs 串行限流**：长 prompt + 并发 = fail，长 prompt 必单跑
  - 4 个 grid 实战诊断 case + 工艺校验 checklist

- ⭐ **scripts/生成分镜图.py** 加 `--no-fingerprint` flag
  - 防 02_IP简报.md 的 ref 风格视觉指纹（neutral / flat / NOT cinematic）污染分镜图 dramatic 光
  - max_workers 8 → 4（降并发防限流）
  - timeout 300 → 420s + 重试 2 次（防长 prompt 超时）

### 最大教训

```
ref 工艺是分镜图工艺的上游。
ref 不纯（chibi 人体），分镜图加 NOT humans 也救不回来。
前期 IP 设计阶段就要避坑：选玻璃塔 / 简单几何，避复杂古建筑。
```

---

## v0.3.0 changelog（2026-05-08）

> SD-001 实战 + 工业级方法论调研沉淀。新增 Phase 1.5 分镜图层 + 4 模视频生成。

### 关键升级

- ⭐ **Phase 1.5 分镜图层**（工业级 5 步流程核心）
  - `scripts/生成分镜图.py`：每 grid 1-4 张候选关键帧（text2image）
  - 分镜图 = 视频首帧（image2video / frames2video 输入）
  - 修改成本 3 积分/张 vs 视频 55 积分/段 = **18 倍便宜**
  - 视频构图 = 静态图（不再随机）
- ⭐ **4 模视频生成**（auto 按文件存在自动选）
  - `image2video`：分镜图首帧 + 动作 prompt（默认主用 80%）
  - `frames2video`：首帧 + 尾帧锁定（关键爆点 10%）
  - `multiframe2video`：2-20 关键帧一镜到底（复杂动作 5%）
  - `multimodal2video`：9 image + 3 video + 3 audio fallback（5%）
- ⭐ **ref 5-8 最优**（不塞 9 → 注意力分散）
- ⭐ **@ 指令显式职责语法**（@图片1 作为角色参考 / @视频1 参考运镜）
- ⭐ **关键 grid 首尾帧**（爆点/反派/心声/卡点必锁）

### 文档新增

- `references/storyboard-frames-craft.md`（分镜图工艺 + 4 模选择）

### 脚本新增 / 改

- `scripts/生成分镜图.py`（新，Step 3）
- `scripts/生成分集视频.py`（改，支持 4 模 auto 选）
- `assets/templates/分镜.json`（新增 video_mode / first_frame_path / last_frame_path / multiframe_paths 字段）

---

## v0.2.0 changelog（2026-05-08）

> SD-001「重生穿越为哮天犬」实战沉淀。13 个失败模式 → 13 个修复 + 工业级标准。

### 关键修复
- ⭐ **scripts/生成分集视频.py**（替代 bash）：subprocess args list 直接调 dreamina，避 bash eval 在中文/特殊字符 prompt 下 quoting 出错（旧 bug 导致 multimodal2video 任务被 server 静默丢弃，list_task 假活 30+ 分钟）
- ⭐ **scripts/ref完备性检查.py**：生视频前强制扫所有 (@xxx_ref.png) 引用，本地缺失就 exit 1
- ⭐ **scripts/派生分集文件.py**：从分镜.json 一键派生即梦批量包.md / 镜头清单.md
- regex 修复：含全角中文 `）` stop 字符（`r'@([^\s),）]+_ref\.png)'`）
- multimodal2video stuck 自动检测：提交后 check `queue_status == 'Generating'`，否则 fallback 到 list_task 找回 submit_id

### 节奏升级
- 36 grid × 4-10s 变奏 替代 60 grid × 3s 死板（multimodal2video 最低 4s，3s 不合法）
- 红果必爆 7 招（详 `references/v21-97-percent-rules.md`）
- 时长分布：4s × 11 + 5s × 14 + 6s × 5 + 7s × 3 + 8-10s × 3 = 36 段 / ~190s

### 素材标准升级
- ref 库目标 **80-150 张**（vs v0.1.x 22 张）
- 单 prompt **300-500 字**（vs v0.1.x 100-200 字）
- ref 分层：① master 风格 ② 角色基础多角度 ③ 角色表情库 ④ 关键动作 ⑤ 场景多角度 ⑥ 道具细节

### 文档
- 新增 `references/troubleshooting.md`（13 失败模式 + 解法）
- 新增 `references/v21-97-percent-rules.md`（7 招 + 24 集校准模板）
- 改 `references/storyboard-craft.md` 为 36 grid 4-10s 变奏
- 改 `references/jimeng-cli-guide.md` 加 v0.2.0 升级 + 网页端可见性

---

## 核心架构：2 Phase

```
┌─ Phase 1：创作（成本低，反复迭代）─────────────────┐
│  阶段 0：市场情报扫描                              │
│  阶段 1：IP 简报（5 子步）                         │
│  阶段 2：故事架构（4 子步）                        │
│  阶段 3：设定圣经（4 子步）                        │
│  阶段 3.5：ref 图自动生成（dreamina CLI）          │
│  阶段 5：批判 refine                              │
└──────────────────────────────────────────────────┘
                      ↓
┌─ Phase 1.5：分镜图（v0.3.0 工业级核心）⭐ 新增 ─────┐
│  ⚠️ 写 prompt 前必读：                            │
│   - storyboard-frame-industrial.md §5（8 段模板）  │
│   - jimeng-failure-modes.md §1+§2（字数+敏感词）   │
│  对每一集独立运行：                               │
│  3A：写该集分镜.json（v0.3.0 字段：video_mode +    │
│       first_frame_path + last_frame_path）         │
│  3B：python scripts/ref完备性检查.py              │
│  3C：python scripts/生成分镜图.py（每 grid 1-4    │
│       张候选关键帧 = 视频首帧）                    │
│  3D：人工选图（grid01_候选3.png → grid01.png）    │
│  3E：关键 grid（爆点/反派/心声）生首尾帧           │
│       （gridXX_首.png + gridXX_尾.png）           │
└──────────────────────────────────────────────────┘
                      ↓
┌─ Phase 2：出片（成本高，按集解锁）────────────────┐
│  4.A：python scripts/生成分集视频.py              │
│       auto 模式按文件存在自动选 4 模：             │
│       - frames2video（首尾帧锁定）                │
│       - image2video（分镜图首帧 + 动作）          │
│       - multiframe2video（2-20 帧一镜到底）       │
│       - multimodal2video（fallback 多 ref）       │
│  4.B：用户在剪映拼接 + 配音 + BGM + 字幕           │
└──────────────────────────────────────────────────┘
```

**为什么这么拆**：

- 剧本 / ref 不满意 → Phase 1 反复改，不烧视频钱
- **分镜图 = 视频首帧** → Phase 1.5 静态图先确认（3 积分/张），不满意改 prompt 重生 → 视频构图固定（不再随机）
- 修改成本：分镜图 3 积分 vs 视频段 55 积分 = **18 倍便宜**，省视频试错 50%+
- 视频出片成本高 → Phase 2 按集解锁，每集都让用户验收
- AI 短剧的真正成本不是创作，是出片。用 Phase 1 + 1.5 把构图打磨到位，Phase 2 才值得花钱

---

## 触发条件

下列任意一个都触发：

- 用户说"做/写/帮我做 ... 短剧"
- 提到红果/番茄/抖音/快手 IP 改编
- 提到即梦/Seedance/可灵/Vidu 出片，并谈到剧本
- 提到分镜、storyboard、shot list、镜头脚本
- 提到爽剧、虐剧、追妻、复仇、重生、穿越、赘婿、奶奶觉醒、神医相师、AI 漫剧奇观

不触发的反例：

- 用户已有完整剧本，只想改某句台词 → 直接改
- 用户问"短剧行业前景如何" → 普通问答
- 用户问"什么是 AI 短剧" → 普通问答

---

## 默认参数（v0.6.0）

| 项 | 默认值 | 来源 |
|----|--------|------|
| 单集时长 | **180-195s** | 红果实测最优（不严卡 180）|
| 集数 | **24 集**（精华）/ 72 集（常规） | 24 集省成本 + 紧凑爆点 |
| 单集分镜数 | **36 grid × 4-10s 变奏** | multimodal2video 最低 4s，变奏防机械感 |
| 时长变奏分布 | 4s×11 + 5s×14 + 6s×5 + 7s×3 + 8-10s×3 | v2.1 红果必爆铁律 |
| 视频比例 | **9:16 竖屏** | 红果/抖音/快手统一 |
| 视频模式 | **multimodal2video（全能参考）** | Seedance 2.0 Fast VIP，多 ref 输入最稳 |
| 字幕 | **开**（中文括号包 + AIGC 标识）| 红果强制 |
| ref 库目标 | **80-150 张**（工业级）| 含动作/表情/场景多角度/道具细节 |
| 单 prompt 字数 | **300-500 字** | 含动作物理 + 表情拆帧 + 灯光 + 字幕规格 |
| 平台 | 红果（默认）+ 抖音（次选）| 月活 3 亿 + 引流 |
| 流派 | 互动选 | 红果纯爽 / 精品悬疑 / 漫剧奇观 / 沙雕轻喜 / 年代爽剧 |
| 付费模式 | 互动选 | 免费（广告）/ 付费（解锁）|
| ref 图生成 | dreamina text2image 4-grid（多角度） | Phase 1 阶段 3.5 |
| 视频出片 | dreamina multimodal2video（含视觉指纹自动 append）| Phase 2 阶段 4.C |
| 跑视频前预检 | **必跑** `python scripts/ref完备性检查.py` | 防 ref 漏 → AI 自由生成 → 一致性破 |

每次启动都要问用户是否调整这些。

**关于 AI 优势**（用户提示，不强推但要点出）：

AI 生视频真正的护城河 = **真人难拍**的奇观（修仙 / 末世 / 西游 / 玄幻 / 异能）。如果用户题材是奶奶觉醒 / 都市追妻这种**真人易拍**的，告诉用户："虽然 AI 也能做，但 AI 真正优势在漫剧奇观流。要不要考虑切换流派？"——给 1 次提示，用户决定。

---

# Phase 1：创作（5 阶段 + 阶段 3.5）

## 阶段 0：市场情报扫描（4 子步）

### 0.1 联网搜当下 Top 5 剧名

```
搜索 1：红果短剧 排行榜 <YYYY-MM>
搜索 2：番茄小说 改编 IP <近 30 天>
搜索 3：抖音短剧 <用户题材关键词> 热度
搜索 4：DataEye 短剧观察 / QuestMobile 月报
搜索 5：短剧 平台 审核 <当前年> 红线
```

### 0.2 真读 1-2 部爆款的业界拆解（核心）

**WebFetch** 1-2 部爆款的剧情解说 / 业界拆解文章。优先源：woshipm / 36 氪 / 腾讯新闻 / 21 经济网。

如果全部 403 → fallback 到内置 `references/red-fruit-data.md`。

### 0.3 给用户 3 选项菜单（不要直接出报告）

让用户挑差异化角度。

### 0.4 写入 `01_市场情报.md`

详见 `references/market-pulse.md`。

---

## 阶段 1：IP 定位（5 子步）

### 1.1 流派选择（关键）

5 选项让用户挑：A 红果纯爽流 / B 精品悬疑流 / C 漫剧奇观流 / D 沙雕轻喜流 / E 年代爽剧流。

**v0.1.2 新增提示**：在选项 C 旁加注：「**真人难拍 = AI 优势**。如果你计划用 AI 出片，C 是最有性价比的选择，因为修仙/末世/玄幻类真人剧组成本极高，AI 直接生」。但不强推，让用户判断。

详见 `references/genre-flavors.md`。

### 1.2 题材原型（1 主 + 1 副）

详见 `references/archetype-catalog.md`。

### 1.3 核心钩子（草拟 3 版让用户挑）

### 1.4 重复爽点公式（草拟 2 版让用户挑）

### 1.5 写入 `02_IP简报.md`

详见 `references/ip-strategy.md`。

---

## 阶段 2：故事架构（4 子步）

### 2.1 三幕结构骨架
### 2.2 关键反转节点（让用户挑）
### 2.3 72 集大纲（先给关键 25 集让用户确认）
### 2.4 写 `03_完整剧本.md` + `04_节奏地图.json`

详见 `references/story-architecture.md`。

---

## 阶段 3：设定圣经（4 子步）

### 3.1 角色清单（≤ 6 人）
### 3.2 5 特写镜头人格锚定
### 3.3 视觉母题 + 反差点 + 服装表 + 即梦 ref prompt
### 3.4 写 3 份圣经

`05_角色圣经.md` + `06_场景圣经.md` + `07_道具圣经.md`

详见 `references/character-design.md`。

---

## 阶段 3.5：ref 图自动生成（v0.1.2 新增，关键）

**这是 Phase 1 的最后一步，也是 Phase 2 的前置依赖**。

### 3.5.1 检测 dreamina CLI

```bash
which dreamina && dreamina --version
```

如果未装 → 引导安装：

```bash
curl -fsSL https://jimeng.jianying.com/cli | bash
```

详细装机指引见 `references/jimeng-cli-guide.md`。

### 3.5.2 检测登录态

```bash
dreamina user_credit
```

如果未登 → 引导：`dreamina login`（浏览器授权）

如果余额不足 → 提示用户充值（不能继续）

### 3.5.3 提取 ref prompt

读 3 份圣经末尾的「即梦角色/场景/道具参考图生成包」段，提取所有 prompt：

- N 个角色 → N 张角色 ref（9:16 半身像）
- M 个场景 → M 张场景四宫格
- K 个道具 → K 张道具三视图

预计 N+M+K 张图，每张 2k 分辨率约 ¥0.5-1，**总成本约 ¥5-15**。

### 3.5.4 批量调用 dreamina text2image

每张图独立提交：

```bash
dreamina text2image \
  --prompt="<从 05_角色圣经.md 提取>" \
  --ratio=9:16 \
  --resolution_type=2k \
  --download_dir="<项目>/ref图/角色/" \
  --poll=60
```

落到项目子目录：

```
SD-XXX_<拼音>/
├── ref图/
│   ├── 角色/
│   │   ├── 周翠英_ref.png
│   │   └── ...
│   ├── 场景/
│   │   └── scene_01_四宫格.png
│   └── 道具/
│       └── prop_01_三视图.png
```

或用项目自带脚本：`scripts/生成参考图.sh`

### 3.5.5 检验 + 用户确认

ref 图生成后**必须让用户看一眼**：

- 角色脸型对吗？
- 服装颜色对吗？
- 场景整体氛围对吗？

不对 → 改 prompt → 重跑（成本低，单图重跑约 ¥1）

OK → 标记 `项目元数据.json` 的 `ref_done = true`，进阶段 5 批判。

---

## 阶段 5：批判 refine（4 子步）

### 5.1 6 维度自评 + 反套路检测 + 平台审核扫描
### 5.2 命中 → 必改 → 在原文件打补丁 → 09_修订记录.md
### 5.3 大改 → 自动归档 `归档/v1.X_<日期>/`

**Phase 1 完成判定**：

- 6 维度总分 ≥ 50/60
- 反套路一级黑名单 0 处命中
- 平台审核全过
- ref 图全部 OK
- 用户确认"可以出片"

详见 `references/critic-checklist.md`。

---

# Phase 2：出片（按集解锁）

**前置条件**：Phase 1 完成 + ref 图齐 + 用户明确说"开始出片"。

每集独立运行 4.A → 4.D。

## 阶段 4.A：选要出片的集

```markdown
Phase 1 已完成 ✅。准备进 Phase 2 按集出片。

成本提醒：每集 60 段视频，约 ¥X-XX（按当前 dreamina 单价计算）。

要先出哪一集？建议顺序：

1. 第 1 集（开篇，最关键，先出测试 ref 图效果是否符合预期）
2. 第 8 集（一卡 / 一爆，付费短剧首付费点）
3. 第 27 集（二卡）
4. 第 50 集（三卡 / 终极反转）
5. 第 72 集（结局）
6. ...

挑 1 集开始。出完该集，确认效果再决定下一集。
```

**默认建议**：先出第 1 集试水，看 ref 图在视频里效果如何。如果不好 → 回阶段 3.5 改 ref → 重出第 1 集。第 1 集 OK 后再批量出后续。

## 阶段 4.B：写该集分镜 + 剧本 + 即梦批量包

如果该集 `分集/第XX集_<集名>/` 还不存在 → 按 `references/scripting-craft.md`（剧本）+ `references/storyboard-frame-industrial.md`（分镜图 8 段 prompt + ref 工艺偏置）+ `references/jimeng-failure-modes.md`（敏感词 / 字数上限 / 并发限流）写：

- `剧本.md`
- `分镜.json`（60 grid）
- `镜头清单.md`
- `即梦批量包.md`（60 段 prompt）

## 阶段 4.C：dreamina image2video 自动出片

读 `分集/第XX集_<集名>/即梦批量包.md` 的 60 段 prompt，**逐段调用** `dreamina image2video`：

```bash
dreamina image2video \
  --image="ref图/角色/周翠英_ref.png" \
  --prompt="<段 N 的 prompt>" \
  --duration=3 \
  --ratio=9:16 \
  --download_dir="分集/第XX集/视频段/" \
  --poll=60
```

每段约 5-15 秒生成（dreamina 服务端排队）。60 段约 30-90 分钟。

或用项目自带脚本：`scripts/生成分集视频.sh <集编号>`

视频段落落到：

```
分集/第01集_<集名>/
├── 剧本.md
├── 分镜.json
├── 镜头清单.md
├── 即梦批量包.md
└── 视频段/
    ├── 段01.mp4
    ├── 段02.mp4
    ├── ...
    └── 段60.mp4
```

## 阶段 4.D：剪映拼接（手动）

skill 不调剪映，但给完整指引：

- 在剪映新建 9:16 / 1080×1920 / 30fps 项目
- 按段 1-60 顺序导入
- 段间过渡：「叠化 0.3s」（爽点段用「白闪 0.2s」）
- 配音：剪映 TTS 或真人
- BGM：按 02_IP简报.md 的关键词在剪映音乐库搜
- 字幕：所有对白上字幕，字号 60，黑边白字
- AIGC 标识（红果 2026 强制）：片头片尾各 5s
- 输出 MP4 H.264 / 1080P

## Phase 2 单集完成判定

- 60 段视频齐
- 用户在剪映看过初剪片
- 用户说"OK 这集可以"
- 标记 `项目元数据.json` 的 `episodes_video_done.append(集号)`

然后进 4.A 选下一集。

---

## ⭐ v0.6.0 视觉一致性 SOP（必读）

> **v0.6.0 update**：原 v0.1.4 8 条 SOP 已被 SD-002 三轮实战推翻 / 拆分到 3 个工业级文档。新手只看这一节 + 3 个 references 即可。

**分镜图 prompt 工艺** → `references/storyboard-frame-industrial.md`
- 8 段模板（CHARACTER/BACKGROUND/ACTION/SCENE/CAMERA/LIGHT/TEXT/STYLE）
- 1 主角 ref + N silhouette 多角色 SOP
- 戏剧光词库 + 红果级首帧 10 条 checklist
- ref 库工艺偏置（现代摩天楼易拟物 / 古建筑必出 chibi 人体）

**ref 图 prompt 工艺** → `references/ref-prompt-industrial.md`
- 6 段 identity block（IDENTITY/BODY/FACE/ATTIRE/LAYOUT/STYLE）
- 视觉指纹放 prompt 开头前 200 token
- 拟物化 IP「IS the object NOT humanoid」必加
- 4 视图标签水印陷阱

**即梦 5.0 故障排查 + 敏感词** → `references/jimeng-failure-modes.md`
- 3 类 fail 区分：InvalidNode / generation failed / 无 image_url
- prompt 字数硬上限：1500 字符（v0.6.0 实测条件下）
- 反派词 / 暧昧词 / 中文敏感词替换表
- 长 prompt 必单跑（不要并发 4+）

**v0.1.4 老 SOP 被推翻的 3 条**（必须知道）：
1. ❌ 老 SOP「scripts 自动 append 视觉指纹」 → v0.6.0 用 `--no-fingerprint` 关闭（ref 风格词会污染分镜图 dramatic 光）
2. ❌ 老 SOP「4 distinct angles」 → 只在 ref 阶段适用，不要写进分镜图 prompt
3. ❌ 老 SOP「改 prompt 后必删旧图重生」 → 仍然成立，但脚本会自动 skip 已存在的；改 prompt 后必须手动删旧文件再跑

详见 `references/visual-consistency-sop.md`（v0.1.4 老文档已大幅瘦身，只保留成本 / 流程部分）。

---

## 项目目录位置规则（v0.1.2）

skill 创建短剧项目时，**项目根目录**按以下顺序确定：

1. **用户明确指定**路径 → 用指定路径
2. **当前 cwd 是短剧工作区**（含 `aiForShortDrama` / `short-drama` / `短剧` 等关键词，或已存在 `SD-XXX_*/` 子目录）→ 直接在 cwd 下创 `SD-XXX_<拼音>/`
3. **当前 cwd 是用户主目录或通用工作区** → 默认建议 `D:\hrdai\aiForShortDrama\SD-XXX_<拼音>/`（用户的标准短剧工作区，本机已建）
4. **都不是** → 询问用户路径，不要自作主张

**默认创作工作区**：`D:\hrdai\aiForShortDrama\`

每次新建短剧项目都落到这个目录下，便于集中管理 + 复用 ref 图 / 角色资产。

---

## 项目文件结构（v0.1.2）

```
D:\hrdai\aiForShortDrama\                       ← 用户标准短剧工作区
├── 即梦 CLI 体验指南.pdf                       ← 用户参考文档
├── README.md                                    ← 工作区 README
│
├── SD-001_<拼音>/                              ← 第 1 部短剧
│   ├── README.md                                ← 项目首页
│   ├── 项目元数据.json
│   │
│   ├── 01_市场情报.md
│   ├── 02_IP简报.md
│   ├── 03_完整剧本.md
│   ├── 04_节奏地图.json
│   ├── 05_角色圣经.md
│   ├── 06_场景圣经.md
│   ├── 07_道具圣经.md
│   │
│   ├── ref图/                                   ← 阶段 3.5
│   │   ├── 角色/
│   │   │   ├── <角色>_ref.png
│   │   │   └── ...
│   │   ├── 场景/scene_01_四宫格.png
│   │   └── 道具/prop_01_三视图.png
│   │
│   ├── 分集/                                    ← Phase 2 按集解锁
│   │   ├── 第01集_<集名>/
│   │   │   ├── 剧本.md
│   │   │   ├── 分镜.json
│   │   │   ├── 镜头清单.md
│   │   │   ├── 即梦批量包.md
│   │   │   └── 视频段/                          ← 阶段 4.C 产出
│   │   │       ├── 段01.mp4
│   │   │       └── ...
│   │   └── 第08集_<集名>/...
│   │
│   ├── 08_自我批判.md
│   ├── 09_修订记录.md
│   │
│   └── 归档/                                    ← 大改前 snapshot
│       └── v1.0_<日期>/
│
├── SD-002_<拼音>/                              ← 第 2 部短剧
│   └── ...
│
└── SD-003_<拼音>/                              ← 第 N 部
```

### `项目元数据.json` 关键字段

```json
{
  "project_id": "SD-001",
  "project_name": "<>",
  "skill_version": "v0.1.2",
  "version": "v1.0",
  "phase": "Phase1_创作 | Phase1_完成 | Phase2_出片 | 完成",
  "stage_progress": {
    "0_市场": "completed",
    "1_IP": "completed",
    "2_故事": "completed",
    "3_设定": "completed",
    "3.5_ref图": "completed",
    "5_批判": "completed",
    "Phase2": "in_progress"
  },
  "ref_done": true,
  "episodes_video_done": [1, 8],
  "next_action": "出第 27 集（二卡）"
}
```

---

## 与用户交互的规矩

1. **每个阶段拆 3-5 子步**，每子步给**选项菜单**让用户挑（A/B/C），不是给完整文档让用户看完
2. **每次开始时主动做市场情报扫描** + WebFetch 真读爆款
3. **如果用户题材落在衰退期 / 红海**，要诚实告诉用户并给替代方向
4. **如果用户没指定流派 / 集数 / 付费**，要问
5. **AI 出片提示**：如果用户题材落在真人易拍范围（奶奶 / 婆媳 / 追妻），给一次"漫剧奇观流是 AI 优势"提示，但不强推
6. **Phase 1 → Phase 2 必须有明确切换确认**：用户说"开始出片"才能进 Phase 2
7. **Phase 2 必须按集解锁**，不能一次出多集
8. **每次大改前自动归档**

---

## dreamina CLI 集成

详见 `references/jimeng-cli-guide.md`。要点：

- 安装：`curl -fsSL https://jimeng.jianying.com/cli | bash`（Mac/Linux/Windows Git Bash）
- 登录：`dreamina login`（浏览器授权）
- 查余额：`dreamina user_credit`
- 文生图：`dreamina text2image --prompt=... --ratio=9:16 --resolution_type=2k --poll=60`
- 图生视频：`dreamina image2video --image=... --prompt=... --duration=3 --poll=60`
- 异步查询：`dreamina query_result --submit_id=<ID>`

skill 通过 Bash 工具直接调 dreamina 命令，不需要 API key 管理。

---

## 启动指令

用户可能这样触发：

- "做一部 ... 短剧"
- "帮我写一个 ... 题材的爽剧"
- "我有个想法：..."
- "改编 ... 这本小说成短剧"

启动后第一句话回应模板：

```
收到。本技能 2 阶段架构：

Phase 1 创作（成本低，反复迭代）
  - 市场情报 + IP 简报 + 故事架构 + 设定圣经 + ref 图自动生成 + 批判
  - dreamina text2image 生 ref 图，成本约 ¥5-15

Phase 2 出片（成本高，按集解锁）
  - dreamina image2video 单集 60 段，按集生成

先 Phase 1，跟你 5 阶段互动确认。3 个最关键问题：

1. 流派：A 红果纯爽 / B 精品悬疑 / C 漫剧奇观（AI 优势）/ D 沙雕轻喜 / E 年代爽剧
2. 集数：默认 70，要改吗？
3. 付费：免费（广告）/ 付费（解锁，第 8 集首付费）

回答后启动阶段 0。
```

---

## 收尾交付

Phase 1 完成时给一份「创作完成清单」：

```
✅ 《XXX》Phase 1 创作完成

📋 IP 信息
- 流派、集数、平台、对标、钩子、爽点公式

📊 创作产出
- 9 个编号文件（市场情报 → 自我批判）
- N 张 ref 图（角色 / 场景 / 道具）
- 72 集大纲 + 节奏地图

🎬 下一步
准备进 Phase 2？告诉我先出哪一集（建议第 1 集试水）。
```

Phase 2 每集完成时给一份「该集出片完成清单」。
