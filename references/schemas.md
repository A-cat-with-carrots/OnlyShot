# JSON Schema 参考（v0.1.1）

适配 72 集 × 180s × 60 grid + 中文文件名 + 项目元数据。

---

## `项目元数据.json`

放在项目根目录。

```json
{
  "project_id": "SD-001",
  "project_name": "<>",
  "skill_version": "v0.1.1",
  "version": "v1.0",
  "created_at": "YYYY-MM-DD",
  "last_modified": "YYYY-MM-DD",
  "stage_progress": {
    "0_market": "pending|in_progress|completed",
    "1_ip": "pending|in_progress|completed",
    "2_story": "pending|in_progress|completed",
    "3_bibles": "pending|in_progress|completed",
    "4_episodes": "pending|in_progress|completed",
    "5_critique": "pending|in_progress|completed"
  },
  "params": {
    "duration_per_ep": 180,
    "total_episodes": 72,
    "grids_per_ep": 60,
    "grid_duration": 3,
    "genre": "红果纯爽流|精品悬疑流|漫剧奇观流|沙雕轻喜流|年代爽剧流",
    "platform": ["红果", "抖音"],
    "is_paid": false,
    "audience": {
      "gender": "女频|男频|全龄",
      "age": "30-55"
    }
  },
  "episodes_done": [1, 8, 27, 50, 72],
  "episodes_outline_only": [/* 其余 67 集编号 */],
  "revision_count": 0,
  "next_action": "<下一步建议>",
  "dependencies": {
    "02_IP简报.md": ["01_市场情报.md"],
    "03_完整剧本.md": ["02_IP简报.md"],
    "04_节奏地图.json": ["02_IP简报.md", "03_完整剧本.md"],
    "05_角色圣经.md": ["02_IP简报.md"],
    "06_场景圣经.md": ["02_IP简报.md"],
    "07_道具圣经.md": ["02_IP简报.md"],
    "分集/第XX集_*/": ["03_完整剧本.md", "04_节奏地图.json", "05_角色圣经.md", "06_场景圣经.md", "07_道具圣经.md"],
    "08_自我批判.md": ["分集/*"]
  },
  "archive": [
    {"version": "v1.0", "date": "YYYY-MM-DD", "trigger": "用户改流派"}
  ]
}
```

---

## `04_节奏地图.json`

整剧节奏地图，一份一剧。

```json
{
  "project_id": "SD-001",
  "project_name": "<>",
  "total_episodes": 72,
  "duration_per_ep_seconds": 180,
  "grids_per_ep": 60,
  "is_paid": false,
  "paywall_episodes": [],
  "preview_episodes": [7, 12, 27, 50],
  "episodes": [
    {
      "ep": 1,
      "title": "<标题>",
      "duration_seconds": 180,
      "core_hook": "<本集核心钩子>",
      "ending_cliffhanger": "<结尾卡点>",
      "is_paywall": false,
      "is_preview": false,
      "emotion_strength": 8,
      "beats": [
        {"t": 0, "type": "cold_open", "note": "<>"},
        {"t": 3, "type": "setup", "note": "<>"},
        {"t": 30, "type": "small_climax", "note": "<30 秒第一爆点>"},
        {"t": 60, "type": "satisfaction", "note": "<>"},
        {"t": 90, "type": "twist", "note": "<>"},
        {"t": 120, "type": "satisfaction", "note": "<>"},
        {"t": 150, "type": "reveal", "note": "<>"},
        {"t": 175, "type": "cliffhanger", "note": "<>"},
        {"t": 30, "type": "setup", "note": "桌上一枚旧戒指", "payoff_ep": 50}
      ]
    }
  ]
}
```

### beats[].type 枚举

`cold_open` / `setup` / `small_climax` / `twist` / `satisfaction` / `pain` / `reveal` / `setup_payoff` / `cliffhanger` / `paywall_punch`

### setup 与 setup_payoff 配对

```json
{"t": 30, "type": "setup", "note": "桌上一枚旧戒指", "payoff_ep": 50}
{"t": 60, "type": "setup_payoff", "note": "戒指原来是亲妈的", "setup_ep": 1}
```

阶段 5 批判时检查所有 setup 是否有 payoff。

---

## `分集/第XX集_<集名>/分镜.json`

一集一份。

```json
{
  "video_id_prefix": "SD-001-EP01",
  "episode": 1,
  "episode_title": "<集名>",
  "total_duration_seconds": 180,
  "fps": 30,
  "resolution": "1080x1920",
  "aspect_ratio": "9:16",
  "platform": "红果+抖音",
  "subtitle": true,
  "synopsis": "<本集 100 字概要>",
  "emotion_tone": "<情感基调>",
  "visual_style": {
    "style_name": "<>",
    "keywords": "<英文关键词串>",
    "lighting": "<>",
    "color_palette": ["#XXXXXX", "#XXXXXX", "#XXXXXX"]
  },
  "characters_in_episode": ["<>"],
  "scenes_in_episode": ["scene_01"],
  "props_in_episode": ["prop_01"],
  "connection": {
    "from_previous": "<>",
    "to_next": "<>"
  },
  "storyboard_60grid": [
    {
      "grid_number": 1,
      "time_start": 0.0,
      "time_end": 3.0,
      "scene_description": "<50 字画面描述>",
      "camera": {
        "type": "大特写|特写|近景|中景|全景|远景",
        "movement": "固定|推|拉|摇|移|跟|升|降",
        "angle": "平视|俯视|仰视|正面|侧面|背面"
      },
      "characters": [
        {
          "name": "<>",
          "action": "<>",
          "expression": "<>",
          "position": "左|中|右"
        }
      ],
      "dialogue": {
        "speaker": "<>",
        "text": "<≤ 15 字>",
        "emotion": "<>",
        "subtext": "<潜台词>"
      },
      "atmosphere": "<本格氛围>",
      "sfx": "<音效配方>",
      "bgm_change": false,
      "continuity_flags": [
        "<角色>: <服装/发型>",
        "<道具>: <位置/状态>"
      ],
      "jimeng_prompt": "<完整即梦 prompt：风格 + 镜头 + 场景 + (@角色_ref.png) 角色 + 氛围 + 同一角色声明 + 9:16 + 排除项>"
    }
  ]
}
```

### grid 必填字段

| 字段 | 类型 | 必填 |
|------|------|------|
| grid_number | int (1-60) | ✓ |
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

### 时间轴自检

- grid_number 1-60 连续
- time_start[N] = time_end[N-1]
- time_end[60] = 180.0

---

## 全局索引（多项目管理）

```
<workdir>/projects/index.json
```

```json
{
  "last_updated": "YYYY-MM-DD",
  "total_projects": 1,
  "next_id": "SD-002",
  "projects": [
    {
      "project_id": "SD-001",
      "project_name": "<>",
      "directory": "SD-001_<拼音>/",
      "skill_version": "v0.1.1",
      "stage_progress": {/* 同 项目元数据.json */},
      "params": {/* 同 项目元数据.json */},
      "core_hook": "<>",
      "created_date": "YYYY-MM-DD",
      "last_modified": "YYYY-MM-DD"
    }
  ]
}
```
