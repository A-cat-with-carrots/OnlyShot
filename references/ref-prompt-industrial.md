# Ref 图工业级 Prompt 工艺（v0.5.0）

来源：SD-002《城市恋综》v2.5 实战 + 行业专家深度审 + 2026 即梦/Midjourney 最佳实践调研。

适用：dreamina text2image 5.0 / Seedance 2.0 / 类似 AIGC 模型的 character ref sheet 生成。

---

## 0. 核心原则（铁律 5 条）

```
1. ref 图 ≠ 成片：ref 图必须 neutral flat lighting（不要戏剧化光）
2. prompt ≠ 一致性：一致性靠 visual reference anchoring（ref 图本身），prompt 只控质量
3. identity block 锁定：身份块独立成段，每次生成逐字复用
4. 视觉指纹放 prompt 开头（前 200 token 权重最高，不是末尾）
5. NOT 词 ≤5 个（堆砌 ≥6 个 NOT，5.0 模型生效率降到 30%）
```

---

## 1. 6 段 identity block 工业模板

```
[IDENTITY] character_id: [城市码 + 序号], fixed character design,
character must remain consistent across all generations,

[BODY] body type: [地标建筑 architecture as creature body],
total height [4 head units], [silhouette 形状],
[标志性结构特征详述],
single cohesive object, NO separation between head and body,

[FACE] facial features painted directly on [塔身/果实身体某个具体位置],
2 large round anime eyes with diamond highlights,
eye color: [配色],
eyelashes long and curled, simple curved smile mouth below eyes,
expression: [城市性格关键词],

[ATTIRE] decorative elements:
[服饰元素] wrapped on [明确身体部位],
NO clothing on tower body, NO human torso underneath,
two small chibi arms emerging from [位置],
arms holding [道具], [配饰] on left wrist,
two tiny [鞋类] at base,

[LAYOUT] 4-grid character reference sheet,
quadrants: top-left front view, top-right 3/4 right view,
bottom-left 3/4 left view, bottom-right back view,
single character per quadrant, identical character in all 4 quadrants,
NO text labels, NO annotations, NO watermarks, NO grid view labels,

[STYLE] soft cell-shaded anime mascot, Funko Pop chibi proportion,
neutral studio lighting flat even, solid pastel [color] background,
glossy plastic shading, bold black outlines,

[NEGATIVE] not human, not humanoid, not realistic, not 3D photoreal,
not multiple characters
```

每段独立行 + 显式标签 → 模型按段处理 → 信息不混。

---

## 2. 视觉指纹铁律

### 错误：戏剧化关键词污染 ref

```
❌ dramatic shoujo manga lighting   → 让 AI 记住"光的方向"而不是"角色外观"
❌ lens flare                      → 镜头光晕掩盖角色细节
❌ glittery rose petals            → 装饰物干扰主体 silhouette
❌ chiaroscuro                     → 阴影被误判为脸部特征
❌ cinematic                       → 引入电影级运镜，破坏 character sheet 用途
```

### 正确：ref 中性 / 视频氛围分层

```
ref 图（character sheet 阶段）：
  ✓ neutral studio lighting flat even
  ✓ solid pastel [color] background
  ✓ no decorative elements
  ✓ single character centered

视频段（multimodal2video 阶段）：
  ✓ 戏剧光 + 玫瑰花瓣 + lens flare（这层加在视频 prompt，不在 ref）
```

**两层分离**：ref 给一致性 anchor，视频给氛围。混在一起 = 一致性崩。

---

## 3. 视觉指纹位置（前 200 token 法则）

```python
# ❌ 错误（当前 SD-002 v2.4）
prompt = f'{role_specific}, {STYLE_FINGERPRINT}'  # FP 在末尾，权重 50% 衰减

# ✅ 正确（v2.5）
prompt = f'{STYLE_FINGERPRINT_HEAD} {role_specific} {LAYOUT_TAIL} {NEGATIVE_TAIL}'
# FP 在开头（最高权重），布局/负面在末尾（结构化）
```

dreamina 5.0 / SD 3.5 / MJ V7 都是前 200 token 权重最高。

---

## 4. 拟物化的真假陷阱（C 方案兑现率）

### 假拟物化（90% 项目踩坑）

```
prompt: "Hangzhou character: 26 year old young woman wearing pagoda headpiece"
result: 少女 + 雷峰塔头饰（≠ 拟物化）
```

