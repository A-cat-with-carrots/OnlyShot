# 视觉一致性 SOP（v0.1.4 → v0.6.0 已大幅瘦身）

> **v0.6.0 update**：本文件 §1（视觉指纹强制 append）/ §2（4 视图组合声明）/ §3（文字 vs 乱码） / §4（人工把关）**已被 v0.6.0 三大新文档全面覆盖+部分推翻**。新手不再读本文件，直接看：
>
> - **分镜图工艺** → `references/storyboard-frame-industrial.md`
> - **ref 工艺** → `references/ref-prompt-industrial.md`
> - **即梦故障/敏感词** → `references/jimeng-failure-modes.md`
>
> 本文件下文 §1-§5 **保留为历史归档**（标 ARCHIVED）。新项目按 v0.6.0 三大文档跑。

---

## ARCHIVED §1-§5（v0.1.4 老 SOP，与 v0.6.0 冲突部分）

### v0.6.0 主要推翻的 3 条

1. ❌ **§1「scripts 自动 append 视觉指纹」**：v0.6.0 实测 ref 风格词 `neutral / flat / NOT cinematic` 会**直接禁掉分镜图 dramatic 光**。修复：`生成分镜图.py --no-fingerprint`
2. ❌ **§2「4 distinct angles」**：只在 ref 阶段适用，不要写进分镜图 prompt（分镜图是单图 9:16 不是 4 视图）
3. ⚠️ **§4 人工把关仍成立**，但「改 prompt 后必删旧图重生」要手动（脚本 auto-skip 已存在文件）

---

## 1. 视觉指纹（VISUAL FINGERPRINT）— ARCHIVED v0.1.4 老规则

### 强制规则（v0.6.0 update：仅在 ref 阶段成立，分镜图阶段用 --no-fingerprint）

**每个 IP 在 `02_IP简报.md` 顶部必须有「视觉指纹」段**，含：

- 核心风格关键词（含正向 + NOT-list）
- 比例后缀（角色/场景/道具/视频段 各自比例）
- 色板（hex 强约束）
- 禁用风格词（防漂移）

### 自动 append 机制

`scripts/生成参考图.sh` 和 `scripts/生成分集视频.sh` 必须从 02_IP简报.md 自动提取视觉指纹**追加到每个 prompt 末尾**。

```bash
# 提取
VISUAL_FINGERPRINT=$("$PYTHON_CMD" "$EXTRACTOR" --fingerprint "$IP_BRIEF")

# Append
full_prompt="$prompt. $VISUAL_FINGERPRINT"
```

不带视觉指纹的 prompt 不允许提交即梦。

### 范例（漫剧奇观流）

```
manhua style, cell-shaded comic book art, vibrant saturated colors with bold outlines,
mythical Chinese celestial setting with energy aura, glowing runes, particle effects,
dramatic chiaroscuro lighting, cinematic CGI, ultra detailed,
NOT realistic photography, NOT live-action, NOT 3D rendered photoreal,
NO garbled characters, NO illegible scribble text
```

---

## 2. 多视图组合图防 AI 偷懒

### 问题

四宫格 / 三视图 / 多角度 ref 图，AI 经常**把同一个角度复制到 2-3 个格子**，浪费多角度参考价值。

### 解法

prompt 中**显式声明**：

```
4 distinct different angles, no duplicate views, each panel shows clearly different orientation
```

或具体到角度：

```
左上正面平视（X 角度），右上侧面 45 度（Y 角度），左下纯背面（Z 角度），右下使用激活态（W 角度）
```

不写就 AI 偷懒。

---

## 3. 文字 vs 乱码

### 原则

**文字 ≠ 乱码**。文字本身没问题（系统弹窗 UI / 白板 KPI / 屏幕代码 / 招牌都该有），**乱码** 才是问题。

### 区分 3 类文字（v0.1.4 修订 — 人工把关 > 强制限制）

| 类 | 处理 |
|----|------|
| **必要文字**（UI / 招牌 / 黑板 / 屏幕代码 / 工位名牌）| 保留 prompt 描述 + 明确指定 `clear legible English text` 或 `clear legible Chinese characters「具体字」, no garbled text` 防乱码 |
| **角色名字写场景里**（如「陈笑工位牌」「凌霄宝殿匾额」）| **可以写 prompt**，但必须明确指定字符内容 + 防乱码关键词。AI 仍可能写错 → 人工把关 → 不行重生 |
| **不必要的测量数字**（30cm / 2 米 / 5cm 宽）| 从 prompt 删，无信息价值还易乱码 |

### 实战示例

**场景：陈笑工位有名牌**

✅ 写法：
> 现代办公室，陈笑工位，工位牌写 clear legible Chinese characters「陈笑」, no garbled text, no other random text

**场景：天庭凌霄宝殿匾额**

