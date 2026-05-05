# JSON Schema 参考

所有机器可读文件的 JSON 结构。模板在 `assets/templates/`。

## beat_sheet.json

整剧节奏地图，一份一剧。

```json
{
  "project_id": "SD-001",
  "project_name": "《重生归来：奶奶的算计》",
  "total_episodes": 24,
  "duration_per_ep_seconds": 30,
  "is_paid": false,
  "paywall_episodes": [],
  "episodes": [
    {
      "ep": 1,
      "title": "断亲",
      "duration_seconds": 30,
      "core_hook": "奶奶 80 大寿当天宣布断亲",
      "ending_cliffhanger": "奶奶留下一份 30 年前的存折",
      "is_paywall": false,
      "beats": [
        {"t": 0,  "type": "cold_open",     "note": "奶奶在寿宴上敲拐杖，全场静"},
        {"t": 3,  "type": "setup",         "note": "全家围坐，气氛喜庆"},
        {"t": 8,  "type": "twist",         "note": "奶奶宣布：今天起，断亲"},
        {"t": 15, "type": "small_climax",  "note": "二儿媳尖叫 \"妈你疯了\""},
        {"t": 20, "type": "satisfaction",  "note": "奶奶冷笑指着大儿子手机：\"30 万转账，转给小三的\""},
        {"t": 27, "type": "cliffhanger",   "note": "奶奶从桌下拿出存折"},
        {"t": 30, "type": "setup_payoff",  "note": "（payoff_ep: 18）那张存折是 30 年前的伏笔"}
      ]
    }
  ]
}
```

### beats[].type 枚举

`cold_open` / `setup` / `small_climax` / `twist` / `satisfaction` / `pain` / `reveal` / `setup_payoff` / `cliffhanger` / `paywall_punch`

### setup 与 setup_payoff 配对

每个 `setup` 必须有对应 `payoff_ep` 字段，指向兑现的集数：

```json
{"t": 30, "type": "setup", "note": "桌上一枚旧戒指", "payoff_ep": 18}
```

`setup_payoff` 必须有 `setup_ep` 反向指向：

```json
{"t": 12, "type": "setup_payoff", "note": "戒指原来是亲妈的", "setup_ep": 1}
```

阶段 5 批判时检查所有 setup 是否有 payoff。

## storyboard.json

一集一份。每集一份 `episodes/EPxx/storyboard.json`。