模型默认按「人 + 装饰」理解。

### 真拟物化（必须显式约束）

```
prompt: "Hangzhou cityscape mascot, the character IS the Leifeng Pagoda itself,
multi-tier curved-roof pagoda body, NO human face, NO human torso underneath,
2 large eyes painted directly on second tier surface,
tiny chibi arms emerging from sides only,
NOT humanoid character, NOT person"
```

关键短语：
- ✅ `the character IS [object] itself`（不是 wearing it）
- ✅ `NO human face, NO human torso underneath`
- ✅ `eyes painted directly on [object] surface`
- ✅ `chibi arms emerging from sides only`（不是 wearing clothes on torso）
- ✅ `NOT humanoid character`（在 NEGATIVE 段）

---

## 5. 4 视图标签水印陷阱

### 问题

```
prompt: "4-grid character sheet, 4 distinct different angles no duplicate views"
result: AI 自动渲染 FRONT / SIDE / BACK / BACK ANGLE 英文水印（模型理解为教学图）
```

### Fix

```
[LAYOUT] 段必须显式拒绝：
  NO text labels, NO annotations, NO watermarks, NO grid view labels,
  NO ENG text overlay, single composition per quadrant
```

---

## 6. 14 城头饰几何分类（防脸盲，5 派分流）

24 集恋综 14 城同框时，必须保证轮廓 silhouette 一眼可辨：

| 派 | 城市 | 几何形状 |
|----|------|---------|
| **细长尖塔派** | 上海 / 深圳 / 广州（小蛮腰）/ 西安（大雁塔）| 高瘦垂直，单点收顶 |
| **多层堆叠派** | 杭州（雷峰塔）/ 武汉（黄鹤楼）/ 苏州（园林门楼）| 多层屋檐横向叠加 |
| **圆球派** | 北京（天坛）/ 重庆（李子坝穿楼）/ 青岛（栈桥圆台）| 主体球形或正方块 |
| **扁平派** | 成都（宽窄巷子门楼）/ 南京（民国总统府方屋顶）/ 长沙（夜市记招牌）| 横向扁平 |
| **异形派** | 天津（天津之眼圆环）/ 柠檬小弟（圆果实）| 非建筑特殊形状 |

每派 ≤4 城，避免同派同框时混淆。

**Funko Pop 工业逻辑**：盲盒 12 个角色的剪影必须不重样。

---

## 7. ref 4 张 / 9 张 / 12 张策略

| 用途 | 数量 | 用法 |
|------|------|------|
| **基础身份** | 1 张（4-grid） | character sheet 4 视图，ID 锚定 |
| **表情库** | 1 张（4-grid 6 表情） | 怒/惊/悲/笑/狠/憨，给 multimodal2video 表情参考 |
| **关键动作** | N 张（每个动作 1 张） | 招牌动作（拔头饰/激光攻击/砸物） |
| **视频生成时** | 5-8 张（不要塞 9） | image ≤9 但最优 5-8（注意力分散） |

**塞满 9 张反而效果差**——5-7 张让模型聚焦核心元素。

---

## 8. 防侵权 checklist

```
□ 角色名不直接借用现有 IP（雪王/咸鱼酱/蛋仔派对等）
□ 角色形状不组合知名 IP 元素（红斗篷+白圆头+5 元定价 = 蜜雪雪王）
□ 配色避开知名品牌主色 + 形状的组合
□ 反派背景不可识别真人原型（薇娅 2021/罗永浩 2020 等具体案件）
□ 商标词全替换：阿里→橙星→蓝鲸星 / 抖音→短视频 / 茶颜悦色→长沙古茶
□ 公众人物台词不直接引用（《潜伏》余则成 →「这地方深得很」改写式致敬）
□ 政治符号弱化（龙袍→礼袍 / 天安门→故宫琉璃瓦）
```

**红果/抖音审核**：「真实公众人物影射」是一票否决项。

---

## 9. catchphrase 锚定密度规则

```
EP01 前 1 分钟 必须出现 ≥3 个跨集 IP catchphrase（建立观众预期）
EP01 cliffhanger 必须预告 ≥1 个未来集 catchphrase（钩用户留下）
跨集 catchphrase 间隔 ≤4 集（防遗忘）
单集 catchphrase 重复 ≥3 次（建立 motif 强度）
```

