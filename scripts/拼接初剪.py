"""
拼接初剪.py（v0.7.0）
阶段 4.D 的自动化：把 视频段/段XX.mp4 按 分镜.json 的格序拼成一集初剪，
烧对白字幕、全程加 AI 标识角标、文件元数据写隐式标识。
拼好的初剪可以直接看，也可以接着交给 scripts/生成配乐.py 配乐，或导进剪映精修。

为什么要加标识（详见 references/compliance-2026.md，以官方文本为准）：
- 《人工智能生成合成内容标识办法》+ GB 45438-2025（2025-09-01 起）：显式标识 + 文件元数据隐式标识
- 广电总局《微短剧发展管理办法》（2026-09-01 起）：AI 生成、制作的微短剧「须在每集明显位置添加提示标识」

用法：
  python 拼接初剪.py <项目目录> <集编号> [格范围]
  例：
    python 拼接初剪.py D:/projects/SD-001 01                  # 整集（缺段会停下，列出缺哪几格）
    python 拼接初剪.py D:/projects/SD-001 01 1-5              # 只拼第 1-5 格
    python 拼接初剪.py D:/projects/SD-001 01 --allow-missing  # 跳过还没出片的格
    python 拼接初剪.py D:/projects/SD-001 01 --dry-run        # 只看计划：不跑 ffmpeg、不写文件
    python 拼接初剪.py --self-test                            # 离线自检（ffmpeg 合成假片段，不碰真实项目）

选项：
  --out-dir DIR      输出目录（默认该集目录）
  --no-burn-subs     字幕不烧进画面，只出 .srt（角标照加）
  --ai-label TEXT    角标文字（默认「AI生成」）
  --label-pos POS    角标位置：tl / tr / bl / br（默认 tr，右上）
  --no-ai-label      不加角标（不建议：上线要求每集明显位置有 AI 标识）
  --producer NAME    隐式标识里的 ContentProducer（默认 OnlyShot）
  --font NAME        字幕字体（默认 Windows 微软雅黑 / macOS 苹方 / Linux Noto Sans CJK SC）
  --size WxH         输出画面（默认 1080x1920）
  --fps N            输出帧率（默认 30）

输出（默认在该集目录）：
  初剪.mp4            H.264 + AAC，9:16
  初剪.srt            对白字幕（不含角标；平台要单独传字幕时用）
  初剪_清单.json       用了哪些段、各段时长、缺了哪些、标识写了什么

依赖：ffmpeg / ffprobe（要带 libass，常见的完整版都带），Python 3.10+
"""
import argparse
import json
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

OUT_STEM = '初剪'
TMP_ASS = '_onlyshot_subs.ass'           # 烧录时用 ASCII 文件名，避开滤镜参数里的路径转义
TMP_MP4 = '_onlyshot_roughcut.mp4'
DEFAULT_LABEL = 'AI生成'
DEFAULT_PRODUCER = 'OnlyShot'
SUB_FONT_SIZE = 60                       # 剪辑规范：字号 60
LABEL_FONT_SIZE = 40
MAX_LINE_CHARS = 14                      # 1080 宽、60 号字，一行 14 个汉字左右
INNER_SPEAKER_HINTS = ('旁白', '心声', '画外音', '内心', 'OS')
PUNCT_BREAK = '，。！？；：、,.!?;:…—'
LABEL_ALIGN = {'tl': 7, 'tr': 9, 'bl': 1, 'br': 3}   # ASS 小键盘对齐


class CutError(Exception):
    """拼接失败（给人看的原因）。"""


# ---------- 纯函数 ----------

def default_font() -> str:
    system = platform.system()
    if system == 'Windows':
        return 'Microsoft YaHei'
    if system == 'Darwin':
        return 'PingFang SC'
    return 'Noto Sans CJK SC'


def parse_grid_range(s: str | None, total: int) -> list[int]:
    """'5' / '1-10' / None（全部）。和 生成分镜图.py 同一种写法。"""
    if not s:
        return list(range(1, total + 1))
    if '-' in s:
        a, b = s.split('-', 1)
        return list(range(int(a), int(b) + 1))
    return [int(s)]


def parse_size(s: str) -> tuple[int, int]:
    m = re.fullmatch(r'(\d+)[xX×](\d+)', s.strip())
    if not m:
        raise CutError(f'--size 写成 1080x1920 这样（收到 {s}）')
    w, h = int(m.group(1)), int(m.group(2))
    if w % 2 or h % 2:
        raise CutError('--size 的宽和高要是偶数（H.264 要求）')
    return w, h


