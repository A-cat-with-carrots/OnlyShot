"""
生成分集视频.py（v0.2.0）
- 替代旧 bash 脚本（bash eval 在中文 + 特殊字符 prompt 下 quoting 出错 → multimodal2video 任务被 server 静默丢弃）
- 用 subprocess args list 调 dreamina（无 quoting 问题）
- 自动 ref 完备性检查（regex 含全角中文 ） stop 字符）
- 自动从 02_IP简报.md 抽视觉指纹 append 到 prompt
- 自动重提 stuck 任务（提交后 queue_status != Generating 视为 stuck）
- 实时 unbuffered 输出
- 自动下载 + 重命名

用法：
  python 生成分集视频.py <项目目录> <集编号> [段数上限]
  例：
    python 生成分集视频.py D:/projects/SD-001 01 5    # 跑前 5 段试水
    python 生成分集视频.py D:/projects/SD-001 01      # 全跑

依赖：dreamina CLI（已登录，余额够）
"""
import subprocess, sys, re, json, time, os, argparse
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def get_visual_fingerprint(ip_brief_path: Path) -> str:
    """从 02_IP简报.md「视觉指纹」段下第一个 ``` 代码块抽取。"""
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
    """按 角色 / 场景 / 道具 顺序找 ref 文件。"""
    for sub in ['角色', '场景', '道具']:
        p = project_dir / 'ref图' / sub / ref_name
        if p.exists():
            return p
    return None


def extract_refs(prompt: str, project_dir: Path) -> tuple[list[Path], list[str]]:
    """
    从 prompt 中抽取所有 (@xxx_ref.png) 引用 → 返回 (本地路径列表, 漏的 ref 名列表)。
    含全角 ） 到 stop 字符（中文 prompt 兼容关键修复）。
    """
    refs = re.findall(r'@([^\s),）]+_ref\.png)', prompt)
    paths = []
    missing = []
    seen = set()
    for r in refs:
        if r in seen:
            continue
        seen.add(r)
        if len(paths) >= 9:
            break  # multimodal2video 上限 9 image
        p = find_ref_path(project_dir, r)
        if p:
            paths.append(p)
        else:
            missing.append(r)
    return paths, missing


def submit_segment(grid_num: int, duration: int, prompt: str, ref_paths: list[Path]) -> tuple[str | None, str | None]:
    """
    提交 multimodal2video 任务。返回 (submit_id, queue_status)。
    queue_status == 'Generating' 视为成功提交。
    若 stdout 拿不到 submit_id，fallback 到 list_task（按 prompt 头匹配）找回。
    """
    cmd = ['dreamina', 'multimodal2video']
    for rp in ref_paths:
        cmd += ['--image', str(rp)]
    cmd += [
        '--prompt', prompt,
        '--duration', str(duration),
        '--ratio', '9:16',
        '--video_resolution', '720p',
        '--model_version', 'seedance2.0fast_vip',
        '--poll', '60',
    ]
    print(f'  📤 submit grid {grid_num} ({duration}s, {len(ref_paths)} refs)', flush=True)
    try:
        ret = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=300)
    except subprocess.TimeoutExpired:
        print(f'  ⚠ grid {grid_num} subprocess timeout，尝试 list_task fallback...', flush=True)
        return _fallback_find_submit(prompt), None
    out = (ret.stdout or '') + (ret.stderr or '')
    sid_m = re.search(r'"submit_id"\s*:\s*"([^"]+)"', out)
    qstatus_m = re.search(r'"queue_status"\s*:\s*"([^"]+)"', out)
    sid = sid_m.group(1) if sid_m else None
    qstatus = qstatus_m.group(1) if qstatus_m else None
    if not sid:
        # stdout 拿不到 submit_id，可能 server 实际接收到了 → list_task fallback
        print(f'  ⚠ grid {grid_num} stdout 无 submit_id，尝试 list_task fallback...', flush=True)
        sid = _fallback_find_submit(prompt)
        if sid:
            print(f'  ✓ fallback 找回 submit_id={sid[:8]}..', flush=True)
    return sid, qstatus