SD-002 v2.4 错误：「蒜鸟」EP04 才首发 → 60% EP01 划走用户错过这个核心 IP → EP05 再重复无意义。

---

## 10. ref 灯光对比测试

### Test：同 prompt 不同灯光的影响

```
neutral studio lighting flat even
  → 角色细节清晰，颜色饱和度准确，可作多场景 anchor

dramatic shoujo manga lighting + lens flare
  → 角色面部 50% 在阴影里，AI 误判阴影为颧骨/眉骨
  → 下次 image2video 生成时面部结构变形
```

工业实测：戏剧光 ref 在 image2video 里**前后两 grid 角色不像同一人**的概率达 40%（neutral 光 < 5%）。

---

## 11. 3 选 1 还是 4 选 1（候选数）

| 候选数 | 适用 grid | 成本 | 用途 |
|--------|----------|------|------|
| **1 张** | 过渡 grid | 3 积分 | 占位 |
| **2 张** | 标准对话段 | 6 积分 | 默认 |
| **3 张** | 反转/爽点段 | 9 积分 | 选最佳 |
| **4 张** | 关键爆点（招 1/2/5/6/7） | 12 积分 | 选最佳 + 留备选 |

每集 36 grid 平均 2 候选 = 72 张 × 3 积分 = 216 积分 ≈ ¥15/集

vs 视频成本 11 × 190s = 2090 积分 ≈ ¥150/集 → 分镜图占视频成本 10%，**省视频试错 50%+**

---

## 12. 完整 prompt 示例（上海女主 v2.5）

```
[IDENTITY] character_id: SHA001_shanghai_mascot, fixed character design,
character must remain consistent across all generations,

[BODY] body type: Oriental Pearl Tower architecture as creature body,
total height 4 head units, slender silhouette,
3 signature spheres stacked vertically (top: red glowing sphere with antenna,
middle: silver large sphere, bottom: pink small sphere),
single cohesive object, NO separation between head and body,

[FACE] facial features painted directly on middle silver sphere,
2 large round anime eyes with diamond highlights, eye color: amethyst purple,
eyelashes long and curled, simple curved smile mouth below eyes,
expression: elegant aloof with subtle raised eye glance,

[ATTIRE] decorative elements:
purple silk qipao art deco geometric pattern wrapped on lower pink sphere only,
NO clothing on tower body, NO human torso underneath,
two small chibi arms emerging from middle sphere sides,
arms wear pearl bracelet on left, no other limbs visible from torso,
two tiny silver high heels at base of tower,

[LAYOUT] 4-grid character reference sheet,
quadrants: top-left front view, top-right 3/4 right view,
bottom-left 3/4 left view, bottom-right back view,
single character per quadrant, identical character in all 4 quadrants,
NO text labels, NO annotations, NO watermarks, NO grid view labels,

[STYLE] soft cell-shaded anime mascot, Funko Pop chibi proportion,
neutral studio lighting flat even, solid pastel pink background,
glossy plastic shading, bold black outlines,

[NEGATIVE] not human, not humanoid, not realistic, not 3D photoreal,
not multiple characters
```

---

## 13. v0.5.0 升级到 SKILL.md 的关键改动

```
1. SKILL.md 加 references/ref-prompt-industrial.md 引用
2. 默认参数表加「ref 灯光：neutral flat（视频 dramatic）」分层规则
3. 默认参数表加「ref prompt 6 段结构 identity/body/face/attire/layout/style/negative」
4. 默认参数表加「14 城几何分类 5 派防脸盲」
5. 流程加「拟物化 IS the object 显式约束」
```

---

## 14. 自查清单（每张 ref 跑前必查）

```
□ identity block 在 prompt 顶部（character_id + fixed design）
□ 视觉指纹放 prompt 开头（前 200 token）
□ ref 用 neutral lighting（不 dramatic）
□ NOT 词 ≤5 个
□ 拟物化用 IS the object（不 wearing）
□ 4 视图段含 NO text labels NO annotations
□ 几何形状不跟同派城市撞（避免脸盲）
□ 服饰位置明确（lower sphere only / middle tier only）
□ 角色名/IP 防侵权 checklist 过
□ chibi 比例标准化（4 head units，统一）
```

通过后才提交 dreamina text2image。
