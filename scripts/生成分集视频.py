"""
生成分集视频.py（v0.3.0）
工业级 5 步流程 Step 4：分镜图 → 视频段。

支持 4 种模式（按优先级自动选）：

| 模式 | 触发条件 | 用途 |
|------|---------|------|
| **frames2video** | 分镜图/gridXX_首.png + gridXX_尾.png | 关键 grid（爆点/反派/心声）首尾帧锁定 |
| **image2video** | 分镜图/gridXX.png（默认主用） | 每段默认 - 分镜图作首帧 + 动作 prompt |
| **multimodal2video** | 无分镜图，prompt 含 (@xxx_ref.png) | fallback - 多 ref 综合 |
| **multiframe2video** | 分镜图/gridXX_帧1.png ~ gridXX_帧N.png（2-20 张） | 一镜到底复杂动作 |

修复 v0.2.0 全部 bug：
- bash → Python subprocess（避中文 quoting）
- regex 含全角 ） stop 字符
- multimodal stuck 自动检测 + fallback list_task

用法：
  python 生成分集视频.py <项目目录> <集编号> [段数上限]
  例：
    python 生成分集视频.py D:/projects/SD-001 01 5         # 跑前 5 段试水
    python 生成分集视频.py D:/projects/SD-001 01           # 全跑
    python 生成分集视频.py D:/projects/SD-001 01 --mode=multimodal2video  # 强制旧模式
"""
import subprocess, sys, re, json, time, argparse
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def get_visual_fingerprint(ip_brief_path: Path) -> str:
    if not ip_brief_path.exists():
        return ''
    txt = ip_brief_path.read_text(encoding='utf-8')
    m = re.search(r'##\s+.*?视觉指纹.*?\n(.+?)(?=^##\s|\Z)', txt, re.DOTALL | re.MULTILINE)
    if not m:
        return ''
    code = re.search(r'```\s*\n(.+?)\n```', m.group(1), re.DOTALL)
    if not code:
        return ''
    return re.sub(r'\s+', ' ', code.group(1).strip())


def find_ref_path(project_dir: Path, ref_name: str) -> Path | None:
    for sub in ['角色', '场景', '道具']:
        p = project_dir / 'ref图' / sub / ref_name
        if p.exists():
            return p
    return None


def extract_refs(prompt: str, project_dir: Path) -> tuple[list[Path], list[str]]:
    """regex 含全角 ） stop 字符（v0.2.0 修复）"""
    refs = re.findall(r'@([^\s),）]+_ref\.png)', prompt)
    paths, missing, seen = [], [], set()
    for r in refs:
        if r in seen:
            continue
        seen.add(r)
        if len(paths) >= 9:
            break
        p = find_ref_path(project_dir, r)
        if p:
            paths.append(p)
        else:
            missing.append(r)
    return paths, missing


def detect_mode(grid_num: int, frame_dir: Path, prompt: str, project_dir: Path, force_mode: str | None) -> tuple[str, dict]:
    """
    自动选模式 + 收集参数。
    优先级：force_mode > frames2video > multiframe2video > image2video > multimodal2video
    """
    if force_mode:
        # 强制模式
        return force_mode, _collect_args(force_mode, grid_num, frame_dir, prompt, project_dir)

    first = frame_dir / f'grid{grid_num:02d}_首.png'
    last = frame_dir / f'grid{grid_num:02d}_尾.png'
    if first.exists() and last.exists():
        return 'frames2video', {'first': first, 'last': last}

    # multiframe: gridNN_帧1.png ~ gridNN_帧N.png
    multi_frames = sorted(frame_dir.glob(f'grid{grid_num:02d}_帧*.png'))
    if len(multi_frames) >= 2:
        return 'multiframe2video', {'frames': multi_frames}

    single = frame_dir / f'grid{grid_num:02d}.png'
    if single.exists():
        return 'image2video', {'image': single}

    # fallback: multimodal2video
    refs, missing = extract_refs(prompt, project_dir)
    return 'multimodal2video', {'refs': refs, 'missing': missing}


def _collect_args(mode: str, grid_num: int, frame_dir: Path, prompt: str, project_dir: Path) -> dict:
    """force_mode 用：按模式收集参数"""
    if mode == 'frames2video':
        return {
            'first': frame_dir / f'grid{grid_num:02d}_首.png',
            'last': frame_dir / f'grid{grid_num:02d}_尾.png',
        }
    if mode == 'image2video':
        return {'image': frame_dir / f'grid{grid_num:02d}.png'}
    if mode == 'multiframe2video':
        return {'frames': sorted(frame_dir.glob(f'grid{grid_num:02d}_帧*.png'))}
    refs, missing = extract_refs(prompt, project_dir)
    return {'refs': refs, 'missing': missing}


