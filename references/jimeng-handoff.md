# 即梦 / Seedance 2.0 出片对接规范（v0.1.2）

> **重要**：v0.1.2 起 skill 通过 **dreamina CLI 自动调用**生 ref 图 + 视频段。
> CLI 详细用法见 `references/jimeng-cli-guide.md`。本文件聚焦**对接规范**：prompt 怎么写、ref 怎么管、字幕怎么处理、出片质量怎么保证。

---

## 1. 集成路径选择

| 路径 | 适用 | 工具 |
|------|------|------|
| **路径 A（推荐）：CLI 自动** | Phase 1 阶段 3.5 + Phase 2 阶段 4.C | `dreamina text2image` / `image2video` |
| 路径 B：web 端手动 | CLI 装失败 / 需要精细控制单图 | jimeng.jianying.com 网页版 |

skill 默认走路径 A。失败 / 用户偏好时 fallback 到 B。

---

## 2. 即梦 prompt 7 要素

即梦官方推荐：

```
主体 + 细节描述 + 环境/背景 + 运动 + 风格 + 情感 + 镜头语言
```

本技能的 `jimeng_prompt`（每个分镜 grid 一个）必须覆盖全 7 要素：

| 要素 | 字段来源 |
|------|---------|
| 主体 | grid.characters[].name |
| 细节描述 | grid.characters[].action + .expression |
| 环境/背景 | grid.scene_description |
| 运动 | grid.camera.movement |
| 风格 | ip_brief.视觉关键词（每段重写）|
| 情感 | grid.atmosphere |
| 镜头语言 | grid.camera.type + .angle |

---

## 3. 角色一致性强声明（必带）

即梦最大痛点：**角色脸跳**。解决方案：

1. 每段 prompt 用 `(@角色名_ref.png)` 引用 ref 图
2. CLI 模式下用 `--image=<ref图路径>` 传入参考
3. prompt 末尾加：「同一角色，<角色名>服装/发型/外貌不变」
4. 服装变了 → 显式写「<角色名>本段穿 XXX」

---

## 4. CLI 模式下的具体调用

### Phase 1 阶段 3.5：生角色 ref

```bash
dreamina text2image \
  --prompt="<从 05_角色圣经.md 提取的中文 prompt>" \
  --ratio=9:16 \
  --resolution_type=2k \
  --download_dir=./SD-XXX/ref图/角色/ \
  --poll=120
```

或用脚本：`bash scripts/生成参考图.sh <项目目录>`

### Phase 2 阶段 4.C：生视频段

```bash
dreamina image2video \
  --image=./SD-XXX/ref图/角色/<角色>_ref.png \
  --prompt="<从 即梦批量包.md 提取的段 N 的 prompt>" \
  --duration=3 \
  --ratio=9:16 \
  --video_resolution=720P \
  --download_dir=./SD-XXX/分集/第01集_<>/视频段/ \
  --poll=120
```

或用脚本：`bash scripts/生成分集视频.sh <项目目录> <集编号>`

---

## 5. 字幕规范

即梦支持中文字幕：

- 用 **中文括号** 包：`（"对话内容"）`
- 字幕前不要加 `字幕：` 前缀
- 不需要字幕的镜头**不要**写括号

---

## 6. 视觉风格关键词每段重写

即梦每段独立生成，不重写就跳风格。

把 `02_IP简报.md` 里的视觉风格关键词作为**每段** prompt 的首句。

---

## 7. 9:16 竖屏强制

短剧 99% 是竖屏。每段 prompt 必带 `9:16 竖屏` 或 `vertical 9:16`。

横屏剧（出海 / 长剧条）才用 16:9。

---

## 8. 排除项（每段 prompt 末尾必加）

```
（排除项）严禁参考图出现在画面中。每个画面为单一画幅，无任何分割线或多宫格效果。
No speech bubbles, no comic panels, no split screen, no manga effects, no text overlays, no watermarks, no logos.
表情、嘴型、呼吸、台词严格同步。
```

---

## 9. 流派专用 prompt 关键词

### 红果纯爽流 A
```
风格：natural lighting, telephoto compression, melodrama, vibrant skin tones,
镜头：medium close-up, smooth dolly,
9:16 vertical, cinematic
```

### 精品悬疑流 B
```
风格：dark realism, low key lighting, high contrast chiaroscuro, desaturated cool palette,
镜头：dramatic angle, slow push-in,
9:16 vertical, cinematic, film grain
```

### 漫剧奇观流 C（AI 优势）
```
风格：comic book art, manhua style, cell-shaded, dynamic action lines, vibrant saturated colors,
特效：energy aura, glowing eyes, lightning sparks, magic runes, particle effects, lens flare,
氛围：epic, mythical, supernatural, otherworldly,
9:16 vertical, cinematic CGI, ultra detailed, ray traced lighting
```

### 沙雕轻喜流 D
```
风格：sitcom lighting, exaggerated expressions, vibrant pastels, animated motion,
镜头：snappy cuts, comedic angles,
9:16 vertical
```

### 年代爽剧流 E
```
风格：80s/90s color grading, warm sepia tones, film grain, period-accurate wardrobe,
道具：cathode-ray TV, old enamel cup, abacus, wood-grain wallpaper,
9:16 vertical, nostalgic atmosphere
```

---

## 10. AIGC 标识（红果 2026 强制）

剪辑时**必须**加：

- 片头 5s：「本片由 AI 生成 / AIGC」字幕
- 片尾 5s：再次出现
- 不加 → 红果不予上线

---

## 11. 故障排查

| 现象 | CLI 模式应对 |
|------|-------------|
| 角色脸总是变 | `--image` 传更高质量 ref + prompt 加「与参考图一致」3 次 |
| 服装跳 | prompt 显式写当前服装颜色 + 款式 |
| 镜头不动 | prompt 强调 `镜头慢推 / camera dolly in slowly` |
| 太静 / 没情绪 | prompt 加情绪词 + 眼神动作 |
| 出现广告水印 | prompt 末尾再加 `no watermarks, no logos, no ads` |
| 风格不一致 | 每段都重写完整视觉关键词 |
| 嘴型不对 | prompt 加 `表情、嘴型、呼吸、台词严格同步` |
| dreamina 命令失败 | 看 `~/.dreamina_cli/logs/`，跑 `dreamina --version` 检查版本 |
| 任务一直 querying | `dreamina query_result --submit_id=<ID>` 主动查 |

---

## 12. 用户跑通流程检查（交付时）

- [ ] dreamina CLI 装好且已登录
- [ ] 余额够单集 + 至少 2 集 buffer
- [ ] ref 图全部生好且用户认可
- [ ] 02_IP简报.md 视觉关键词清晰
- [ ] 即梦批量包.md 60 段 prompt 都可复制可用
- [ ] 单集出片测试通过 → 用户在剪映看到初剪片 → 满意

如有任何一步卡住，回到 SKILL.md 对应阶段重做。
