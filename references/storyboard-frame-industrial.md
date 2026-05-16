# 分镜图工业级 Prompt 工艺（v0.2.0）

> 本文件回答一个核心问题：**ref 图、分镜图、视频段三层不同工艺，哪些参数必须分离、哪些不能复用？**
>
> 来源：SD-002《城市恋综》EP01 36 grid 全审反推（2026-05-16）+ grid13/21/22 v0.2.0 实测验证（3/3 一致性 5/5 + 场景 5/5）。
>
> 适用：dreamina 5.0 image2image / Seedance 关键首帧 / 任何「拟物化 IP 角色 × 红果级首帧」场景。

---

## v0.2.0 实测铁律（必读，3 条命）

跑过 grid13/21/22 三种场景类型实测，验证 SOP 后又踩了 3 个新坑，新增 3 条铁律：

### 铁律 1：即梦 5.0 prompt 上限 **1500 字符**（中英混合）
- 1294 字 ✅ 通过
- 1467 字 ✅ 通过
- 1507 字 ✅ 通过
- 1656 字 ❌ fail `ret=1046 InvalidNode`
- 1677 字 ❌ fail `ret=1046 InvalidNode`
- 1995 字 ❌ fail
- **结论**：严守 **< 1500 字**，理想 1200-1400 字。

### 铁律 2：STYLE 段必含 `NOT a human wearing X clothing NOT a human with X headpiece` 防人形先验
- grid21 v1（无此子句）→ CP 变「人头戴塔头盔」（一致性 1.5/5）
- grid21 v2（加 NOT humans 子句）→ 真拟物化（一致性 5/5）
- **结论**：每个 ref 主角必须**单独**写 NOT 子句（不能写 "characters bodies ARE X and Y NOT humans" 复数共用，模型不认）

### 铁律 3：每个 grid 单跑 100% 通过率，4+ 张并发 90% fail
- v2.6 36 张并发（每张 ~325 字）→ 100% 通过（短 prompt）
- v2.7 4 张并发（每张 ~1700 字）→ 0% 通过（长 prompt 触发限流）
- v2.7 单跑（1500 字）→ 100% 通过
- **结论**：长 prompt + 并发不可兼得。批量跑用 `--candidates=1` + max_workers=4 + 重试 2 次。

---

## v0.2.0 新增：分镜图 prompt 防变人 8 段定式（覆盖原 §5 模板）

```
[CHARACTER] (@xxx_ref.png) — same identity, [位置].
  ↑ 短化「same character identity」→「same identity」省 9 字符

[BACKGROUND] soft bokeh: 1 [silhouette描述] (城市), N chibi silhouettes blurred.
  ↑ silhouette 用列表，单行写，去 "in deep bokeh background all out-of-focus"

[ACTION] [拟物动作动词] + [塔/球/楼某部位变化] + [道具状态].
  ↑ 注意：禁用 "stands center / hand-in-hand / raises chibi arm" 等人形动作
  ↑ 改用 "tower leans / sphere glows / antenna pulses"

[SCENE] [场所] [前景道具], [中景元素], [背景地标], shallow DoF.

[CAMERA] [景别], [角度], [焦段 mm].
  ↑ 去 "golden ratio composition" "negative space" 等抽象词

[LIGHT] dramatic [主光] from [方向], [边缘光], [体积光], [粒子].

[TEXT] subtitle [位置] Chinese: 「[内容]」. 
  ↑ 弹幕只写 1 处 + ONE bullet chat 单数

[STYLE] soft cell-shaded anime mascot Funko Pop chibi 4 head units glossy plastic bold outlines cinematic 9:16, [主角A] body IS the [arch] architecture itself NOT a human wearing [thing] clothing NOT a human with headpiece, [主角B] body IS the [arch] architecture itself NOT a human, background figures pure silhouettes only.
  ↑ 关键：每个主角单独 NOT humans 子句
```

### v0.2.0 完整示例：grid13 验证版（1285 字通过，一致性 5/5）

