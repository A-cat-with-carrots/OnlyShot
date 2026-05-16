"""
生成分镜图.py（v0.6.0）
每 grid 用 dreamina text2image 出 1-4 张候选关键帧。
分镜图 = 视频首帧（image2video / frames2video 输入）。

工业级流程 Step 3：
- 修改成本：3 积分/张 vs 视频 11 积分/秒（55 积分/段）= 18 倍便宜
- 静态图先确认构图 → 满意才出视频
- 静态图自动作为 image2video / frames2video 首帧

用法：
  python 生成分镜图.py <项目目录> <集编号> [grid 范围]
  例：
    python 生成分镜图.py D:/projects/SD-001 01           # 整集 36 grid
    python 生成分镜图.py D:/projects/SD-001 01 1-5       # 前 5 grid 试水
    python 生成分镜图.py D:/projects/SD-001 01 1         # 单 grid
    python 生成分镜图.py D:/projects/SD-001 01 1 --candidates=4   # 1 grid 4 张候选

v0.6.0 新增预检 flag（SD-002 实战教训）：
  --no-fingerprint   不 append 视觉指纹（防 ref 风格词污染分镜图 dramatic 光）
  --check-length     跑前预检 prompt 字数（即梦 5.0 上限 1500，超就 warn / skip）
  --check-sensitive  跑前扫敏感词（反派词 / 暧昧词命中 warn 不阻断）

输出结构：
  分集/第XX集_*/
    分镜图/
      grid01_候选1.png
      grid01_候选2.png
      ...
      grid01.png  ← 用户选定（默认 grid01_候选1.png）

依赖：dreamina CLI（已登录），Python 3.10+（PEP 604 类型注解）
"""
import subprocess, sys, re, json, urllib.request, argparse, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


# v0.6.0 敏感词清单（来自 references/jimeng-failure-modes.md §2）
# 反派词（角色/情感语境必触发，物理语境偶发）
SENSITIVE_VILLAIN = [
    'sinister', 'menacingly', 'dark intent', 'possessive', 'dark cyan', 'dark teal',
    'dark particles', 'dark shadows engulf', 'cold smirk', 'harsh shadow',
    'dark wood', 'sinister spotlight'
]
# 暧昧词（面部特写易触发即梦面部审核）
SENSITIVE_INTIMATE = [
    'blush on cheeks', 'pink blush', 'extreme close-up upper portion',
    'extreme close-up face filling frame', 'internal warm glow',
    'subtle internal glow', 'pulsing softly', 'blooms with'
]
# 中文敏感词（subtitle / 弹幕段）
SENSITIVE_CN = ['反派', '不死心']

# 字数上限（即梦 5.0 实测，dreamina CLI 2026-05）
PROMPT_LEN_LIMIT = 1500

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


def find_episode_dir(project_dir: Path, ep_num: str) -> Path | None:
    ep_root = project_dir / '分集'
    if not ep_root.exists():
        return None
    for d in ep_root.iterdir():
        if d.is_dir() and d.name.startswith(f'第{ep_num}集_'):
            return d
    return None


def parse_grid_range(s: str | None, total: int) -> list[int]:
    if not s:
        return list(range(1, total + 1))
    if '-' in s:
        a, b = s.split('-')
        return list(range(int(a), int(b) + 1))
    return [int(s)]


def submit_one(grid_num: int, candidate_idx: int, prompt: str, fp: str, retries: int = 2) -> tuple[int, int, str | None, str | None]:
    """提交 text2image。返回 (grid_num, candidate_idx, submit_id, image_url)。retries=2 时总共最多 3 次。"""
    full_prompt = f'{prompt}, {fp}' if fp else prompt
    cmd = ['dreamina', 'text2image',
           '--prompt', full_prompt,
           '--ratio', '9:16',
           '--model_version', '5.0',
           '--resolution_type', '2k',
           '--poll', '300']
    for attempt in range(retries + 1):
        try:
            ret = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=420)
        except subprocess.TimeoutExpired:
            if attempt < retries:
                continue
            return grid_num, candidate_idx, None, None
        out = (ret.stdout or '') + (ret.stderr or '')
        sid_m = re.search(r'"submit_id"\s*:\s*"([^"]+)"', out)
        img_m = re.search(r'"image_url"\s*:\s*"([^"]+)"', out)
        if img_m:
            return grid_num, candidate_idx, sid_m.group(1) if sid_m else None, img_m.group(1)
        if attempt < retries:
            import time; time.sleep(3)
            continue
        return grid_num, candidate_idx, sid_m.group(1) if sid_m else None, None
    return grid_num, candidate_idx, None, None


def download(url: str, target: Path) -> int:
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(url, target)
        return target.stat().st_size
    except Exception:
        return 0