def submit_segment(grid_num: int, duration: int, prompt: str, mode: str, mode_args: dict) -> tuple[str | None, str | None]:
    """提交视频任务。返回 (submit_id, queue_status)。"""
    cmd = ['dreamina', mode]

    if mode == 'image2video':
        img = mode_args['image']
        if not img.exists():
            print(f'    ❌ 首帧图缺失: {img}')
            return None, None
        cmd += ['--image', str(img)]

    elif mode == 'frames2video':
        first, last = mode_args['first'], mode_args['last']
        if not first.exists() or not last.exists():
            print(f'    ❌ 首尾帧缺失: {first} / {last}')
            return None, None
        cmd += ['--first', str(first), '--last', str(last)]

    elif mode == 'multiframe2video':
        frames = mode_args['frames']
        if len(frames) < 2:
            print(f'    ❌ multiframe 需 ≥2 帧')
            return None, None
        # multiframe2video 用 --images stringSlice 一次传
        cmd += ['--images', ','.join(str(f) for f in frames)]
        cmd += ['--duration', str(duration)]
        # transition prompt: N-1 segment, 这里简化 = 整段 prompt
        n = len(frames)
        for _ in range(n - 1):
            cmd += ['--transition-prompt', prompt]

    elif mode == 'multimodal2video':
        refs = mode_args['refs']
        if not refs:
            print(f'    ❌ 段 {grid_num} 没找到任何 ref')
            return None, None
        for rp in refs:
            cmd += ['--image', str(rp)]

    # 共通参数（multiframe2video 不需要 model_version 不需要 video_resolution）
    cmd += ['--prompt', prompt]
    if mode != 'multiframe2video':
        cmd += ['--duration', str(duration)]
        cmd += ['--video_resolution', '720p']
        cmd += ['--model_version', 'seedance2.0fast_vip']
    if mode == 'multimodal2video':
        cmd += ['--ratio', '9:16']
    cmd += ['--poll', '60']

    ref_count_str = (
        f'first+last' if mode == 'frames2video' else
        f'{len(mode_args.get("frames", []))} frames' if mode == 'multiframe2video' else
        f'1 image' if mode == 'image2video' else
        f'{len(mode_args.get("refs", []))} refs'
    )
    print(f'  📤 submit grid {grid_num} [{mode}] ({duration}s, {ref_count_str})', flush=True)

    try:
        ret = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=300)
    except subprocess.TimeoutExpired:
        print(f'  ⚠ grid {grid_num} subprocess timeout, fallback list_task...', flush=True)
        return _fallback_find(prompt), None
    out = (ret.stdout or '') + (ret.stderr or '')
    sid_m = re.search(r'"submit_id"\s*:\s*"([^"]+)"', out)
    qstatus_m = re.search(r'"queue_status"\s*:\s*"([^"]+)"', out)
    sid = sid_m.group(1) if sid_m else None
    qstatus = qstatus_m.group(1) if qstatus_m else None
    if not sid:
        print(f'  ⚠ grid {grid_num} stdout 无 submit_id, fallback list_task...', flush=True)
        sid = _fallback_find(prompt, mode)
        if sid:
            print(f'  ✓ fallback 找回 submit_id={sid[:8]}..', flush=True)
    return sid, qstatus


def _fallback_find(prompt: str, mode: str = 'multimodal2video') -> str | None:
    try:
        ret = subprocess.run(
            ['dreamina', 'list_task', f'--gen_task_type={mode}', '--limit=10'],
            capture_output=True, text=True, encoding='utf-8', timeout=30
        )
        out = ret.stdout or ''
        prompt_head = prompt[:100]
        matches = re.findall(r'"submit_id"\s*:\s*"([^"]+)".*?"prompt"\s*:\s*"([^"]+)"', out, re.DOTALL)
        for sid, p in matches:
            if p[:100] == prompt_head:
                return sid
    except Exception:
        pass
    return None


def query_one(sid: str) -> tuple[str, str | None]:
    try:
        ret = subprocess.run(
            ['dreamina', 'query_result', '--submit_id', sid],
            capture_output=True, text=True, encoding='utf-8', timeout=60
        )
    except subprocess.TimeoutExpired:
        return 'timeout', None
    out = (ret.stdout or '') + (ret.stderr or '')
    status_m = re.search(r'"gen_status"\s*:\s*"([^"]+)"', out)
    qstatus_m = re.search(r'"queue_status"\s*:\s*"([^"]+)"', out)
    return (status_m.group(1) if status_m else 'unknown',
            qstatus_m.group(1) if qstatus_m else None)


def download_one(sid: str, grid_num: int, video_dir: Path) -> bool:
    try:
        subprocess.run(
            ['dreamina', 'query_result', '--submit_id', sid, '--download_dir', str(video_dir)],
            capture_output=True, text=True, encoding='utf-8', timeout=180
        )
    except subprocess.TimeoutExpired:
        return False
    candidates = list(video_dir.glob(f'{sid}_video_*.mp4'))
    if not candidates:
        return False
    target = video_dir / f'段{grid_num:02d}.mp4'
    candidates[0].rename(target)
    return True


def find_episode_dir(project_dir: Path, ep_num: str) -> Path | None:
    ep_root = project_dir / '分集'
    if not ep_root.exists():
        return None
    for d in ep_root.iterdir():
        if d.is_dir() and d.name.startswith(f'第{ep_num}集_'):
            return d
    return None


