"""
派生分集文件.py（v0.2.0）
从分镜.json 一键派生：即梦批量包.md / 镜头清单.md
（修剧本时改分镜.json，跑此脚本派生其余两个）

用法：python 派生分集文件.py <分镜.json 路径>
"""
import json, sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def derive(storyboard_path: Path):
    data = json.loads(storyboard_path.read_text(encoding='utf-8'))
    grids = data.get('storyboard_36grid') or data.get('storyboard_60grid') or []
    if not grids:
        print('❌ 没找到 storyboard_36grid/60grid')
        sys.exit(1)

    total = data.get('total_duration_seconds') or sum(g.get('_duration', 5) for g in grids)
    ep = data.get('episode', '?')
    title = data.get('episode_title', '')
    ep_dir = storyboard_path.parent

    # 即梦批量包.md
    out = []
    out.append(f'# 第 {ep:02d} 集 即梦批量生成包（multimodal2video / Seedance 2.0 Fast VIP）')
    out.append('')
    out.append(f'- **集**：{title}')
    out.append(f'- **总时长**：{total}s（{len(grids)} 段 / 4-10s 变奏）')
    out.append(f'- **模式**：multimodal2video / 9:16 / 720p')
    out.append(f'- **视觉指纹**：脚本自动 append（来源 02_IP简报.md）')
    out.append('')
    out.append('---')
    out.append('')
    for g in grids:
        n = g['grid_number']
        d = g.get('_duration', 5)
        t0 = g.get('time_start', 0)
        t1 = g.get('time_end', 0)
        out.append(f'### 段 {n}（{t0}-{t1}s / **{d}s**）')
        out.append('')
        out.append(f'**场景**：{g.get("scene_description", "")}')
        out.append('')
        cam = g.get('camera', {})
        out.append(f'**镜头**：{cam.get("type", "")} / {cam.get("movement", "")} / {cam.get("angle", "")}')
        dlg = g.get('dialogue')
        if dlg:
            out.append(f'**对白**：{dlg.get("speaker", "")}：「{dlg.get("text", "")}」（{dlg.get("emotion", "")}）')
        out.append(f'**氛围**：{g.get("atmosphere", "")}')
        out.append(f'**音效**：{g.get("sfx", "")}')
        out.append('')
        out.append('**Prompt**：')
        out.append(f'> {g["jimeng_prompt"]}')
        out.append('')
        out.append('---')
        out.append('')
    (ep_dir / '即梦批量包.md').write_text('\n'.join(out), encoding='utf-8')
    print(f'✓ 即梦批量包.md → {len(grids)} 段, {total}s')

    # 镜头清单.md
    lst = []
    lst.append(f'# 第 {ep:02d} 集 镜头清单')
    lst.append('')
    lst.append(f'**总：{len(grids)} 段 / {total}s**')
    lst.append('')
    lst.append('| # | 时间 | 时长 | 镜头 | 场景 | 对白 |')
    lst.append('|---|------|------|------|------|------|')
    for g in grids:
        n = g['grid_number']
        d = g.get('_duration', 5)
        t0 = g.get('time_start', 0)
        t1 = g.get('time_end', 0)
        cam = g.get('camera', {})
        desc = g.get('scene_description', '')[:40]
        dlg = g.get('dialogue')
        dlg_text = f'{dlg.get("speaker", "")}：{dlg.get("text", "")[:30]}' if dlg else '—'
        lst.append(f'| {n} | {t0}-{t1}s | **{d}s** | {cam.get("type", "")}/{cam.get("movement", "")} | {desc} | {dlg_text} |')
    (ep_dir / '镜头清单.md').write_text('\n'.join(lst), encoding='utf-8')
    print('✓ 镜头清单.md')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('用法：python 派生分集文件.py <分镜.json 路径>')
        sys.exit(1)
    derive(Path(sys.argv[1]).resolve())