def main():
    parser = argparse.ArgumentParser(description='生成分镜图 v0.3.0')
    parser.add_argument('project_dir')
    parser.add_argument('ep_num')
    parser.add_argument('grid_range', nargs='?', default=None, help='grid 范围: 单 grid (5) / 范围 (1-10) / 全跑省略')
    parser.add_argument('--candidates', type=int, default=2, help='每 grid 候选数（1-4）')
    parser.add_argument('--auto-pick-first', action='store_true', help='自动用候选 1 作为最终图（无候选时用）')
    parser.add_argument('--no-fingerprint', action='store_true', help='不 append 02_IP简报.md 的视觉指纹（分镜图工艺隔离时用，避免 ref 词污染 dramatic 光）')
    parser.add_argument('--check-length', action='store_true', help='v0.6.0 预检：prompt 字数 > 1500 时 warn（即梦 5.0 实测上限）')
    parser.add_argument('--check-sensitive', action='store_true', help='v0.6.0 预检：扫反派词 / 暧昧词 / 中文敏感词，命中 warn（不阻断）')
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    ep_num = args.ep_num.zfill(2)
    candidates = max(1, min(4, args.candidates))

    ep_dir = find_episode_dir(project_dir, ep_num)
    if not ep_dir:
        print(f'❌ 第 {ep_num} 集目录未找到')
        sys.exit(1)

    sb_path = ep_dir / '分镜.json'
    if not sb_path.exists():
        print(f'❌ 分镜.json 不存在')
        sys.exit(1)

    sb = json.loads(sb_path.read_text(encoding='utf-8'))
    grids = sb.get('storyboard_36grid') or sb.get('storyboard_60grid') or []
    if not grids:
        print('❌ 没找到 storyboard 字段')
        sys.exit(1)

    targets = parse_grid_range(args.grid_range, len(grids))
    grids_todo = [g for g in grids if g['grid_number'] in targets]
    if not grids_todo:
        print(f'❌ grid 范围 {args.grid_range} 无匹配')
        sys.exit(1)

    fp = '' if args.no_fingerprint else get_visual_fingerprint(project_dir / '02_IP简报.md')
    if args.no_fingerprint:
        print('  ⚠ --no-fingerprint：跳过视觉指纹 append（分镜图工艺隔离）')
    frame_dir = ep_dir / '分镜图'
    frame_dir.mkdir(parents=True, exist_ok=True)

    print(f'\n=== 生成第 {ep_num} 集分镜图（v0.3.0）===')
    print(f'  集目录: {ep_dir}')
    print(f'  grid 数: {len(grids_todo)}')
    print(f'  候选数: {candidates} 张/grid')
    print(f'  总: {len(grids_todo) * candidates} 张 × 3 积分 = {len(grids_todo) * candidates * 3} 积分（≈ ¥{len(grids_todo) * candidates * 3 / 14:.1f}）')
    print('')

    # v0.6.0 预检：字数 + 敏感词
    if args.check_length or args.check_sensitive:
        print('\n=== v0.6.0 预检 ===')
        for g in grids_todo:
            n = g['grid_number']
            p = g['jimeng_prompt']
            full = f'{p}, {fp}' if fp else p
            if args.check_length and len(full) > PROMPT_LEN_LIMIT:
                print(f'  ⚠ grid {n}: 字数 {len(full)} > {PROMPT_LEN_LIMIT}（即梦 5.0 实测上限，可能 InvalidNode）')
            if args.check_sensitive:
                hits_v = [w for w in SENSITIVE_VILLAIN if w in p.lower()]
                hits_i = [w for w in SENSITIVE_INTIMATE if w in p.lower()]
                hits_c = [w for w in SENSITIVE_CN if w in p]
                if hits_v or hits_i or hits_c:
                    print(f'  ⚠ grid {n}: 敏感词命中', end=' ')
                    if hits_v: print(f'反派={hits_v}', end=' ')
                    if hits_i: print(f'暧昧={hits_i}', end=' ')
                    if hits_c: print(f'中文={hits_c}', end=' ')
                    print('(详 references/jimeng-failure-modes.md §2)')
        print('=== 预检完成（不阻断，仅 warn）===\n')

    # 跳过已有
    todo = []
    for g in grids_todo:
        n = g['grid_number']
        for ci in range(1, candidates + 1):
            target = frame_dir / f'grid{n:02d}_候选{ci}.png'
            if target.exists():
                continue
            todo.append((n, ci, g['jimeng_prompt']))

    if not todo:
        print('全部已存在，无需生成')
    else:
        print(f'📤 并发提交 {len(todo)} 张...\n')
        with ThreadPoolExecutor(max_workers=4) as ex:
            futures = {ex.submit(submit_one, n, ci, p, fp): (n, ci) for n, ci, p in todo}
            for fut in as_completed(futures):
                n, ci = futures[fut]
                try:
                    _, _, sid, img_url = fut.result()
                except Exception as e:
                    print(f'  ❌ grid {n} 候选{ci}: {e}')
                    continue
                if not img_url:
                    print(f'  ⚠ grid {n} 候选{ci}: 无 image_url')
                    continue
                target = frame_dir / f'grid{n:02d}_候选{ci}.png'
                sz = download(img_url, target)
                print(f'  ✓ grid {n} 候选{ci} → {sz/1024:.0f} KB', flush=True)

    # auto pick: 默认 候选1 作为最终
    if args.auto_pick_first:
        print('\n📌 auto-pick：候选1 作为最终分镜图')
        for g in grids_todo:
            n = g['grid_number']
            src = frame_dir / f'grid{n:02d}_候选1.png'
            dst = frame_dir / f'grid{n:02d}.png'
            if src.exists() and not dst.exists():
                import shutil
                shutil.copy(src, dst)
                print(f'  ✓ grid {n}.png ← 候选1')

    print('\n=== 完成 ===')
    print(f'  分镜图位置: {frame_dir}')
    print('  下一步：')
    print('    1. 看每个 grid 的候选，选满意的（默认候选1）')
    print(f'    2. 重命名 grid{targets[0]:02d}_候选N.png → grid{targets[0]:02d}.png 作为最终首帧')
    print('    3. 跑 python 生成分集视频.py <项目> <集> --mode=image2video 用分镜图作首帧出视频')


if __name__ == '__main__':
    main()
