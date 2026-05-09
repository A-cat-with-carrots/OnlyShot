# 分镜图工艺（v0.3.0）

工业级 AI 短剧 5 步流程的核心层：**分镜图 = 视频首帧**。

来自 SD-001「重生穿越为哮天犬」实战 + 红果/可灵/即梦 2026 工业化制作经验沉淀。

---

## 工业级 5 步流程

```
Step 1: 剧本（LLM 生成）
Step 2: 分镜（每 grid 描述 + 动作 + 对白）
Step 3: 分镜图（每 grid 1-4 张候选静态图）⭐ 工业级核心
Step 4: 视频段（image2video / frames2video / multiframe2video / multimodal2video）
Step 5: 剪辑（拼接 + 配音 + BGM + 字幕）
```

vs v0.2.0 旧 4 步流程（跳过 Step 3 → multimodal2video 直出视频）。

---

## 为什么必须有分镜图层

### 1. 修改成本差 18 倍

| 内容 | 单价 | 修改一次 |
|------|------|---------|
| 分镜图（text2image） | 3 积分/张 | **3 积分** |
| 视频段（multimodal2video） | 11 积分/秒 × 5s | **55 积分** |

旧流程改 1 段 = 55 积分。新流程：先改图（3 积分） → 满意再花 55 积分出视频 → **省 95% 试错成本**。

### 2. 构图固定（不再随机）

multimodal2video 直出每次构图随机。同一段 prompt 跑 2 次，2 个截然不同的画面。

image2video 用分镜图作首帧 → **构图 = 静态图，不再随机**。

### 3. 角色一致性（关键场景锁脸）

每段视频独立生成 → 角色面部漂移（即使有 ref）。

分镜图先精修锁脸 → 视频从锁脸的图开始动 → **整段视频全程锁脸**。

### 4. 段间过渡可控

`frames2video` 用首帧 + 尾帧 → AI 插值中间。

关键 grid（爆点/反派揭露/心声/卡点）用首尾帧锁住开始结束 → **段间不跳变**。

---

## 4 种视频模式选择矩阵

| 模式 | 输入 | 用途 | 控制度 |
|------|------|------|--------|
| **image2video** | 1 张分镜图 + 动作 prompt | 默认主用（80%+ 段） | 高（首帧固定）|
| **frames2video** | 首帧 + 尾帧 + prompt | 关键 grid（爆点/反派/心声/卡点） | 极高（首尾固定）|
| **multiframe2video** | 2-20 张关键帧 + transition prompts | 复杂动作 / 一镜到底 | 极高（多帧固定）|
| **multimodal2video** | 9 image + 3 video + 3 audio + prompt | fallback / 多 ref 综合 | 低（构图随机）|

### 何时用哪个

```
普通对白段（80%）：image2video
  - 工位陈笑打字 / 二郎神发呆 / 玉帝端茶 / 哮天犬走路
  - 分镜图 = 静态画面 + prompt = "subtle camera push in"

关键爆点（10%）：frames2video
  - 30s 踢飞瞬间（首帧 = 二郎神抬腿，尾帧 = 哮天犬落地）
  - 玉帝心声「眼熟」（首帧 = 端茶，尾帧 = 抬眼锐视镜头）
  - 卡点定格（首帧 = 双重画面，尾帧 = 黑屏字幕）

复杂动作（5%）：multiframe2video
  - 哮天犬变身白虎星君（5 关键帧 → 渐变）
  - 二郎神接奖一镜到底 + 闪回老板（3 关键帧）

兜底（5%）：multimodal2video
  - 分镜图未生成时降级
  - 多 ref 综合需求（角色 + 场景 + 道具同时锁定）
```

---

## 分镜图生成方法论

### 文件结构

```
分集/第XX集_*/
  分镜图/
    grid01_候选1.png  ← 初版候选
    grid01_候选2.png  ← 备选
    grid01_候选3.png
    grid01.png        ← 最终选用（image2video 首帧）
    
    grid05_首.png     ← frames2video 首帧
    grid05_尾.png     ← frames2video 尾帧
    
    grid20_帧1.png    ← multiframe2video 关键帧 1
    grid20_帧2.png
    grid20_帧3.png
```

### 候选数策略

| grid 重要度 | 候选数 | 决策 |
|-----------|--------|------|
| 关键爆点（招 1/2/5/6/7） | **4 张** | 选最佳 + 留备选 |
| 标准对话段 | **2 张** | 默认 |
| 过渡段 | **1 张** | 省成本 |

每 grid 4 候选 × 36 grid = 144 张 × 3 积分 = 432 积分 ≈ ¥31 / 集
每 grid 2 候选 × 36 grid = 72 张 × 3 积分 = 216 积分 ≈ ¥15 / 集

vs 视频成本 11 × 190s = 2090 积分 ≈ ¥150 / 集。**分镜图占比 10-20%，但省视频试错 50%+**。

### 用 `生成分镜图.py`

```bash
python scripts/生成分镜图.py <项目目录> 01 --candidates=2
# 跑全集 36 grid，每 grid 2 候选，并发 8 个

python scripts/生成分镜图.py <项目目录> 01 1-5 --candidates=4
# 跑前 5 grid，每 grid 4 候选（试水）

python scripts/生成分镜图.py <项目目录> 01 5 --candidates=4
# 单 grid 4 候选（关键 grid 多备选）
```

### 选图原则

每 grid N 候选，**人工**选 1：