def main():
    parser = argparse.ArgumentParser(description='生成分集视频 v0.3.0')
    parser.add_argument('project_dir')
    parser.add_argument('ep_num')
    parser.add_argument('limit', type=int, nargs='?', default=0, help='段数上限（0=全跑）')
    parser.add_argument('--mode', choices=['auto', 'image2video', 'frames2video', 'multiframe2video', 'multimodal2video'],
                        default='auto', help='模式（auto = 按文件存在自动选）')
    parser.add_argument('--max-rounds', type=int, default=30)
    parser.add_argument('--skip-precheck', action='store_true')
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    ep_num = args.ep_num.zfill(2)
    if not project_dir.exists():
        print(f'❌ 项目目录不存在')
        sys.exit(1)

    ep_dir = find_episode_dir(project_dir, ep_num)
    if not ep_dir:
        print(f'❌ 第 {ep_num} 集目录未找到')
        sys.exit(1)

    sb_path = ep_dir / '分镜.json'
    if not sb_path.exists():
        print(f'❌ 分镜.json 不存在')
        sys.exit(1)

    # 自检 dreamina
    try:
        ret = subprocess.run(['dreamina', 'user_credit'], capture_output=True, text=True, timeout=15)
        if ret.returncode != 0 or 'total_credit' not in (ret.stdout or ''):
            print('❌ dreamina 未登录')
            sys.exit(1)
    except Exception:
        print('❌ dreamina CLI 失败')
        sys.exit(1)

    video_dir = ep_dir / '视频段'
    video_dir.mkdir(parents=True, exist_ok=True)
    frame_dir = ep_dir / '分镜图'

    fp = get_visual_fingerprint(project_dir / '02_IP简报.md')

    print(f'\n=== 生成第 {ep_num} 集视频（v0.3.0）===')
    print(f'  集目录: {ep_dir}')
    print(f'  模式: {args.mode}（auto = 按文件自动选）')
    print(f'  分镜图目录: {frame_dir}{"（不存在 → fallback multimodal2video）" if not frame_dir.exists() else ""}')
    print(f'  视觉指纹: {fp[:80]}...' if fp else '  ⚠️ 无视觉指纹')

    sb = json.loads(sb_path.read_text(encoding='utf-8'))
    grids = sb.get('storyboard_36grid') or sb.get('storyboard_60grid') or []
    if args.limit > 0:
        grids = grids[:args.limit]

    total_d = sum(g.get('_duration', 5) for g in grids)
    cost = total_d * 11
    print(f'🎬 共 {len(grids)} 段 / {total_d}s / 估 {cost} 积分（≈ ¥{cost / 14:.0f}）\n')

    # 提交所有
    submits = {}
    force_mode = None if args.mode == 'auto' else args.mode
    for g in grids:
        n = g['grid_number']
        out_file = video_dir / f'段{n:02d}.mp4'
        if out_file.exists():
            print(f'  ✓ 段 {n} 已存在跳过')
            continue
        d = g.get('_duration', 5)
        prompt = g['jimeng_prompt']
        prompt_full = f'{prompt}. {fp}' if fp else prompt

        mode, mode_args = detect_mode(n, frame_dir, prompt, project_dir, force_mode)
        sid, qstatus = submit_segment(n, d, prompt_full, mode, mode_args)
        if not sid:
            continue
        if qstatus and qstatus != 'Generating':
            print(f'    ⚠ queue_status={qstatus}')
        else:
            print(f'    ✓ submit_id={sid[:8]}.. queue_status={qstatus or "?"}')
        submits[n] = {'sid': sid, 'status': 'querying', 'mode': mode}

    if not submits:
        print('\n无段需提交')
        return

    # 轮询
    print(f'\n⏳ 轮询（每 60s 一轮，最多 {args.max_rounds} 轮）...', flush=True)
    for round_n in range(1, args.max_rounds + 1):
        pending = {n: info for n, info in submits.items()
                   if info['status'] not in ('success', 'failed')}
        if not pending:
            break
        time.sleep(60)
        print(f'\n[轮 {round_n}] 待完成 {len(pending)}: {sorted(pending.keys())}', flush=True)
        for n, info in pending.items():
            status, qs = query_one(info['sid'])
            info['status'] = status
            print(f'  段 {n} [{info["mode"]}]: {status} | qs={qs}', flush=True)
            if status == 'success':
                if download_one(info['sid'], n, video_dir):
                    print(f'    ✓ 段 {n} 落盘', flush=True)

    # 总结
    success = sorted([n for n, info in submits.items() if info['status'] == 'success'])
    pending = sorted([n for n, info in submits.items() if info['status'] not in ('success', 'failed')])
    print(f'\n=== 完成 ===')
    print(f'  成功: {len(success)}/{len(submits)} = {success}')
    if pending:
        print(f'  仍在跑: {pending}')
        print(f'  submit_ids: {[submits[n]["sid"] for n in pending]}')
    files = sorted(video_dir.glob('段*.mp4'))
    if files:
        print(f'\n📹 落盘:')
        for f in files:
            print(f'  {f.name}: {f.stat().st_size / 1024 / 1024:.1f} MB')


if __name__ == '__main__':
    main()