```
[CHARACTER] (@深圳_ref.png) — same identity, foreground left. (@上海_ref.png) — same identity, foreground right, facing Shenzhen.
[BACKGROUND] soft bokeh: 1 dark teal pagoda silhouette far back left (Hangzhou shock), 2 chibi mascot silhouettes blurred far back, warm gold party bokeh circles.
[ACTION] Shenzhen tower leans forward, antenna spire pulses electric blue, mouth open speaking. Shanghai's red sphere top glows from grey to bright pink, soft blush on middle sphere face, wide surprised eyes.
[SCENE] grand reception ballroom, crystal chandelier overhead foreground, polished marble floor reflecting pink-gold, tall windows mid-ground showing city night skyline.
[CAMERA] medium two-shot, eye-level 3/4 angle, 35mm.
[LIGHT] dramatic warm pink key from upper-right, electric blue rim behind Shenzhen, gold rim on Shanghai, sparkle bokeh, romantic volumetric haze.
[TEXT] subtitle bottom Chinese 「这事儿跟你现在没关系」blue + English 「Bro」white sans-serif glow.
[STYLE] soft cell-shaded anime mascot Funko Pop chibi 4 head units glossy plastic bold outlines cinematic 9:16, Shenzhen body IS Ping An Finance Center architecture NOT a human wearing tower clothing NOT human with headpiece, Shanghai body IS Oriental Pearl Tower architecture NOT a human, background figures pure silhouettes only.
```

---

---

## 0. 三层工艺分离铁律（v0.1.0 最大教训）

```
ref 图    →  「角色身份证」  → neutral / flat / 单角色 / 4 视图 / 信息密度 0
分镜图    →  「视频首帧」    → dramatic / 多层景深 / 戏剧构图 / 信息密度满 / 候选 2-4 张
视频段    →  「动作连贯」    → 在分镜图首帧基础上加 motion + camera move
```

**最大错误**：把 ref 工艺照搬到分镜图。结果 36 grid 全部「平、淡、正面、无戏剧光」，
更糟的是因为重描身体 + 多 ref 引用 → 角色形态完全偏离 ref（如 grid11/13/16/17/20/27 等
直接变成「人类小孩」「ET 抽象 mascot」「鹿角娃娃」「猫娘群」）。

---

## 1. 三层工艺差异表（核心）

| 维度 | ref 图（character sheet） | 分镜图（视频首帧） | 视频段（4-10s） |
|------|---------------------------|---------------------|-----------------|
| **光影** | neutral studio flat even | dramatic key+rim+fill / 玫瑰金顶光 / 体积光 | 沿用分镜图首帧光，加动态光斑/粒子 |
| **构图** | 居中 4 视图 | 三分律 / 黄金比例 / dutch angle / 引导线 | 沿用分镜图首帧构图 + camera move |
| **角色描述** | 完整 6 段 identity block | **只写 ACTION，禁止重描 BODY/FACE/ATTIRE** | 同分镜图，加 motion verb |
| **场景细节** | solid pastel 背景 / 0 道具 | 3 层景深（前景道具 / 中景角色 / 背景地标）/ 5+ 道具 | 沿用 + 粒子动态 |
| **ref 引用方式** | 不引用（这就是 ref 本身） | **1 主角 ref（@xxx_ref.png）+ N 文字 silhouette** | 用上一步选定的分镜图作 image2video 输入 |
| **多角色** | 单角色 4 视图 | 1 主角 ref + 配角文字描述 silhouette/blur | 同分镜图 |
| **画幅** | 1:1 方图（4-grid） | 9:16 竖屏 1080x1920 | 9:16 竖屏 |
| **NOT 词数** | ≤5 个 | ≤5 个（不要堆 NOT humanoid 之类的，因为这一步就是要正确呈现 mascot 体型） | ≤3 个 |
| **候选数** | 1（每角色 1 张定型） | 关键爆点 4 张 / 标准 2 张 / 过渡 1 张 | 关键 3 段 / 标准 1 段 |

---