- ✅ 角色面部清晰 + 跟 ref 对得上
- ✅ 构图符合分镜描述（景别/角度/运镜起始）
- ✅ 关键道具/字幕清晰（工牌/工位牌/字幕）
- ✅ 灯光氛围对（冷白/暖金/夜景）
- ❌ 不接受：角色变形 / 文字乱码 / 道具缺失 / 风格漂移

选定后：`mv grid01_候选3.png grid01.png`（候选 3 是最佳）

---

## @ 指令语法（v0.3.0 升级）

### 旧 v0.2.0 隐式

```
(@哮天犬_ref.png) 哮天犬金瞳 + (@scene_03_蟠桃园_ref.png) 蟠桃园背景
```
模型不知道每个 @ 的「职责」（角色锁定？场景锁定？运镜参考？）。

### 新 v0.3.0 显式

```
@图片1 作为角色参考（哮天犬金瞳）
@图片2 作为场景背景（蟠桃园）
@视频1 参考运镜方式（缓推）
@音频1 作为背景音乐
```

模型理解每个素材的具体职责 → 生成更准。

### 落地

`生成分镜图.py` 默认仍用 v0.2.0 语法（兼容现有 prompt），但**新写 prompt 时**推荐用 v0.3.0 显式语法。

---

## 5-8 ref 最优（不塞 9）

multimodal2video 上限 9 image，但**最优 5-8**：

```
角色 × 2  → 主角 + 配角
场景 × 1  → 背景
运镜视频 × 1  → 镜头运动参考
音频 × 1  → 节奏氛围
共 5 个素材
```

**为什么不塞 9**：
- 留余量让模型理解每个素材职责
- 9 个全塞 → 模型注意力分散 → 生成质量下降
- 实战：5-7 ref 比 9 ref 一致性更稳

旧 v0.2.0 grid 1 塞 9 ref → 现在改 5-7 个最重要的。

---

## 输入分辨率限制

dreamina text2image 输入 ref 图分辨率：**640×640 至 834×1112**。

超出范围会报错或被压缩。生成 ref 时用：
- 1:1: 768×768 或 1024×1024（输入时压到 768）
- 9:16: 768×1366 或 832×1216
- 16:9: 1280×720（输入时压到 832×468）

---

## 真人 vs 漫剧风格

### 真人风格审核严格

dreamina 对真人人脸审核严格：
- 政治人物 / 明星 → 直接拒
- 真实人脸特征 → 可能拒
- 替换为「演员风格」"Asian male in his 30s wearing..." → 通过

### 漫剧风格审核宽松

`manhua style + cell-shaded comic book art` → 几乎不拒绝。

**SD-001 默认漫剧奇观流**：
- 角色描述用「dynamic action lines, comic book art」修饰
- 避免「realistic photography / live-action」
- 视觉指纹强制 `NOT realistic photography, NOT live-action, NOT 3D rendered photoreal`

---

## 关键 grid 首尾帧锁定（frames2video）

红果热门短剧的「卡点画面」全用 frames2video 锁定：

```
EP01 grid 5（30s 爆破踢飞）：
  首帧：二郎神右脚抬起 90 度（参考 @二郎神_踢腿动作_ref.png 第 1 格）
  尾帧：哮天犬重落地 + 玻璃碎裂粒子 + 冲击波（参考 @哮天犬_腾空翻滚_ref.png 第 4 格）
  prompt: "踢飞动作 + 空中翻滚 + 落地玻璃碎裂"
  
  → frames2video 自动插值中间帧 → 5s 完整爆点
```

vs image2video 单首帧：开始确定但结尾随机（可能哮天犬没落地，或落地姿势错）。

vs multimodal2video 直出：首尾全随机（可能没踢到，或踢飞方向错）。

**结论**：关键爆点 grid 必用 frames2video。

---

## 5-8 ref vs 12 ref 误解

字节官方网页端「全能参考」上限 12（图 9 + 视频 3 + 音频 3 含媒体）。

但 CLI multimodal2video：
- image ≤ 9
- video ≤ 3
- audio ≤ 3
- 上限 9 image（CLI 不放开 video/audio 入口当前）

**实战经验**：5-7 image 比 9 image 角色一致性更稳。多塞稀释模型注意力。

---

## 工作流变化

### v0.2.0 旧（4 步）

```
1. 写分镜.json（含 jimeng_prompt + ref 引用）
2. ref 完备性检查
3. python 生成分集视频.py 项目 01     ← 直接 multimodal2video 出片
4. 剪映拼接
```

### v0.3.0 新（5 步）

```
1. 写分镜.json（含 jimeng_prompt + ref 引用 + video_mode 字段）
2. ref 完备性检查
3. python 生成分镜图.py 项目 01 --candidates=2   ← 新 Step 3
4. 人工选图（每 grid 候选 → 最终）
5. 关键 grid 加首尾帧（生 grid05_首.png + grid05_尾.png）
6. python 生成分集视频.py 项目 01     ← auto 模式自动选 image2video / frames2video
7. 剪映拼接
```

成本：分镜图层 +¥15-31 / 集，但省视频试错 50%+ → **总成本下降 30%**，质量提升 50%+。

---

## 自查清单

每集生视频前必查：

- [ ] 分镜.json 中每 grid 的 video_mode 字段（image2video / frames2video / multiframe2video）
- [ ] 分镜图/ 目录已生成 N 候选/grid
- [ ] 每 grid 已选定（grid01.png 存在）
- [ ] 关键爆点 grid 已生首尾帧（gridXX_首.png + gridXX_尾.png）
- [ ] ref 完备性检查通过（python ref完备性检查.py）
- [ ] 余额够（24 集 × ¥150 ≈ ¥3600）

全 ✓ → `生成分集视频.py` 自动按文件存在选模式跑。