✅ 写法：
> 凌霄宝殿，宝座前匾额 clear legible Chinese characters「凌霄宝殿」 in classic Song typeface, no garbled text

### v0.1.4 设计原则：人工把关 > 强制限制

之前 v0.1.3 试图通过"删除可能出错的元素"（如改"主角工位"代替"陈笑工位"）减少 AI 出错风险，但这导致信息损失（剧情细节丢失）。

v0.1.4 改为：**保留 prompt 完整表达 + 显式声明清晰文字 + 用户人工把关 + 错误重生**。

成本上：单图重生 ¥1 左右，比丢失剧情细节的代价低得多。

---

## 4. 人工把关流程（不可省）

### 强制环节

ref 图 / 视频段生成完后，**用户必须人工逐张/逐段看**，不要直接进下一阶段。

检查清单：
- [ ] 风格统一？（全 manhua？还是混了真人）
- [ ] 角色脸不畸形？（多手指、变形等）
- [ ] 文字部分清晰可读？还是乱码？
- [ ] 名字 / 数字没错误渲染到图里？
- [ ] 多视图 ref 4 个角度真不同？
- [ ] 色调跟视觉指纹一致？

### 重生流程

发现问题 → 删该图 → 改 prompt（如有 prompt 错误）/ 改视觉指纹 → 重跑脚本。

**关键陷阱**：脚本「已存在跳过」逻辑会导致用旧图。改 prompt 后**必须先删旧图**才能让新 prompt 生效。

---

## 5. CLI 调用注意事项（实战教训）

### Python 解释器

Windows Git Bash + 系统装了 Microsoft Store python3 stub → `command -v python3` 找到 stub → 调用静默失败（无任何输出）。

修：`PYTHON_CMD=$(command -v python || command -v python3)` + `python -c "print('ok')"` 验证。

### Python stdout 编码

Windows 终端默认 GBK，Python 默认 UTF-8 输出 → 中文乱码截断。

修：Python 脚本头部加 `sys.stdout.reconfigure(encoding='utf-8')`。

### dreamina query_result 不带 --poll

实战发现：`dreamina query_result --submit_id=X --download_dir=Y --poll=120` 会有异常行为（exit code 非零或不下载）。

不带 `--poll` 反而 OK。脚本里：

```bash
dreamina query_result --submit_id="$submit_id" --download_dir="$out_dir" > /dev/null 2>&1 || true
```

### 不依赖 query_result exit code

dreamina query_result 即使下载成功也可能 rc≠0（CLI bug 或异常状态）。

修：脚本里**直接看文件落盘**，不看 exit code：

```bash
dreamina query_result --submit_id="$submit_id" --download_dir="$out_dir" > /dev/null 2>&1 || true
downloaded=$(ls "$out_dir/${submit_id}"_image_*.png 2>/dev/null | head -1)
if [ -n "$downloaded" ]; then
    mv "$downloaded" "$out_path"
    return 0
fi
```

### 命名规则

dreamina 默认下载文件名是 `<submit_id>_image_1.png`（图片） / `<submit_id>_video_1.mp4`（视频）。脚本要按这个 pattern 找文件 + 重命名为目标 ref 名。

### 限速 / 错误恢复

实战中发现：连续提交 ~10 个 text2image 会偶发 `get_history_by_ids failed: ret=2008`（限速）。

应对：
- 失败任务的 submit_id 已经在 dreamina 服务器有结果 → 用 `dreamina list_task --gen_status=success` 拿回 submit_id
- 或者过几分钟重跑脚本（脚本"已存在跳过"会自动只补失败的）

---

## 6. 成本控制建议

### Phase 1 ref 图

- 估算：约 ¥10-20（角色 + 场景 + 道具 ~20 张）
- 重生 1-3 张正常，超过 5 张说明视觉指纹有问题

### Phase 2 视频段

- 单集 60 段 × 3s × ¥1-3 = ¥60-180 / 集
- 全 70+ 集出片 ≈ ¥4200-12600 → **必须按集解锁，不能一次出全**

### 重生预算建议

- 每集允许重生失败段 ≤ 10 段（占 60 段的 17%）
- 超过说明 prompt / ref 有系统性问题，回到阶段 5 批判 + 改 ref + 重生

---

## 7. 用户体验流程

### Phase 1 → Phase 2 切换

skill 在阶段 3.5 完成后**必须等用户确认 ref 满意才进 Phase 2**。

不要假设 ref 一次过，要给用户「检查 → 反馈 → 重生」循环时间。

### 单集出片的等待与中断

`生成分集视频.sh` 单集 60 段 ≈ 30-90 分钟。建议：

- 后台跑（`run_in_background=true`）
- 期间用户可以做别的事
- 完成自动通知

中断恢复：脚本"已存在跳过"逻辑保证可断点续生。
