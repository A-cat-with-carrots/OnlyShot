# Troubleshooting（v0.2.0）

SD-001 项目沉淀 13 个失败模式 + 解法。生视频前必读。

---

## 1. ⭐ bash eval 中文/特殊字符 quoting 失败 → multimodal2video 任务被 server 静默丢弃

**症状**：
- `bash 生成分集视频.sh` 提交后立即「下载失败」，但拿到 submit_id
- `dreamina list_task --gen_task_type=multimodal2video` 显示 querying
- **但**：余额不扣 + 网页端「视频生成 → 全能参考」看不到任务
- 等 30+ 分钟仍 querying（任务实际已被 server 丢弃）

**原因**：
bash `eval "dreamina multimodal2video --prompt='$full_prompt'"` 在 prompt 含中文 `「」`、`(@xxx_ref.png)`、`@`、半全角混合 字符时 quoting 解析错误。dreamina CLI 收到 malformed prompt，server 创建 task entry 但不实际处理。

**诊断**：
```bash
# 看 dreamina log 是否有此 submit_id 的提交记录
grep "<submit_id>" ~/.dreamina_cli/logs/dreamina.log.*
# 没记录 = 提交方式有问题
```

**解法**：
**禁用 bash eval。改 Python subprocess args list**：
```python
cmd = ['dreamina', 'multimodal2video',
       '--image', str(ref1), '--image', str(ref2),
       '--prompt', full_prompt,
       '--duration', '5', ...]
subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
```

v0.2.0 用 `scripts/生成分集视频.py` 替代旧 `生成分集视频.sh`。

---

## 2. awk seg_num UTF-8 字节切错（"段 �" 文件名坏）

**症状**：
```
printf: � 1: invalid number
段 �01.mp4
```

**原因**：
awk `match($0, /段 [0-9]+/)` + `substr($0, RSTART+2, RLENGTH-2)` 用字节偏移。「段」是 3 字节 UTF-8，`RSTART+2` 切到字符中间。

**解法**：
```awk
if (match($0, /段 [0-9]+/)) {
    s = substr($0, RSTART, RLENGTH)   # 取整段
    gsub(/[^0-9]/, "", s)              # 去非数字
    current_num = s
}
```

**最优**：弃 awk，用 Python（已在 v0.2.0 实现）。

---

## 3. multimodal2video 任务 stuck（querying 30+ 分钟）

**症状**：提交后 list_task 显示 querying，余额不扣，queue_status 字段缺失。

**诊断**：
```bash
dreamina query_result --submit_id=<sid> | grep queue_status
# 正常: "queue_status": "Generating"
# stuck: 没有 queue_status 字段
```

**解法**：
- 提交后立即 check `queue_status == "Generating"`
- 若不是 → 重提（任务被 server 丢弃，无积分浪费）
- v0.2.0 `生成分集视频.py` 自动 check

---

## 4. ref 引入新元素无新 ref → 一致性破

**症状**：v2.1 加「老板」描述但无 `老板_ref.png` → AI 每次生成不同形象 → 闪回反差失败。

**解法**：
**生视频前强制跑 `ref完备性检查.py`**：
```bash
python scripts/ref完备性检查.py <项目目录> [集编号]
# 全 ✓ 才能生视频
```

`生成分集视频.py` 默认 `--precheck=on`，预检失败 exit 1。

---

## 5. ref 提取 regex 漏中文括号

**症状**：grid 1 prompt `（参考 @scene_05_xxx_ref.png），(@老板_ref.png)` regex 把后续 `(@老板_ref.png` 拼到第一个 ref 名里 → ref 路径找不到 → 实际只传 1 ref（少 2 ref）。

**原因**：
旧 regex `r'@([^\s),]+_ref\.png)'` stop 字符不含全角 `）`。

**解法**：
```python
refs = re.findall(r'@([^\s),）]+_ref\.png)', prompt)
#                            ^ 加全角 ） stop 字符
```

v0.2.0 已修。

---

## 6. Python stdout UTF-8 截断（Windows GBK）

**症状**：bash pipe-to-while 静默失败，输出截断。

**原因**：Windows Python 默认 stdout encoding 跟 console codepage（GBK）。print 中文 emoji 时编码错误，stdout 截断。

**解法**：
```python
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
```

所有 v0.2.0 脚本顶部已加。

---

## 7. Microsoft Store python3 stub 静默失败

