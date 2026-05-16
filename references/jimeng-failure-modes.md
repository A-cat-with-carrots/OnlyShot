# 即梦 5.0 失败模式 + 敏感词全清单（v0.1.0）

> 来源：SD-002《城市恋综》EP01 36 grid v2.5/v2.6/v2.7 三轮跑 + 4 类 fail 实测尸检（2026-05-16）。
>
> 适用：dreamina CLI text2image / image2video / 任何即梦 5.0 调用。

---

## 0. 三类 fail 完全区分（最重要）

即梦 CLI 返回 3 种失败，**根因完全不同，修法完全不同**：

| 错误 | 返回信号 | 根因 | 修法 |
|------|----------|------|------|
| `ret=1046, message=InvalidNode` | `gen_status: fail` + 上面 reason | **prompt 字数超上限** | 压到 ≤ 1400 字符 |
| `generation failed: final generation failed` | `gen_status: fail` + 上面 reason | **内容触发审核**（敏感词/暧昧/反派词） | 改 prompt 去敏感词 |
| 无 image_url 无错误 | stdout 无 url / 超时 | **网络/并发限流** | 单跑串行 + 重试 |

诊断：必查 stderr/stdout 完整内容，**不要看到「无 image_url」就以为是审核**。先匹配 `fail_reason` regex 看具体错误。

---

## 1. prompt 字数硬上限：1500 字符

### 实测分布

| 字数 | 通过率 |
|------|--------|
| < 1300 | **100%** |
| 1300-1500 | ~95% |
| 1500-1600 | ~70% |
| 1600-1700 | ~20% |
| > 1700 | **0%（InvalidNode）** |

### 安全策略

- **理想区间：1200-1400 字符**
- **硬上限：1500 字符**（严守）
- **严禁 > 1600**

### 字数算法陷阱

```python
len(prompt)  # python 实测，唯一可信
```

- ⚠️ 中文 1 字符 = 1 python 字符（不是 1 token = 2-3 字节）
- ⚠️ subagent 手算字数会撒谎（cavecrew-builder 无 Bash exec 时分段手算误差 ±20%）
- ✅ 改完每个 prompt 必须 python 实测，**不接受目测/手算**

---

## 2. 内容审核敏感词清单（generation failed 的根因）

### 2.1 反派/邪恶词（最易触发）

```
❌ sinister             →  ✅ moody
❌ menacingly           →  ✅ leaning forward
❌ dark intent          →  ✅ quiet
❌ possessive           →  ✅ focused
❌ dark cyan            →  ✅ deep cyan
❌ dark teal            →  ✅ deep teal
❌ dark particles       →  ✅ floating motes
❌ dark shadows engulf  →  ✅ shadows along
❌ cold smirk           →  ✅ subtle smirk
❌ harsh shadow         →  ✅ soft shadow（柔化）
❌ dark wood tiers      →  ✅ wood tiers
❌ sinister spotlight   →  ✅ moody spotlight
```

### 2.2 暧昧/亲密词（面部特写易触发）

```
❌ blush on cheeks                    →  ✅ rose tint on surface
❌ pink blush                         →  ✅ pink glow
❌ extreme close-up upper portion     →  ✅ medium shot full body
❌ extreme close-up face filling frame →  ✅ medium close-up
❌ internal warm glow                 →  删
❌ subtle internal glow               →  删
❌ pulsing softly                     →  ✅ glowing steadily
❌ blooms with                        →  ✅ shows
```

**关键洞察**：`extreme close-up` + `面部细节描述`（blush/cheeks/lips/eyes 等）= 即梦面部审核拦截。

### 2.3 中文敏感词（subtitle/弹幕段）

```
❌ 「反派」              →  删 / 改「这个角色」
❌ 「磕」                →  删 / 改「围观」
❌ 「不死心」            →  改「还在惦记」
❌ 「曾经是我的」        → 保留但 prompt 其他敏感词去清
❌ 致敬经典台词（如「这天津，深得很」） → 改「这天津，水太深」
```

### 2.4 街拍/真人拟人词

```
❌ strolls past camera   →  ✅ walks across stage center
❌ snack string          →  ✅ food snack
❌ duck-neck snack       →  ✅ snack（去具体食物名）
```

---

## 3. 并发 vs 单跑限流

### 实测结果

| 模式 | prompt 字数 | 通过率 |
|------|-------------|--------|
| 8 并发 | 短（~300 字） | 100% |
| 8 并发 | 长（~1100 字） | 50% |
| 8 并发 | 长（~1500 字） | **0%** |
| 4 并发 | 长（~1500 字） | ~50% |
| 串行 | 长（~1300 字） | 100% |

### 推荐策略

```python
# scripts/生成分镜图.py 配置：
max_workers = 4          # 并发上限
timeout = 420            # 单次 timeout（秒）
poll = 300               # dreamina --poll
retries = 2              # 失败重试次数
```

**长 prompt (> 1200 字) + 高并发 = 必死**。要么压 prompt 短，要么降并发到 1（串行）。

---

## 4. ref 引用层失败

### 4.1 多 ref 同框 = 一致性必崩

| ref 数 | 一致性预期 | 表现 |
|--------|------------|------|
| 1 主角 | 95% | 完美保 ref |
| 2 主角（CP） | 80% | 接受 |
| 3+ 主角 | < 50% | 全员脸盲化 |
| 6+ 主角 | 0% | 全部变 chibi 通用形 |

**SOP**：1 主角 ref + N 文字 silhouette + bokeh blur 模糊。详见 `storyboard-frame-industrial.md` §3。