def dialogue_of(grid: dict) -> tuple[str, str]:
    d = grid.get('dialogue')
    if isinstance(d, dict):
        return str(d.get('speaker') or '').strip(), str(d.get('text') or '').strip()
    if isinstance(d, str):
        return '', d.strip()
    return '', ''


def is_inner_voice(speaker: str) -> bool:
    return any(h in speaker for h in INNER_SPEAKER_HINTS)


def wrap_cjk(text: str, max_chars: int = MAX_LINE_CHARS) -> list[str]:
    """中文字幕折行：优先在标点后断；最后一行只剩一两个字时并回上一行。"""
    text = re.sub(r'\s+', ' ', text).strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    lines, cur = [], ''
    for ch in text:
        cur += ch
        if len(cur) >= max_chars:
            cut = max(cur.rfind(p) for p in PUNCT_BREAK)
            if cut >= max_chars // 2:
                lines.append(cur[:cut + 1])
                cur = cur[cut + 1:]
            else:
                lines.append(cur)
                cur = ''
    if cur:
        if len(cur) <= 2 and lines:
            lines[-1] += cur
        else:
            lines.append(cur)
    return [line.strip() for line in lines if line.strip()]


def ts_srt(t: float) -> str:
    ms = max(0, round(t * 1000))
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


def ts_ass(t: float) -> str:
    cs = max(0, round(t * 100))
    h, rem = divmod(cs, 360_000)
    m, rem = divmod(rem, 6000)
    s, cs = divmod(rem, 100)
    return f'{h:d}:{m:02d}:{s:02d}.{cs:02d}'


def build_cues(items: list[dict]) -> list[dict]:
    """每格对白占这一段的全长（段尾留 0.08 秒），时间轴按实际片段时长累加。"""
    cues, t = [], 0.0
    for it in items:
        d = float(it['duration'])
        if it.get('text'):
            end = t + d - 0.08 if d > 0.5 else t + d
            cues.append({'grid': it['grid'], 'start': round(t, 3), 'end': round(end, 3),
                         'text': it['text'], 'inner': is_inner_voice(it.get('speaker', ''))})
        t += d
    return cues


def ass_escape(s: str) -> str:
    # ASS 里 { } 是样式标记、\ 是转义，换成全角免得被吃掉
    return s.replace('\\', '＼').replace('{', '｛').replace('}', '｝')


def build_ass(cues: list[dict], total: float, label: str | None, label_pos: str,
              font: str, width: int, height: int) -> str:
    margin_v = int(height * 0.18)            # 离底边 18%，避开平台底部的标题和简介
    lines = [
        '[Script Info]',
        'ScriptType: v4.00+',
        f'PlayResX: {width}',
        f'PlayResY: {height}',
        'WrapStyle: 2',
        'ScaledBorderAndShadow: yes',
        '',
        '[V4+ Styles]',
        'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, '
        'Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, '
        'Alignment, MarginL, MarginR, MarginV, Encoding',
        # 白字黑边（对白）
        f'Style: Dialog,{font},{SUB_FONT_SIZE},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,'
        f'-1,0,0,0,100,100,0,0,1,4,1,2,60,60,{margin_v},1',
        # 浅黄字黑边（旁白、心声）
        f'Style: Inner,{font},{SUB_FONT_SIZE},&H0080E6FF,&H0080E6FF,&H00000000,&H64000000,'
        f'-1,0,0,0,100,100,0,0,1,4,1,2,60,60,{margin_v},1',
        # 半透明黑底白字（AI 标识角标）
        f'Style: Label,{font},{LABEL_FONT_SIZE},&H00FFFFFF,&H00FFFFFF,&H80000000,&H80000000,'
        f'0,0,0,0,100,100,1,0,3,8,0,{LABEL_ALIGN[label_pos]},40,40,48,1',
        '',
        '[Events]',
        'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text',
    ]
    if label:
        lines.append(f'Dialogue: 1,{ts_ass(0)},{ts_ass(total)},Label,,0,0,0,,{ass_escape(label)}')
    for c in cues:
        text = r'\N'.join(ass_escape(x) for x in wrap_cjk(c['text']))
        style = 'Inner' if c['inner'] else 'Dialog'
        lines.append(f'Dialogue: 0,{ts_ass(c["start"])},{ts_ass(c["end"])},{style},,0,0,0,,{text}')
    return '\n'.join(lines) + '\n'