**症状**：`command -v python3` 返回 stub 路径但执行 noop（弹商店）。

**解法**：
```bash
PYTHON_CMD=$(command -v python || command -v python3)
if ! "$PYTHON_CMD" -c "print('ok')" >/dev/null 2>&1; then
    echo "python 解释器无效"; exit 1
fi
```

v0.2.0 直接用 Python，不再走 bash → 此问题消除。

---

## 8. dreamina --poll 异常 exit code

**症状**：`dreamina image2image --poll=300` 提交成功但 exit code != 0。

**解法**：
- 不依赖 exit code，看输出文件落盘
- 或去掉 --poll，用 `query_result --submit_id` + sleep loop

---

## 9. 风格漂移（角色 / 场景画风不统一）

**症状**：陈笑工位 ref 是漫画风，玉帝 ref 变成写实风 → 视频段画风跳。

**解法**：
**视觉指纹自动 append 到每个 prompt 末尾**：

`02_IP简报.md` 必含 `## 视觉指纹` 段 + ` ``` ` 代码块：
```
manhua style, cell-shaded comic book art, vibrant saturated colors with bold outlines, dynamic action lines, mythical Chinese celestial setting with energy aura, glowing runes, particle effects, lens flare, dramatic chiaroscuro lighting, NOT realistic photography, NOT live-action, NOT 3D rendered photoreal
```

`生成分集视频.py` 自动抽取 + append。

---

## 10. 多视图重复（AI 复制同一角度）

**症状**：4-grid ref 图 4 个格子全是同角度，浪费 3 格。

**解法**：
prompt 强制：`4 distinct different angles, no duplicate views`

---

## 11. 文字渲染：「乱码」≠「文字本身」

**症状**：玉如意刻「30cm」渲染成乱码 → user 误以为「文字本身有问题」。

**实际**：文字 OK，乱码才是问题。**去掉无意义测量数字**（30cm 这种），保留有剧情意义的文字（人名 / 道具名 / 字幕）。

**Prompt 写法**：
- ❌ "engraved 30cm scale"
- ✓ "clear legible Chinese characters「玉如意」"

---

## 12. 角色名误删（AI 自由替换）

**症状**：原 prompt 写「陈笑工位」，AI 生成时改成「程序员工位」丢失剧情。

**解法**：
- 角色名直接写进 prompt 显示文字：`desk nameplate clear legible Chinese characters「陈笑」`
- 工牌、屏幕、对白叠字都用此模板
- AI 出错就重生（成本低），人工把关 > 强制限制

---

## 13. 网页端看不到 multimodal2video 任务（user 误以为没提交）

**症状**：CLI 提交后网页端默认 image 历史页看不到。

**解法**：
multimodal2video = 全能参考，在网页端**「视频生成 → 全能参考 → 历史记录」** tab，**不在默认图生成历史页**。

---

## 通用诊断流程

任务失败 → 按顺序查：

```
1. dreamina user_credit               → 登录 + 余额 OK？
2. ls ~/.dreamina_cli/logs/           → log 文件存在？
3. grep <submit_id> ~/.dreamina_cli/logs/*  → 提交记录存在？
   - 没记录 = 提交方式有问题（参考 #1）
4. dreamina list_task --gen_task_type=multimodal2video --limit=10
                                      → server 端任务列表
5. dreamina query_result --submit_id=<sid> | grep queue_status
   - "Generating" = 真在跑，等
   - 没字段 = stuck，重提（参考 #3）
6. 网页端「视频生成 → 全能参考」    → 任务可见？
   - 不可见 = bash eval quoting 问题（参考 #1）
```

---

## v0.2.0 防呆清单

跑 `生成分集视频.py` 前：

- [ ] dreamina 已登录（`dreamina user_credit` 能返回）
- [ ] 余额够（每秒 11 积分；24 集 × 193s × 11 ≈ 51000 积分 ≈ ¥3650）
- [ ] `02_IP简报.md` 含 `## 视觉指纹` 段 + 代码块
- [ ] `ref图/` 目录全（`角色/`、`场景/`、`道具/` 子目录）
- [ ] 跑 `python scripts/ref完备性检查.py <项目>` 全 ✓
- [ ] 第 1 集先 B 试水（5 段 ≈ ¥20）验证一致性
- [ ] 网页端「视频生成 → 全能参考」tab 能看到任务