### 4.2 prompt 重描 ref 已有的身体 = 污染 ref

```
❌ [BODY] (@xxx_ref.png) 3 spheres red top + silver mid + pink bottom, two eyes...
✅ [CHARACTER] (@xxx_ref.png) — same identity, foreground left.
```

ref 引用是图像 token 70% 权重 vs 文字描述 30% 权重，**冲突**而不是叠加。文字重描身体 → 模型按文字重画 → ref 降级为「风格参考」→ 角色完全变形。

### 4.3 ref 库本身偏置 = 分镜图层无解

实测：
- ✅ 现代摩天楼 ref（东方明珠 / 平安金融）→ 分镜图 5/5 纯拟物
- ⚠️ 古建筑 ref（雷峰塔 / 故宫 / 黄鹤楼 / 小蛮腰）→ 分镜图 3/5「chibi 人+塔顶头饰」

**根因**：即梦 5.0 训练数据对**典型现代摩天楼**学习充分（玻璃塔结构清晰）→ 能拟物；对**带檐角/复杂结构/塔/宫殿**学习偏「人物穿戴」→ 难拟物。

**这是 ref 层问题，分镜图层加 STYLE 段 `NOT humans` 子句也无法完全修复**。修复路径：
1. 在 ref 阶段就跑出纯拟物化 ref（v2.5 上海/深圳 工艺）
2. 换模型（Midjourney v6 / Seedance / Flux）
3. 手画 / 3D 建模渲染 ref
4. 接受现状（chibi 人也有萌点）

---

## 5. 视觉指纹陷阱（脚本默认 append 的污染）

`scripts/生成分镜图.py` 默认 append `02_IP简报.md` 的视觉指纹到每个 prompt 末尾。如果视觉指纹含 ref 风格词：

```
❌ neutral studio lighting flat even
❌ solid pastel background
❌ NOT realistic photography, NOT cinematic, NOT 3D rendered photoreal
```

这些会**中和分镜图需要的 dramatic 光 + 复杂背景 + cinematic 感**。

修复：
- 跑分镜图加 `--no-fingerprint` flag（v0.3.1 加）
- 或：02_IP简报.md 加「分镜图视觉指纹」段（dramatic 版）
- 或：把 ref 风格词移到 `references/ref-prompt-industrial.md` 由 ref 跑时单独 append

---

## 6. 4 个 grid 实战诊断 case（参考）

### case A：grid14 上海心动（5 次 fail → 1 次 pass）

| 版本 | prompt | 结果 |
|------|--------|------|
| v1 | `extreme close-up upper portion` + `pulsing softly` + `pink blush on cheeks` + `internal glow` | generation failed × 3 |
| v2 | 同上去 `internal glow` | generation failed × 3 |
| v3 | 改 `medium shot full body` + 删 `blush on cheeks` + 删 `internal glow` + 删 `extreme close-up` | ✓ pass |

**教训**：面部 close-up + 任何「面部红晕」描述 = 必触发审核。

### case B：grid25 杭州独白钩子（3 次 fail → 1 次 pass）

| 版本 | prompt | 结果 |
|------|--------|------|
| v1 | `sinister` + `dark intent` + `possessive` + 中文「反派戏多」 | generation failed × 3 |
| v2 | 全改：`moody` + `quiet` + `focused` + 「杭州还在惦记」 | ✓ pass |

**教训**：反派戏，prompt 用「氛围词」（moody/cold/quiet）不用「反派词」（sinister/menacingly/dark intent）。中文「反派」二字直接删。

### case C：grid27 武汉再蒜鸟（3 次 fail → 1 次 pass）

| 版本 | prompt | 结果 |
|------|--------|------|
| v1 | `Wuhan strolls past camera` + `snack string` | generation failed × 3 |
| v2 | `walks across stage center` + `mouth opens speaking with smile` | ✓ pass |

**教训**：`strolls past camera` 可能被理解为「街拍」触发肖像权类审核。改成 `walks across stage center` 通过。

### case D：grid33 杭州冷笑（3 次 fail → 1 次 pass）

同 case B（反派词全替换）+ 加 `wood tiers tilt`（不要 `lean menacingly`）。

---

## 7. 工艺校验 checklist（跑前必查）

```
□ 1. python 实测 prompt 字数 ≤ 1500（理想 1200-1400）
□ 2. 单 grid 最多 2 ref（CP 镜上限），3+ ref 改 silhouette
□ 3. CHARACTER 段后只写 ACTION/SCENE/CAMERA/LIGHT，禁止重描身体
□ 4. STYLE 段每个主角单独 NOT humans 子句
□ 5. 反派词全替换（sinister/menacingly/dark intent/possessive → moody/leaning/quiet/focused）
□ 6. 暧昧词全清（blush/cheeks/extreme close-up upper portion → rose tint/medium shot）
□ 7. 中文敏感词全清（反派/磕/不死心 → 删/改）
□ 8. 跑长 prompt（> 1200 字）用串行模式（max_workers=1）
□ 9. 加 2 次重试（即梦偶发限流）
□ 10. fail 时先 regex 匹配 fail_reason 区分 InvalidNode/generation failed/超时
```

---

## 8. 一句话总结

```
即梦 5.0 = 严格审核 + 1500 字硬上限 + 多 ref 必崩 + 古建筑拟物难

跑前：实测字数 + 1 主 ref + 拟物动作 + 替反派词
跑时：串行长 prompt + 4 并发短 prompt
跑后：fail 必看 fail_reason 区分根因
```