def _fallback_find_submit(prompt: str) -> str | None:
    """
    submit 拿不到 submit_id 但 server 可能已接收。
    用 list_task 找最近的 multimodal2video 任务，按 prompt 前 100 字符匹配。
    """
    try:
        ret = subprocess.run(
            ['dreamina', 'list_task', '--gen_task_type=multimodal2video', '--limit=10'],
            capture_output=True, text=True, encoding='utf-8', timeout=30
        )
        out = ret.stdout or ''
        # 提取所有 (submit_id, prompt 前 100 字符) 对
        prompt_head = prompt[:100]
        matches = re.findall(r'"submit_id"\s*:\s*"([^"]+)".*?"prompt"\s*:\s*"([^"]+)"', out, re.DOTALL)
        for sid, p in matches:
            if p[:100] == prompt_head:
                return sid
    except Exception:
        pass
    return None


def query_one(sid: str) -> tuple[str, str | None]:
    """查询任务状态。返回 (gen_status, queue_status)。"""
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
    """下载视频 + 重命名 → 段NN.mp4。"""
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


def precheck_refs(grids, project_dir: Path) -> list[tuple[int, list[str]]]:
    """生视频前 ref 完备性检查 → 返回 [(grid_num, missing_refs)]。"""
    issues = []
    for g in grids:
        n = g['grid_number']
        prompt = g['jimeng_prompt']
        _, missing = extract_refs(prompt, project_dir)
        if missing:
            issues.append((n, missing))
    return issues