## 2. 致命陷阱：prompt 重描身体 = 污染 ref（最大杀手）

### 错误样例（SD-002 EP01 当前做法，导致 60% 一致性崩）

```
[BODY] (@上海_ref.png) Shanghai Oriental Pearl Tower mascot,
3 stacked spheres (red top, silver middle, pink bottom), purple silk qipao
on lower sphere, two amethyst eyes, Funko Pop chibi.
```

**问题分解**：
1. `(@上海_ref.png)` 是图像锚点（视觉权重 ≈70%）
2. 紧跟 `3 stacked spheres ... purple silk qipao ... two amethyst eyes` 是**重生成指令**（文本权重 ≈30%）
3. 即梦/Seedance 把两者**叠加渲染**：因为文本 prompt 描述的体型「不完整 / 顺序变了 / 颜色描述简化了」
   → 模型会**按文本重新生成一个新的体型**，再用 ref 图「修色」
   → 结果出来的是一个**像 ref 但不是 ref** 的新角色
4. 这就是 grid11（上海变正常人）/ grid13（变果冻 ET）/ grid14（只剩半张脸 + 红球）
   / grid16（变鹿角女孩）/ grid20（变 blob）的根因

### 正确做法（v2.7）

```
[CHARACTER] (@上海_ref.png) — same character identity, full body in frame.
[ACTION] Shanghai mascot walks elegantly down red carpet, raises left chibi arm waving,
top red sphere on head sparkles with internal light pulse, hem of purple qipao flutters back.
[SCENE] hotel lobby with art deco gold-trim columns, deep red carpet leading to camera,
crystal chandelier above out-of-focus foreground, marble floor reflecting warm pink-gold,
two background mascot silhouettes at edges blurred bokeh, shallow depth of field f/2.0.
[CAMERA] medium shot, eye level, 35mm equivalent, slight low-angle for hero impact.
[LIGHT] dramatic key light from upper-left warm gold, soft pink rim light from behind,
volumetric haze in background catching chandelier glow.
[TEXT] subtitle bottom Chinese: 「侬好，阿拉来了」
```

**关键差异**：
- `(@上海_ref.png) — same character identity`：图像 ref 是身份**唯一**来源，文字不重描
- 文字只写 ACTION + SCENE + CAMERA + LIGHT + TEXT
- 任何与 ref 重复的 BODY/FACE/ATTIRE 描述全删，只保留**新动作**和**新场景信息**

### 一句话铁律

> **「ref 引用 = 身份冻结，prompt 文字 = 行为变量」**
> 凡是文字里描述身体/脸/服饰，等于告诉模型「按文字重画」。

---

## 3. 多角色同框 SOP（grid 同框 ≥2 主角时）

### 错误样例（grid10/11/16/20/21/22/31）

```
[BODY] ensemble shot: (@上海_ref.png) Shanghai pearl tower stage left,
(@深圳_ref.png) Shenzhen sky tower stage right, (@柠檬小弟_ref.png) Lemon Buddy
small front center, with 3 other mascots in background blurred silhouette.
```

**问题**：3-5 个 ref 同时引用 → 即梦只能保 1-2 个核心 ref 一致 → 其他变形/融合/错位。
- grid20: 上海+深圳同框，结果上海变蓝色幽灵鸟 + 深圳变绿色月牙 blob
- grid21: 7 个角色同框，全部变成圆头大眼一样脸的 chibi 群体（脸盲）
- grid31: 7 个角色同框，全部变成日漫猫娘+熊猫，无 1 个 mascot 形态

### 正确 SOP（1 主角 ref + N 文字 silhouette）

**Step 1：选定本 grid 的「视觉主角」**（情感焦点 / 推进剧情的人）

**Step 2：主角用 ref 引用（1 张，最多 2 张当 CP 镜头）**

```
[HERO] (@上海_ref.png) — same character identity, foreground left, hero focus.
```

**Step 3：配角全部用文字 silhouette + 模糊处理（绝不引用 ref）**