def build_srt(cues: list[dict]) -> str:
    out = []
    for i, c in enumerate(cues, 1):
        out += [str(i), f'{ts_srt(c["start"])} --> {ts_srt(c["end"])}', '\n'.join(wrap_cjk(c['text'])), '']
    return '\n'.join(out)


def aigc_metadata(producer: str, produce_id: str) -> str:
    """隐式标识：GB 45438-2025 实践示例的 7 个字段（Label=1 表示 AI 生成合成内容）。
    传播平台会补 ContentPropagator / PropagateID；格式以标准原文和平台要求为准。"""
    return json.dumps({
        'Label': '1',
        'ContentProducer': producer,
        'ProduceID': produce_id,
        'ReservedCode1': '',
        'ContentPropagator': '',
        'PropagateID': '',
        'ReservedCode2': '',
    }, ensure_ascii=False, separators=(',', ':'))


def build_ffmpeg_cmd(items: list[dict], out_name: str, width: int, height: int, fps: int,
                     ass_name: str | None, metadata_json: str, comment: str) -> list[str]:
    """一条命令拼完：统一画面和声音 → concat → 烧字幕和角标 → 写元数据。"""
    cmd = ['ffmpeg', '-hide_banner', '-nostdin', '-y']
    pairs, idx = [], 0
    for it in items:
        cmd += ['-i', str(it['path'])]
        vi = idx
        idx += 1
        if it['has_audio']:
            ai = vi
        else:
            cmd += ['-f', 'lavfi', '-t', f'{it["duration"]:.3f}', '-i', 'anullsrc=r=48000:cl=stereo']
            ai = idx
            idx += 1
        pairs.append((vi, ai, float(it['duration'])))
    parts = []
    for k, (vi, ai, d) in enumerate(pairs):
        parts.append(
            f'[{vi}:v:0]scale={width}:{height}:force_original_aspect_ratio=decrease,'
            f'pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps={fps},'
            f'format=yuv420p,trim=duration={d:.3f},setpts=PTS-STARTPTS[v{k}]')
        parts.append(
            f'[{ai}:a:0]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,'
            f'apad,atrim=duration={d:.3f},asetpts=PTS-STARTPTS[a{k}]')
    parts.append(''.join(f'[v{k}][a{k}]' for k in range(len(pairs))) + f'concat=n={len(pairs)}:v=1:a=1[vc][ac]')
    parts.append(f'[vc]ass={ass_name}[vout]' if ass_name else '[vc]null[vout]')
    cmd += [
        '-filter_complex', ';'.join(parts),
        '-map', '[vout]', '-map', '[ac]',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-r', str(fps),
        '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
        '-metadata', f'AIGC={metadata_json}',
        '-metadata', f'comment={comment}',
        '-movflags', '+faststart+use_metadata_tags',
        out_name,
    ]
    return cmd


# ---------- 读文件、调 ffmpeg ----------

def find_episode_dir(project_dir: Path, ep_num: str) -> Path | None:
    ep_root = project_dir / '分集'
    if not ep_root.exists():
        return None
    for d in sorted(ep_root.iterdir()):
        if d.is_dir() and d.name.startswith(f'第{ep_num}集_'):
            return d
    return None


def segment_file(video_dir: Path, n: int) -> Path | None:
    for name in (f'段{n:02d}.mp4', f'段{n}.mp4'):
        p = video_dir / name
        if p.is_file():
            return p
    return None


def has_tool(name: str) -> bool:
    return shutil.which(name) is not None