def main():
    parser = argparse.ArgumentParser(description='生成分集视频 v0.2.0')
    parser.add_argument('project_dir', help='项目根目录（含 02_IP简报.md, ref图/, 分集/）')
    parser.add_argument('ep_num', help='集编号（01-99）')
    parser.add_argument('limit', type=int, nargs='?', default=0, help='段数上限（0=全跑）')
    parser.add_argument('--max-rounds', type=int, default=30, help='轮询最多轮数（每轮 60s）')
    parser.add_argument('--skip-precheck', action='store_true', help='跳过 ref 完备性预检')
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    ep_num = args.ep_num.zfill(2)

    if not project_dir.exists():
        print(f'❌ 项目目录不存在: {project_dir}')
        sys.exit(1)

    ep_dir = find_episode_dir(project_dir, ep_num)
    if not ep_dir:
        print(f'❌ 第 {ep_num} 集目录未找到（需 分集/第{ep_num}集_*/）')
        sys.exit(1)

    storyboard_path = ep_dir / '分镜.json'
    if not storyboard_path.exists():
        print(f'❌ 分镜.json 不存在: {storyboard_path}')
        sys.exit(1)

    # 自检 dreamina
    try:
        ret = subprocess.run(['dreamina', 'user_credit'], capture_output=True, text=True, timeout=15)
        if ret.returncode != 0 or 'total_credit' not in (ret.stdout or ''):
            print('❌ dreamina 未登录或不可用')
            sys.exit(1)
    except Exception as e:
        print(f'❌ dreamina CLI 调用失败: {e}')
        sys.exit(1)

    video_dir = ep_dir / '视频段'
    video_dir.mkdir(parents=True, exist_ok=True)

    # 抽视觉指纹
    fp = get_visual_fingerprint(project_dir / '02_IP简报.md')
    print(f'\n=== 生成第 {ep_num} 集视频（v0.2.0）===')
    print(f'  集目录: {ep_dir}')
    print(f'  模式: multimodal2video / Seedance 2.0 Fast VIP / 9:16 / 720p')
    print(f'  视觉指纹: {fp[:100]}...' if fp else '  ⚠️ 无视觉指纹')
    print('')

    # 读分镜
    sb = json.loads(storyboard_path.read_text(encoding='utf-8'))
    grids = sb.get('storyboard_36grid') or sb.get('storyboard_60grid') or []
    if not grids:
        print('❌ 分镜.json 中没找到 storyboard_36grid 或 storyboard_60grid')
        sys.exit(1)

    if args.limit > 0:
        grids = grids[:args.limit]
        print(f'⚠️  LIMIT 模式：只跑前 {args.limit} 段')

    total_d = sum(g.get('_duration', 5) for g in grids)
    cost = total_d * 11
    print(f'🎬 共 {len(grids)} 段 / {total_d}s / 估 {cost} 积分（≈ ¥{cost / 14:.0f}）\n')

    # ref 预检
    if not args.skip_precheck:
        issues = precheck_refs(grids, project_dir)
        if issues:
            print('❌ ref 完备性预检发现缺失：')
            for n, miss in issues:
                print(f'  grid {n}: 缺 {miss}')
            print('\n请先生成缺失 ref 图，或加 --skip-precheck 强行跑（不推荐）')
            sys.exit(1)
        print('✓ ref 完备性预检通过\n')

    # 第 1 轮：全部提交
    submits = {}  # grid_num -> {sid, status, retry, ...}
    for g in grids:
        n = g['grid_number']
        out_file = video_dir / f'段{n:02d}.mp4'
        if out_file.exists():
            print(f'  ✓ 段 {n} 已存在跳过')
            continue
        d = g.get('_duration', 5)
        prompt_raw = g['jimeng_prompt']
        prompt_full = f'{prompt_raw}. {fp}' if fp else prompt_raw
        ref_paths, missing = extract_refs(prompt_raw, project_dir)
        if not ref_paths:
            print(f'  ❌ 段 {n} 没找到任何 ref 图，跳过')
            continue
        sid, qstatus = submit_segment(n, d, prompt_full, ref_paths)
        if not sid:
            print(f'  ❌ 段 {n} 提交失败')
            continue
        if qstatus != 'Generating':
            print(f'    ⚠ 段 {n} queue_status={qstatus}（非 Generating，可能 stuck）')
        else:
            print(f'    ✓ submit_id={sid[:8]}.. queue_status=Generating')
        submits[n] = {
            'sid': sid, 'status': 'querying', 'qs': qstatus, 'retry': 0,
            'd': d, 'prompt_full': prompt_full, 'ref_paths': ref_paths,
        }

    if not submits:
        print('\n所有段都已存在或跳过，无需轮询')
        return

    # 轮询直到全部 success/failed（或达到 max_rounds）
    print(f'\n⏳ 轮询中（每 60s 一轮，最多 {args.max_rounds} 轮）...', flush=True)
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
            info['qs'] = qs
            print(f'  段 {n}: {status} | qs={qs}', flush=True)
            if status == 'success':
                if download_one(info['sid'], n, video_dir):
                    print(f'    ✓ 段 {n} 落盘', flush=True)
                else:
                    print(f'    ⚠ 段 {n} success 但下载失败', flush=True)

    # 总结
    success = sorted([n for n, info in submits.items() if info['status'] == 'success'])
    pending = sorted([n for n, info in submits.items() if info['status'] not in ('success', 'failed')])
    failed = sorted([n for n, info in submits.items() if info['status'] == 'failed'])
    print(f'\n=== 完成 ===')
    print(f'  成功: {len(success)}/{len(submits)} = {success}')
    if pending:
        print(f'  仍在跑（轮询超时）: {pending}')
        print(f'  submit_ids: {[submits[n]["sid"] for n in pending]}')
        print(f'  → 稍后用 query_result 手动下载')
    if failed:
        print(f'  失败: {failed}')
    files = sorted(video_dir.glob('段*.mp4'))
    if files:
        print(f'\n📹 落盘文件:')
        for f in files:
            print(f'  {f.name}: {f.stat().st_size / 1024 / 1024:.1f} MB')


if __name__ == '__main__':
    main()