```
[BACKGROUND] in soft bokeh background:
  - one tall thin glowing-blue tower-shaped silhouette (Shenzhen) at right edge,
  - one wider red-and-gold pagoda silhouette (Beijing) at center back,
  - 2 generic chibi mascot silhouettes blurred far back.
All background figures out-of-focus f/1.8 shallow DoF, dark teal tint, low contrast.
```

**Step 4：必要的话，关键配角的 ref 引用「插帧合成」（后期用 PS/即梦局部重绘）**

不要试图让 1 张分镜图同时呈现 5 个标准 mascot 形态。

### 同框上限

| 主角 ref 数 | 适用场景 | 一致性预期 |
|--------------|----------|------------|
| 1 | 单人特写 / 单人镜头 | 95% |
| 2 | CP 对话 / 对峙 | 80%（接受） |
| 3+ | **禁用**，改用「主 1 + silhouette N」 | <50% |

---

## 4. 戏剧光影词库（分镜图必备，ref 禁用）

### 4.1 主光（key light）

```
✅ dramatic golden hour key light from upper-left at 45-degree angle
✅ warm tungsten 3200K key light spotlight from above
✅ cold neon blue key light from window (cyberpunk)
✅ harsh top-down spotlight (interrogation / dramatic moment)
```

### 4.2 边缘光（rim light，区分主体与背景的关键）

```
✅ pink rim light from behind (romantic)
✅ teal rim light from upper-right (sinister / villain)
✅ warm gold rim light separating subject from dark background
✅ blue electric rim halo (tech mascot 深圳)
```

### 4.3 体积光 / 大气光（volumetric / atmosphere）

```
✅ volumetric god rays through window
✅ floating dust particles catching light (close-up shot atmosphere)
✅ misty bokeh background with depth haze
✅ moody underlit fog (反派 grid18/25 必加)
✅ sparkle particle bokeh (心动镜 grid14/32)
```

### 4.4 角度（dutch angle / hero shot / pov）

```
✅ dutch angle 15-degree tilt (混乱 / 反派 / 紧张)
✅ low-angle hero shot looking up (北京宣布 grid01/19/22)
✅ high-angle bird view (全场反应 grid21/31)
✅ over-the-shoulder shot (CP 镜 grid20/32)
✅ extreme close-up macro lens (大特写 grid08/14/18/23/25)
```

### 4.5 景深 / 镜头

```
✅ shallow depth of field f/2.0 (主角清晰，背景柔焦)
✅ wide-angle 24mm with foreground objects (前景道具入画)
✅ telephoto compression 85mm (压缩感 + 浅景深)
✅ macro extreme close-up (柠檬水滴落 / 蓝鲸 logo 特写)
```

### 4.6 配色情绪映射

| 情绪 | 配色方案 | 适用 grid |
|------|----------|-----------|
| 皇家威严 | warm gold + deep red + ivory | 北京 grid01/19/22 |
| 海派精致 | warm pink + champagne gold | 上海 grid02/14/15 |
| 反派阴谋 | cold cyan + dark teal + blacks | 杭州 grid17/18/23/25/26/33 |
| 心动 CP | warm pink + soft gold + sparkle | grid13/14/16/20/32 |
| 卷王科技 | electric blue + silver + cool white | 深圳 grid12/24 |
| 江湖暖意 | warm sunset orange + cherry pink | 武汉 grid06/27 |
| 沉默见证 | soft warm spotlight + cool fill | 柠檬小弟 grid07/08/09/10/28/34 |

---

## 5. 分镜图 prompt 8 段模板（取代 ref 6 段）

