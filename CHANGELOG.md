# 更新记录

### v0.7.0（2026-11-10）⭐ 当前
- ⭐ `scripts/拼接初剪.py`：视频段按分镜顺序一键拼成初剪（1080×1920 / 30 帧）；对白字幕烧进画面并另出 .srt；全程「AI生成」角标 + 元数据 AIGC 隐式标识；`--dry-run`、`--self-test`
- ⭐ 上线前合规：`references/compliance-2026.md`（AI 标识、2026-06 AI 微短剧分类、2026-09-01《微短剧发展管理办法》、2026-11-05 表态，每条带出处和日期）+ SKILL.md 阶段 4.E + 模板 `10_上线前检查.md` + 项目元数据 compliance 一节
- `生成分镜图.py` / `生成分集视频.py` 加 `--dry-run`：先看任务和预估积分，不调 dreamina、不写文件
- `生成分集视频.py` 加 `--model-version`（原来写死 `seedance2.0fast_vip`，没开即梦会员跑不了）
- 第 7 流派 G AI 仿真人流（`genre-flavors.md`）
- dreamina 指南：模型现状（本机 CLI 限制、Seedance 2.5、可灵 4.0、真人参考停用）、OAuth 设备登录
- 市场数字换成带日期的出处（DataEye 2026 上半年等），去掉查不到出处的数字
- 合并 #5：Sonilo 配乐 / 音效（`scripts/生成配乐.py`，第三方付费服务，可选；感谢 Sonilo 团队）
- README 重写首屏（30 秒看懂、轻量模式、一集花多少）、英文 README、issue 模板、CONTRIBUTING、GitHub Actions 离线检查
- 修：README 安装命令用新仓库名；依赖写明 Python 3.10+；版本历史挪进 CHANGELOG；SKILL.md 阶段 4 的「60 grid」旧写法

### v0.6.1（2026-05-16）
- AI 短剧专家 subagent 审报告修复 16 项（信度 disclaimer + 主流程引用 + 古建筑铁律）
- ref 70%/30% 权重等无证据断言加 disclaimer
- NOT humans 子句从「必加」改「建议加（边际 ~30%）」
- 反派词替换表加触发语境列（情感 vs 物理描述）
- 3 个 storyboard 文档合并整理（避免新手混乱）
- visual-consistency-sop.md 大幅瘦身归档

### v0.6.0（2026-05-16）
- ⭐ 分镜图 8 段 prompt SOP（`storyboard-frame-industrial.md`）：CHARACTER/BACKGROUND/ACTION/SCENE/CAMERA/LIGHT/TEXT/STYLE
- ⭐ 即梦 5.0 故障排查 + 敏感词清单（`jimeng-failure-modes.md`）：3 类 fail 区分 + prompt 1500 字硬上限 + 反派词/暧昧词替换表
- ⭐ ref 库工艺偏置铁律：现代摩天楼易拟物 / 古建筑必出 chibi 人体
- ⭐ NOT humans 子句（每个主角单独 STYLE 段）
- `scripts/生成分镜图.py` 加 3 个预检 flag：`--no-fingerprint` / `--check-length` / `--check-sensitive`
- max_workers 8 → 4 + timeout 加倍 + 2 次重试（即梦限流防）
- F 抽象拟人流加古建筑避坑硬约束（`genre-flavors.md`）
- 来源：SD-002《城市恋综》EP01 36 grid × 3 轮（v2.5/v2.6/v2.7）实战反推

### v0.4.0（2026-05-16）
- 加 F 抽象拟人流（`genre-flavors.md`）：5 流派 → 6 流派
- 来源：2026 年 3-5 月《Fruit Love Island》等水果剧爆款公式拆解

### v0.3.0（2026-05-08）
- 加 Phase 1.5 分镜图层（修改成本 3 积分 vs 视频 55 积分 = 18 倍便宜）
- 4 模视频生成（image2video / frames2video / multiframe2video / multimodal2video auto 选）
- 关键 grid 首尾帧锁定（爆点/反派/心声）
- ref 5-8 最优（仅 multimodal2video 适用，分镜图 1-2 ref；v0.6.0 澄清）
- @ 指令显式职责语法
- 新增 `生成分镜图.py` + `storyboard-frames-craft.md`

### v0.2.0（2026-05-08）
- bash → Python subprocess（避中文 prompt quoting 任务静默丢弃）
- 36 grid × 4-10s 变奏（替代 60 × 3s 死板）
- 红果必爆 7 招校准（对抗式开场 / 30s 爆破 / 60s 爽点 / 90s 反转 / 120s 爽点 / 150s 钩子 / 180s 倒计时）
- 工业级 ref 库 80-150 张（动作 / 表情 / 多角度 / 道具细节）
- 单 prompt 300-500 字（ref 段；v0.6.0 分镜图段升至 1200-1500）
- 13 失败模式 + 自动 ref 预检 + multimodal stuck 自动检测
- 新增 `troubleshooting.md` + `v21-97-percent-rules.md` + 3 个 Python 脚本

### v0.1.x（2026-04）
- 初版 5 阶段创作流程（市场情报 → IP 简报 → 故事架构 → 设定圣经 → 批判）
- 60 grid × 3s 默认
- 5 流派定调（红果纯爽 / 精品悬疑 / 漫剧奇观 / 沙雕轻喜 / 年代爽剧）
- 反套路检测 + 自我批判