def has_libass() -> bool:
    try:
        ret = subprocess.run(['ffmpeg', '-hide_banner', '-filters'], capture_output=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return re.search(r'^\s*\S*\s+ass\s+V->V', ret.stdout.decode('utf-8', 'replace'), re.MULTILINE) is not None


def probe(path: Path) -> dict:
    try:
        ret = subprocess.run(
            ['ffprobe', '-v', 'error', '-print_format', 'json', '-show_streams', '-show_format', str(path)],
            capture_output=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise CutError(f'ffprobe 运行失败：{e}') from e
    if ret.returncode != 0:
        raise CutError(f'ffprobe 读不了 {path.name}')
    info = json.loads(ret.stdout.decode('utf-8', 'replace'))
    streams = info.get('streams', [])
    v = next((s for s in streams if s.get('codec_type') == 'video'), None)
    if not v:
        raise CutError(f'{path.name} 里没有视频流')
    dur = float(v.get('duration') or info.get('format', {}).get('duration') or 0)
    if dur <= 0:
        raise CutError(f'{path.name} 读不出时长')
    return {
        'duration': round(dur, 3),
        'has_audio': any(s.get('codec_type') == 'audio' for s in streams),
        'width': int(v.get('width') or 0),
        'height': int(v.get('height') or 0),
        'tags': {k.lower(): val for k, val in (info.get('format', {}).get('tags') or {}).items()},
    }


def plan(project_dir: Path, ep_num: str, grid_range: str | None, allow_missing: bool) -> dict:
    ep_dir = find_episode_dir(project_dir, ep_num)
    if not ep_dir:
        raise CutError(f'第 {ep_num} 集目录没找到（应为 {project_dir / "分集"}/第{ep_num}集_<集名>）')
    sb_path = ep_dir / '分镜.json'
    if not sb_path.is_file():
        raise CutError(f'没有 {sb_path}')
    data = json.loads(sb_path.read_text(encoding='utf-8'))
    grids = data.get('storyboard_36grid') or data.get('storyboard_60grid') or []
    if not grids:
        raise CutError('分镜.json 里没有 storyboard_36grid / storyboard_60grid')
    numbers = [int(g.get('grid_number', i + 1)) for i, g in enumerate(grids)]
    targets = set(parse_grid_range(grid_range, max(numbers)))
    video_dir = ep_dir / '视频段'
    items, missing = [], []
    for g, n in zip(grids, numbers):
        if n not in targets:
            continue
        p = segment_file(video_dir, n)
        if not p:
            missing.append(n)
            continue
        speaker, text = dialogue_of(g)
        items.append({'grid': n, 'path': p, 'speaker': speaker, 'text': text, 'planned': g.get('_duration')})
    if missing and not allow_missing:
        raise CutError(f'这些格还没有视频段：{missing}（在 {video_dir}）。'
                       '先出片，或加 --allow-missing 跳过，或用格范围只拼已有的（如 1-5）')
    if not items:
        raise CutError(f'没有可拼的视频段（{video_dir}）')
    return {'ep_dir': ep_dir, 'data': data, 'items': items, 'missing': missing}


def run(args) -> dict:
    project_dir = Path(args.project_dir).resolve()
    ep_num = str(args.ep_num).zfill(2)
    width, height = parse_size(args.size)
    label = None if args.no_ai_label else (args.ai_label or DEFAULT_LABEL).strip()
    font = args.font or default_font()
    if args.label_pos not in LABEL_ALIGN:
        raise CutError('--label-pos 只能是 tl / tr / bl / br')
    for tool in ('ffmpeg', 'ffprobe'):
        if not has_tool(tool):
            raise CutError(f'没找到 {tool}。先装 ffmpeg（Windows: winget install ffmpeg；macOS: brew install ffmpeg）')

    p = plan(project_dir, ep_num, args.grid_range, args.allow_missing)
    for it in p['items']:
        it.update(probe(it['path']))
    total = round(sum(it['duration'] for it in p['items']), 3)
    cues = build_cues(p['items'])
    out_dir = Path(args.out_dir).resolve() if args.out_dir else p['ep_dir']
    prefix = p['data'].get('video_id_prefix') or project_dir.name
    tag = '' if f'EP{ep_num}' in prefix else f'-EP{ep_num}'
    produce_id = f'{prefix}{tag}-{uuid.uuid4().hex[:8]}'
    meta = aigc_metadata(args.producer or DEFAULT_PRODUCER, produce_id)
    burn = not args.no_burn_subs
    need_ass = burn and bool(cues) or bool(label)

    print(f'\n=== 拼接第 {ep_num} 集初剪（v0.7.0）===')
    print(f'  集目录: {p["ep_dir"]}')
    print(f'  视频段: {len(p["items"])} 段，共 {total:.1f} 秒；格 {[it["grid"] for it in p["items"]]}')
    if p['missing']:
        print(f'  ⚠ 跳过没出片的格: {p["missing"]}')
    print(f'  画面: {width}×{height} / {args.fps} 帧；字幕 {len(cues)} 条（{"烧进画面" if burn else "只出 .srt"}）')
    print(f'  AI 标识: 角标「{label}」（{args.label_pos}）+ 元数据 AIGC' if label
          else '  ⚠ AI 标识: 不加角标（--no-ai-label）。上线前要在剪辑里自己加，见 references/compliance-2026.md')
    print(f'  输出: {out_dir / (OUT_STEM + ".mp4")}')
    if need_ass and not has_libass():
        raise CutError('ffmpeg 没带 libass，烧不了字幕和角标。换完整版 ffmpeg（gyan.dev full build / brew ffmpeg），'
                       '或加 --no-burn-subs --no-ai-label 只拼接（角标要在剪辑里自己加）')

    manifest = {
        'episode': ep_num,
        'episode_title': p['data'].get('episode_title', ''),
        'created': time.strftime('%Y-%m-%d %H:%M:%S'),
        'output': str(out_dir / f'{OUT_STEM}.mp4'),
        'size': f'{width}x{height}',
        'fps': args.fps,
        'total_seconds': total,
        'segments': [{'grid': it['grid'], 'file': it['path'].name, 'seconds': it['duration'],
                      'planned_seconds': it.get('planned'), 'has_audio': it['has_audio'],
                      'dialogue': it['text']} for it in p['items']],
        'missing_grids': p['missing'],
        'subtitles': {'count': len(cues), 'burned': burn and bool(cues)},
        'ai_label': {'visible': label, 'position': args.label_pos if label else None, 'aigc_metadata': json.loads(meta)},
    }
    if args.dry_run:
        print('\n（--dry-run：没有调用 ffmpeg，没有写任何文件）')
        return manifest

    out_dir.mkdir(parents=True, exist_ok=True)
    ass_name = None
    if need_ass:
        ass_cues = cues if burn else []
        (out_dir / TMP_ASS).write_text(build_ass(ass_cues, total, label, args.label_pos, font, width, height),
                                       encoding='utf-8')
        ass_name = TMP_ASS
    comment = f'含人工智能生成内容（OnlyShot 初剪，标识：{label or "未加角标"}）'
    cmd = build_ffmpeg_cmd(p['items'], TMP_MP4, width, height, args.fps, ass_name, meta, comment)
    print('\n🎬 ffmpeg 拼接中...', flush=True)
    t0 = time.monotonic()
    try:
        ret = subprocess.run(cmd, cwd=str(out_dir), capture_output=True, timeout=3600)
    except subprocess.TimeoutExpired as e:
        raise CutError('ffmpeg 超过 1 小时没结束') from e
    finally:
        if ass_name:
            (out_dir / TMP_ASS).unlink(missing_ok=True)
    if ret.returncode != 0:
        tail = '\n'.join(ret.stderr.decode('utf-8', 'replace').strip().splitlines()[-15:])
        (out_dir / TMP_MP4).unlink(missing_ok=True)
        raise CutError(f'ffmpeg 失败（返回 {ret.returncode}）：\n{tail}')
    final = out_dir / f'{OUT_STEM}.mp4'
    (out_dir / TMP_MP4).replace(final)
    (out_dir / f'{OUT_STEM}.srt').write_text(build_srt(cues), encoding='utf-8')
    got = probe(final)
    manifest['result'] = {
        'seconds': got['duration'], 'width': got['width'], 'height': got['height'],
        'has_audio': got['has_audio'], 'aigc_tag_found': 'aigc' in got['tags'],
        'bytes': final.stat().st_size, 'render_seconds': round(time.monotonic() - t0, 1),
    }
    (out_dir / f'{OUT_STEM}_清单.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                                 encoding='utf-8')
    r = manifest['result']
    print(f'  ✓ {final.name}: {r["width"]}×{r["height"]}，{r["seconds"]:.1f} 秒，'
          f'{r["bytes"] / 1024 / 1024:.1f} MB，用时 {r["render_seconds"]} 秒')
    print(f'  ✓ {OUT_STEM}.srt（{len(cues)} 条）、{OUT_STEM}_清单.json')
    print(f'  ✓ 元数据 AIGC：{"已写入" if r["aigc_tag_found"] else "⚠ 没读到，检查 ffmpeg 版本"}')
    print('🎬 下一步：配乐（scripts/生成配乐.py，可选）→ 剪映精修 → 上线前检查（references/compliance-2026.md）')
    return manifest


# ---------- 离线自检 ----------

def run_self_test() -> None:
    passed = 0

    def ok(name: str) -> None:
        nonlocal passed
        passed += 1
        print(f'  ✓ {name}')

    assert parse_grid_range(None, 3) == [1, 2, 3] and parse_grid_range('2-4', 9) == [2, 3, 4]
    assert parse_grid_range('5', 9) == [5]
    ok('格范围解析')

    assert wrap_cjk('垃圾！今晚再改一版！') == ['垃圾！今晚再改一版！']
    long = '我在这家公司干了五年，从来没有准时下班过一天，今天终于想明白了。'
    lines = wrap_cjk(long)
    assert len(lines) >= 2 and ''.join(lines) == long and all(len(x) <= MAX_LINE_CHARS + 2 for x in lines)
    assert wrap_cjk('一二三四五六七八九十一二三四五') == ['一二三四五六七八九十一二三四五']  # 末行一个字并回
    ok('字幕折行（标点处断，末行不留一两个字）')

    assert ts_srt(3723.456) == '01:02:03,456' and ts_ass(3723.456) == '1:02:03.46'
    ok('时间码')

    cues = build_cues([
        {'grid': 1, 'duration': 7.06, 'speaker': '老板', 'text': '垃圾！'},
        {'grid': 2, 'duration': 4.06, 'speaker': '陈笑（旁白）', 'text': '就这么走了？'},
        {'grid': 3, 'duration': 4.0, 'speaker': '', 'text': ''},
        {'grid': 4, 'duration': 5.0, 'speaker': '陈笑（心声）', 'text': '工资呢'},
    ])
    assert [c['grid'] for c in cues] == [1, 2, 4]
    assert cues[0]['start'] == 0 and cues[1]['start'] == 7.06 and cues[2]['start'] == 15.12
    assert not cues[0]['inner'] and cues[1]['inner'] and cues[2]['inner']
    ok('字幕时间轴按实际片段时长累加，旁白和心声单独样式')

    ass = build_ass(cues, 20.12, 'AI生成', 'tr', 'Microsoft YaHei', 1080, 1920)
    assert 'PlayResX: 1080' in ass and 'Dialogue: 1,0:00:00.00,0:00:20.12,Label,,0,0,0,,AI生成' in ass
    assert ',Inner,' in ass and ',Dialog,' in ass
    assert ass_escape('{坏}\\x') == '｛坏｝＼x'
    ok('ASS：角标全程，对白和心声两种样式，花括号转义')

    srt = build_srt(cues)
    assert srt.startswith('1\n00:00:00,000 --> 00:00:06,980\n垃圾！\n') and 'AI生成' not in srt
    ok('SRT：只有对白，不含角标')

    meta = json.loads(aigc_metadata('OnlyShot', 'SD-001-EP01-abcd'))
    assert list(meta) == ['Label', 'ContentProducer', 'ProduceID', 'ReservedCode1',
                          'ContentPropagator', 'PropagateID', 'ReservedCode2'] and meta['Label'] == '1'
    ok('隐式标识 7 个字段，Label=1')

    cmd = build_ffmpeg_cmd([
        {'path': Path('a.mp4'), 'duration': 2.0, 'has_audio': True},
        {'path': Path('b.mp4'), 'duration': 3.0, 'has_audio': False},
    ], 'out.mp4', 1080, 1920, 30, TMP_ASS, '{}', 'c')
    joined = ' '.join(cmd)
    assert cmd.count('-i') == 3 and 'anullsrc=r=48000:cl=stereo' in joined
    assert 'concat=n=2:v=1:a=1' in joined and f'ass={TMP_ASS}' in joined
    assert 'AIGC={}' in cmd and '+faststart+use_metadata_tags' in cmd
    ok('ffmpeg 命令：没声音的段补静音、concat、烧字幕、写元数据')

    if not (has_tool('ffmpeg') and has_tool('ffprobe')):
        print('  - 没装 ffmpeg，跳过真拼接的两项')
        print(f'\n✅ 自检通过（{passed} 项；真拼接未测）')
        return
    if not has_libass():
        print('  - ffmpeg 没带 libass，跳过真拼接的两项')
        print(f'\n✅ 自检通过（{passed} 项；真拼接未测）')
        return

    with tempfile.TemporaryDirectory() as td:
        proj = Path(td) / '测试项目'
        ep = proj / '分集' / '第01集_自检'
        vdir = ep / '视频段'
        vdir.mkdir(parents=True)
        storyboard = {'video_id_prefix': 'SELFTEST', 'episode': 1, 'storyboard_36grid': [
            {'grid_number': 1, '_duration': 2, 'dialogue': {'speaker': '甲', 'text': '第一句，带{花括号}'}},
            {'grid_number': 2, '_duration': 2, 'dialogue': {'speaker': '乙（心声）', 'text': '第二句心声'}},
            {'grid_number': 3, '_duration': 2, 'dialogue': {'speaker': '丙', 'text': '这一格没出片'}},
        ]}
        (ep / '分镜.json').write_text(json.dumps(storyboard, ensure_ascii=False), encoding='utf-8')

        def make(name: str, audio: bool) -> None:
            cmd = ['ffmpeg', '-hide_banner', '-nostdin', '-y', '-f', 'lavfi', '-i',
                   'testsrc=size=720x1280:rate=60:duration=2']
            if audio:
                cmd += ['-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=44100:duration=2', '-shortest']
            cmd += ['-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p']
            cmd += ['-c:a', 'aac'] if audio else []
            cmd += [str(vdir / name)]
            r = subprocess.run(cmd, capture_output=True, timeout=120)
            assert r.returncode == 0, r.stderr.decode('utf-8', 'replace')[-500:]

        make('段01.mp4', True)
        make('段02.mp4', False)

        ns = argparse.Namespace(project_dir=str(proj), ep_num='1', grid_range=None, allow_missing=False,
                                out_dir=None, no_burn_subs=False, ai_label=None, label_pos='tr',
                                no_ai_label=False, producer=None, font=None, size='1080x1920', fps=30,
                                dry_run=False)
        try:
            run(ns)
            raise AssertionError('缺段时应该停下')
        except CutError as e:
            assert '[3]' in str(e)
        ok('缺段时停下并列出缺哪几格')

        ns.allow_missing = True
        m = run(ns)
        r = m['result']
        assert (r['width'], r['height']) == (1080, 1920) and r['has_audio'] and r['aigc_tag_found']
        assert abs(r['seconds'] - 4.0) < 0.2, r['seconds']
        assert m['missing_grids'] == [3] and m['subtitles']['count'] == 2
        assert (ep / f'{OUT_STEM}.srt').read_text(encoding='utf-8').count('-->') == 2
        assert not (ep / TMP_ASS).exists() and not (ep / TMP_MP4).exists()
        ok('真拼接：1080×1920、约 4 秒、有声音、元数据带 AIGC、字幕 2 条、临时文件已清')

    print(f'\n✅ 自检通过（{passed} 项，没碰任何真实项目）')


def main() -> None:
    parser = argparse.ArgumentParser(description='拼接初剪 v0.7.0：视频段 → 一集初剪（字幕 + AI 标识）',
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('project_dir', nargs='?')
    parser.add_argument('ep_num', nargs='?')
    parser.add_argument('grid_range', nargs='?', default=None, help='格范围：5 / 1-10，省略 = 整集')
    parser.add_argument('--allow-missing', action='store_true', help='跳过还没出片的格')
    parser.add_argument('--out-dir', help='输出目录（默认该集目录）')
    parser.add_argument('--no-burn-subs', action='store_true', help='字幕不烧进画面，只出 .srt')
    parser.add_argument('--ai-label', help=f'角标文字（默认「{DEFAULT_LABEL}」）')
    parser.add_argument('--label-pos', default='tr', help='角标位置 tl / tr / bl / br（默认 tr）')
    parser.add_argument('--no-ai-label', action='store_true', help='不加角标（不建议）')
    parser.add_argument('--producer', help=f'隐式标识的 ContentProducer（默认 {DEFAULT_PRODUCER}）')
    parser.add_argument('--font', help='字幕字体')
    parser.add_argument('--size', default='1080x1920', help='输出画面（默认 1080x1920）')
    parser.add_argument('--fps', type=int, default=30, help='输出帧率（默认 30）')
    parser.add_argument('--dry-run', action='store_true', help='只看计划，不跑 ffmpeg、不写文件')
    parser.add_argument('--self-test', action='store_true', help='离线自检')
    args = parser.parse_args()

    if args.self_test:
        run_self_test()
        return
    if not args.project_dir or not args.ep_num:
        parser.print_help()
        sys.exit(1)
    try:
        run(args)
    except CutError as e:
        print(f'❌ {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