```
[CHARACTER] (@主角_ref.png) — same character identity, [位置 / 焦点].
  ↑ 注意：ref 后面只能写 same character identity + 位置，禁止重描身体。

[BACKGROUND] in soft bokeh background:
  - [配角1 silhouette 颜色 + 形状] at [位置],
  - [配角2 silhouette 颜色 + 形状] at [位置],
  - [N 个 generic chibi silhouettes] far back blurred.

[ACTION] [主角动作动词] + [手 / 头 / 身体某部位的具体动作] + [道具/物体的状态变化].
  ↑ 不写 "is doing"，写 "verbs in present tense"，模型理解动作更直接。

[SCENE] [场所] with [前景道具1] [中景元素2] [背景地标3],
  shallow depth of field f/2.0, [天气/环境氛围词].

[CAMERA] [景别] shot, [角度], [焦段 mm], [运镜方式静态描述].
  ↑ 即梦不真的会运镜，但描述运镜会触发对应构图（如 push in → 中心构图）。

[LIGHT] [主光] from [方向] [色温] + [边缘光] from [方向] [色] + [体积光/大气].

[TEXT] subtitle [位置] [语言]: 「[完整中文/中英混排]」 + [bullet chat 弹幕] [颜色] [位置]: 「[弹幕内容]」.

[STYLE] soft cell-shaded anime mascot Funko Pop chibi proportion 4 head units,
  glossy plastic shading, bold black outlines, cinematic 9:16 aspect ratio,
  vertical composition for short drama platform.
  ↑ 这一段对每张分镜图都一样，固定 append。
```

### 5.1 完整示例：grid01 v2.7 改写

**v2.5 原版（错）**：
```
[BODY] (@北京_ref.png) Forbidden City palace mascot, red wall body with golden roof,
two gold eyes, goatee line, Funko Pop chibi 4 head units. [SCENE] grand reception hall
center, panoramic slow push in, slight upward angle. [ACTION] character raises tiny chibi
arm holding gold scroll, red ceremonial robe flutters, mouth opens announcing.
[LIGHT] warm golden lighting. [TEXT] subtitle bottom showing Chinese text reading:
「您内瞧瞧朕这阵仗，24城恋综开播！」
```

**v2.7 改写（对）**：
```
[CHARACTER] (@北京_ref.png) — same character identity, center of frame, hero focus.

[BACKGROUND] grand Forbidden City throne hall stretching back:
  - massive red lacquered columns in foreground left and right (out of focus),
  - golden tiled ceiling dragons fading into background haze,
  - 2 silver chibi mascot silhouettes flanking far background (small + blurred).

[ACTION] character raises right chibi arm holding glowing gold scroll up high,
mouth opens wide announcing, red ceremonial robe billows backward as if wind-blown,
gold star eyes pulse with internal light, gold seal in left hand glints.

[SCENE] vast imperial throne hall with red lacquered pillars foreground, marble floor
reflecting warm gold, hanging red lanterns mid-ground, golden dragon ceiling above
fading into atmospheric haze, shallow DoF f/2.8.

[CAMERA] hero low-angle medium shot looking up 20-degrees, 35mm equivalent,
character occupies central 60% of frame, slight wide-angle perspective for grandeur.

[LIGHT] dramatic warm gold key light from upper-left at 60-degrees,
soft red rim light from behind separating from columns,
volumetric god rays streaming through ceiling beams,
floating golden dust particles catching the light.

[TEXT] subtitle bottom Chinese: 「您内瞧瞧朕这阵仗，24城恋综开播！」
+ small bullet chat top-right red: 「24城开播了！」.

[STYLE] soft cell-shaded anime mascot Funko Pop chibi 4 head units,
glossy plastic shading, bold black outlines, cinematic 9:16 vertical short drama frame.
```

**改了 5 件事**：
1. 删除 `red wall body with golden roof, two gold eyes, goatee line` 重描身体
2. 加 8 段标签结构 + 显式景深 / 镜头焦段
3. 加 dramatic key+rim+volumetric 三层光
4. 加 3 层景深 SCENE（前景柱 / 中景灯 / 背景龙）
5. 加 hero low-angle + 60% 占幅 + 黄金构图

---

## 6. 红果级首帧 10 条 checklist

每张分镜图跑前必查：