```json
{
  "video_id_prefix": "SD-001-EP01",
  "episode": 1,
  "episode_title": "断亲",
  "total_duration_seconds": 30,
  "fps": 30,
  "resolution": "1080x1920",
  "aspect_ratio": "9:16",
  "platform": "红果",
  "subtitle": true,
  "synopsis": "奶奶 80 大寿当天宣布断亲，揭开 30 年前的家族秘密",
  "emotion_tone": "压抑爆发型",
  "visual_style": {
    "style_name": "暗黑写实",
    "keywords": "high contrast, dramatic lighting, desaturated, cinematic, vertical 9:16",
    "lighting": "low key",
    "color_palette": ["#1a1a1a", "#8b3a3a", "#d4af37"]
  },
  "characters_in_episode": ["奶奶", "大儿子", "二儿媳", "孙女"],
  "scenes_in_episode": ["scene_01"],
  "props_in_episode": ["prop_01"],
  "connection": {
    "from_previous": "（首集，无）",
    "to_next": "存折引出 30 年前的事"
  },
  "part_a": {
    "video_id": "SD-001-EP01-A",
    "label": "上",
    "time_range": "00:00-00:15",
    "duration_seconds": 15,
    "atmosphere": {
      "overall_mood": "暴风雨前的平静 → 雷霆爆发",
      "lighting": "暖色烛光 + 头顶冷光",
      "weather": "室内"
    },
    "bgm": {
      "description": "钢琴单音 + 低频弦乐持续 + 80bpm，奶奶宣布断亲时鼓点猛击 + 反向音效",
      "mood": "压抑→爆发"
    },
    "storyboard_9grid": [
      {
        "grid_number": 1,
        "time_start": 0.0,
        "time_end": 1.67,
        "scene_description": "全家围坐圆桌，烛光摇曳，奶奶端坐主位，拐杖立于身侧",
        "camera": {
          "type": "全景",
          "movement": "固定",
          "angle": "平视"
        },
        "characters": [
          {"name": "奶奶", "action": "端坐", "expression": "平静含威", "position": "中"},
          {"name": "大儿子", "action": "举杯", "expression": "笑", "position": "左"},
          {"name": "二儿媳", "action": "夹菜", "expression": "得意", "position": "右"}
        ],
        "dialogue": null,
        "atmosphere": "看似喜庆的寿宴",
        "sfx": "餐具碰撞 + 远处话语模糊",
        "bgm_change": false,
        "continuity_flags": [
          "奶奶: 深褐色对襟衫 + 灰白发髻",
          "桌上: 寿桃 + 红蜡烛 2 支"
        ],
        "jimeng_prompt": "暗黑电影感，high contrast，desaturated，全景固定镜头平视，古色古香的中式厅堂，圆桌上摆满寿宴菜肴，红蜡烛 2 支摇曳，(@奶奶_ref.png) 奶奶端坐主位，深褐色对襟衫，灰白发髻，平静含威的表情，左侧 (@大儿子_ref.png) 大儿子举杯笑，右侧 (@二儿媳_ref.png) 二儿媳夹菜得意，氛围：看似喜庆的寿宴下暗流涌动，同一角色，所有人物服装/发型/外貌不变，9:16 竖屏，cinematic，浅景深。（排除项）严禁参考图出现在画面中。每个画面为单一画幅，无任何分割线或多宫格效果。No speech bubbles, no text overlays, no watermarks. 表情、嘴型、呼吸、台词严格同步。"
      }
    ]
  },
  "part_b": {
    "video_id": "SD-001-EP01-B",
    "label": "下",
    "time_range": "00:15-00:30",
    "duration_seconds": 15,
    "atmosphere": {},
    "bgm": {},
    "storyboard_9grid": []
  }
}
```

### grid 必填字段

| 字段 | 类型 | 必填 |
|------|------|------|
| grid_number | int | ✓ |
| time_start | float | ✓ |
| time_end | float | ✓ |
| scene_description | string | ✓ |
| camera.type | enum | ✓ |
| camera.movement | enum | ✓ |
| camera.angle | enum | ✓ |
| characters | array | ✓（可空数组）|
| dialogue | object/null | ✓ |
| atmosphere | string | ✓ |
| sfx | string | ✓ |
| bgm_change | bool | ✓ |
| continuity_flags | array | ✓（可空）|
| jimeng_prompt | string | ✓（核心交付！）|

### camera 字段枚举

- `type`: `大特写` / `特写` / `近景` / `中景` / `全景` / `远景`
- `movement`: `固定` / `推` / `拉` / `摇` / `移` / `跟` / `升` / `降`
- `angle`: `平视` / `俯视` / `仰视` / `正面` / `侧面` / `背面`

### dialogue 结构

```json
"dialogue": {
  "speaker": "奶奶",
  "text": "今天起，断亲。",
  "emotion": "冷峻",
  "subtext": "我已经知道你们做的所有事"
}
```

无对话时 `"dialogue": null`。

## index.json（项目目录索引）

放在 `<workdir>/projects/index.json`，全局管理。

```json
{
  "last_updated": "2026-05-05",
  "total_projects": 1,
  "next_id": "SD-002",
  "projects": [
    {
      "project_id": "SD-001",
      "project_name": "断亲奶奶",
      "directory": "SD-001_dqnn/",
      "episodes": 24,
      "is_paid": false,
      "platform": ["红果", "抖音"],
      "status": "scripted",
      "stage_completed": [0, 1, 2, 3, 4, 5],
      "created_date": "2026-05-05",
      "core_hook": "奶奶 80 大寿当天宣布断亲，理由 30 年没说出口"
    }
  ]
}
```

### status 枚举

- `ip_briefed` — 阶段 1 完
- `architected` — 阶段 2 完
- `bibled` — 阶段 3 完
- `scripted` — 阶段 4 完
- `critiqued` — 阶段 5 完
- `delivered` — 全部完