```
□ 1. 主角占幅 ≥40%（避免太小看不清）
□ 2. 至少 2 层景深（前景虚 / 中景主角 / 背景虚）
□ 3. 戏剧光（key + rim + 体积光，三选二必加）
□ 4. 主角面部能看清（特写镜头脸不被遮）
□ 5. 主角与背景明度对比 ≥3 档（避免融背）
□ 6. 关键道具入画（柠檬水/蓝鲸 logo/红礼袍/激光珠）
□ 7. 字幕位置不挡脸（底部 1/8 安全区）
□ 8. 配色服务情绪（暖=甜/冷=阴/金=爽）
□ 9. 镜头角度服务剧情（低=英雄/高=失败/平=日常/dutch=混乱）
□ 10. 一帧能讲清「谁 + 在做什么 + 什么后果即将发生」（信息密度）
```

---

## 7. 分镜图 vs ref 图错误清单（不能犯的 10 条）

```
1. ❌ 用 neutral lighting flat even（这是 ref 词，分镜图必崩）
2. ❌ 用 solid pastel background（红果首帧需要复杂背景）
3. ❌ 用 4-grid character sheet（分镜图是单图 9:16）
4. ❌ 用 NOT human, NOT humanoid（这只在 ref 防 mascot 变人）
5. ❌ 在 prompt 里重描 ref 已有的 BODY/FACE/ATTIRE
6. ❌ 同时 @ 引用 3 个以上 ref
7. ❌ 期望 1 张图把 5 个角色都画对
8. ❌ camera 段写 "panoramic slow push in"（这是视频段词，分镜图是静态）
9. ❌ 用 "single character per quadrant"（分镜图不是 grid）
10. ❌ 不写景深、不写构图角度、不写镜头焦段
```

---

## 8. 分镜图候选数策略

| 类型 | 候选数 | 选图标准 |
|------|--------|----------|
| 关键爆点（招1/2/3/5/6/7） | 4 张 | 选戏剧最强 + 信息密度最大 |
| CP 镜 / 反派关键独白 | 3 张 | 选情绪传达最准 |
| 标准对话段 | 2 张 | 选 ref 一致性最高 |
| 过渡段 / UI 全屏 | 1 张 | 占位即可 |

EP01 36 grid 推荐分布：
- 4 张候选：grid01 / 03 / 06 / 13 / 18 / 22 / 25 / 30 = 8 grid × 4 = 32 张
- 3 张候选：grid04 / 05 / 14 / 16 / 17 / 20 / 23 / 33 / 35 = 9 grid × 3 = 27 张
- 2 张候选：其余 17 grid × 2 = 34 张
- 1 张候选：grid29 / 36（全 UI 屏）= 2 grid × 1 = 2 张
- 总数：95 张 ≈ 285 积分 ≈ ¥20/集

---

## 9. ref 引用顺序最佳实践

即梦/Seedance 对多 ref 的处理：**第 1 张权重 70% / 第 2 张 20% / 第 3+ 张 10%**

```
✅ 关键 grid：把视觉主角放第 1 个 ref 引用位
✅ CP 镜：女主放第 1 / 男主放第 2
✅ 反派镜：反派放第 1（最强一致性）
❌ 不要按"剧情先后"排序 ref，要按"视觉重要性"排序
```

---

## 10. v0.1.0 最终铁律（一句话总结）

```
ref 图：身份证（neutral / 单角色 / 4 视图 / 0 戏剧）
分镜图：海报（dramatic / 主角 ref + silhouette 配角 / 8 段结构 / 3 层景深）
视频段：短片（image2video，分镜图作首帧）

最大错误：把 ref 工艺照搬分镜图。
最大救命：(@xxx_ref.png) 后面只写 ACTION/SCENE/CAMERA/LIGHT，
          禁止重描 BODY/FACE/ATTIRE。
```

---

## 11. v0.3.0 新增：ref 库工艺偏置 - 分镜图层无解的硬伤

实测 SD-002 EP01 24 grid v2.7 跑完后的最大教训：**分镜图 SOP 修不掉 ref 层的本质偏置**。

### 11.1 即梦 5.0 拟物化能力按建筑类型分裂 2 派

| 建筑类型 | 例子 | 拟物化预期 | 分镜图效果 |
|----------|------|-----------|------------|
| 现代摩天楼（玻璃塔） | 东方明珠 / 平安金融 / 帝国大厦 | ✅ 易（5/5） | 真正塔身长脸，无人体 |
| 复杂古建筑（檐角/塔/宫殿） | 雷峰塔 / 故宫 / 黄鹤楼 / 小蛮腰 | ⚠️ 难（3/5） | chibi 人体 + 塔顶头饰 |

### 11.2 根因诊断

- **训练数据偏置**：即梦 5.0 训练数据中，「现代摩天楼」结构清晰且经常被「拟人化」（如 Pixar / 国创动画），所以模型学会「塔本身长脸」
- 「古建筑」（带檐角/复杂榫卯）经常出现在「人物穿戴」语境中（cosplay / 国漫角色），所以模型学会「人物穿戴塔形装饰」
- **分镜图 prompt 加 `NOT humans wearing X` 只能减弱，无法消除偏置**（实测加了 NOT 子句的 jingdesh/wuhan/hangzhou/guangzhou grid 仍 30-50% 出现 chibi 人体）

### 11.3 4 个修复路径（按工程复杂度排）

| # | 方案 | 工程量 | 一致性预期 | 适用 |
|---|------|--------|-----------|------|
| 1 | 接受现状（chibi 人体也是萌点） | 0 | 3/5 | 古建筑类 IP 兜底 |
| 2 | 重做 ref（多候选 + 选纯拟物的） | 中（¥30-50） | 4/5 | ref 阶段就强约束 |
| 3 | 换模型（MJ v6 / Seedance / Flux） | 高（迁工艺） | 5/5 | 主力换 + 重训 |
| 4 | 手画 / 3D 建模渲染 | 极高（人/外包） | 5/5 | 真正工业级 IP |

### 11.4 红果级 IP 设计阶段建议

**前期阶段就避坑**：

```
✅ 优先选「玻璃塔 / 圆球 / 几何简单」建筑作角色
❌ 避免「带檐角 / 多层塔 / 复杂宫殿」（除非接受 chibi 人体形态）
```

SD-002《城市恋综》选错 4 城（杭州雷峰塔 / 北京故宫 / 武汉黄鹤楼 / 广州小蛮腰）→ 这 4 城分镜图永远是 chibi 人体。如换成「上海+深圳+香港中银+台北101+迪拜哈利法塔」清一色现代摩天楼 → 全部纯拟物。

### 11.5 一句话铁律

> **「分镜图工艺是 ref 工艺的下游，ref 不纯，分镜图无法救」**
>
> ref 阶段就要跑 4-8 候选，挑「最纯拟物化」的那张作定型。
> 分镜图 prompt 只能微调，无法重塑角色形态。

---

## 附：与 ref-prompt-industrial.md 的边界

| 规则 | ref 图（ref-prompt-industrial.md） | 分镜图（本文件） |
|------|-------------------------------------|------------------|
| 视觉指纹位置 | prompt 开头前 200 token | prompt 中段（CHARACTER + STYLE 分两端） |
| 6/8 段标签 | 6 段 IDENTITY/BODY/FACE/ATTIRE/LAYOUT/STYLE | 8 段 CHARACTER/BACKGROUND/ACTION/SCENE/CAMERA/LIGHT/TEXT/STYLE |
| 灯光规则 | neutral flat even | dramatic key+rim+volumetric |
| 拟物化约束 | IS the object（必加） | 已在 ref 锁定，分镜图不重申 |
| NOT 词 | ≤5（防变人） | ≤3（不必再防变人） |
| 候选数 | 1（每角色 1 张定型） | 1-4（按 grid 重要性） |
| 用途 | 给分镜图作 (@ref.png) 引用源 | 给视频段作 image2video 首帧源 |

两份文档**互补**，跑 ref 用 ref-prompt-industrial.md，跑分镜图用本文件。
