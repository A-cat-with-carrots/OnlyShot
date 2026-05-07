"""
ref完备性检查.py（v0.2.0）
扫整集分镜.json 中所有 (@xxx_ref.png) 引用 → 校验 ref图/ 是否本地有对应文件。
生视频前必跑（防 ref 漏 → AI 自由生成 → 角色不一致）。

用法：
  python ref完备性检查.py <项目目录> [集编号]
  例：
    python ref完备性检查.py D:/projects/SD-001        # 检查所有集
    python ref完备性检查.py D:/projects/SD-001 01     # 只检查第 1 集

中文 prompt 注意：regex 含全角 ） stop 字符（v0.2.0 修复）
"""
import json, re, sys
from pathlib import Path
from collections import Counter

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def find_ref_path(project_dir: Path, ref_name: str) -> Path | None:
    for sub in ['角色', '场景', '道具']:
        p = project_dir / 'ref图' / sub / ref_name
        if p.exists():
            return p
    return None


def extract_refs(prompt: str) -> list[str]:
    """含全角 ） stop 字符（中文 prompt 兼容关键修复）。"""
    return re.findall(r'@([^\s),）]+_ref\.png)', prompt)


def check_episode(project_dir: Path, storyboard_path: Path) -> bool:
    """检查单集。返回 True = 全 OK，False = 有缺失。"""
    data = json.loads(storyboard_path.read_text(encoding='utf-8'))
    grids = data.get('storyboard_36grid') or data.get('storyboard_60grid') or []
    if not grids:
        print(f'  ⚠ {storyboard_path.parent.name}: 没找到 storyboard 字段')
        return False

    all_refs = []
    issues = []
    for g in grids:
        n = g['grid_number']
        prompt = g['jimeng_prompt']
        refs = extract_refs(prompt)
        all_refs.extend(refs)
        missing = []
        for r in set(refs):
            if not find_ref_path(project_dir, r):
                missing.append(r)
        if missing:
            issues.append((n, missing))

    ep = data.get('episode', '?')
    title = data.get('episode_title', storyboard_path.parent.name)
    print(f'\n=== 第 {ep:02d} 集: {title} ===')

    counter = Counter(all_refs)
    print(f'引用统计（{len(counter)} 种 ref）:')
    for ref, cnt in sorted(counter.items(), key=lambda x: -x[1]):
        ok = '✓' if find_ref_path(project_dir, ref) else '❌ 缺'
        print(f'  {ok} {ref}: {cnt} 次')

    # 单 grid ref 数（multimodal2video 上限 9）
    over9 = []
    for g in grids:
        n = g['grid_number']
        refs = set(extract_refs(g['jimeng_prompt']))
        valid = [r for r in refs if find_ref_path(project_dir, r)]
        if len(valid) > 9:
            over9.append((n, len(valid)))
    if over9:
        print(f'\n⚠️ 超 9 ref 的 grid（multimodal2video 上限）:')
        for n, cnt in over9:
            print(f'  grid {n}: {cnt} ref → 砍到 9 个')

    if issues:
        print(f'\n❌ 缺失 ref:')
        for n, miss in issues:
            print(f'  grid {n}: {miss}')
        return False

    print('\n✓ 全部 ref 完备')
    return True


def main():
    if len(sys.argv) < 2:
        print('用法：python ref完备性检查.py <项目目录> [集编号]')
        sys.exit(1)

    project_dir = Path(sys.argv[1]).resolve()
    if not project_dir.exists():
        print(f'❌ 项目目录不存在: {project_dir}')
        sys.exit(1)

    ep_root = project_dir / '分集'
    if not ep_root.exists():
        print(f'❌ 分集目录不存在: {ep_root}')
        sys.exit(1)

    target_ep = sys.argv[2].zfill(2) if len(sys.argv) >= 3 else None

    # ref 库总览
    ref_root = project_dir / 'ref图'
    if ref_root.exists():
        all_refs = list(ref_root.rglob('*.png'))
        print(f'📁 ref 库: {len(all_refs)} 张')
        for sub in ['角色', '场景', '道具']:
            sub_path = ref_root / sub
            if sub_path.exists():
                cnt = len(list(sub_path.glob('*.png')))
                print(f'  {sub}: {cnt}')

    # 找所有集
    eps = sorted([d for d in ep_root.iterdir() if d.is_dir() and d.name.startswith('第')])
    if target_ep:
        eps = [d for d in eps if d.name.startswith(f'第{target_ep}集_')]
        if not eps:
            print(f'❌ 第 {target_ep} 集目录未找到')
            sys.exit(1)

    all_ok = True
    for ep_dir in eps:
        sb = ep_dir / '分镜.json'
        if not sb.exists():
            print(f'\n⚠ {ep_dir.name}: 无 分镜.json，跳过')
            continue
        ok = check_episode(project_dir, sb)
        if not ok:
            all_ok = False

    print(f'\n{"=" * 50}')
    if all_ok:
        print('✅ 全部检查通过 → 可生视频')
        sys.exit(0)
    else:
        print('❌ 有缺失 → 生 ref 图后重跑')
        sys.exit(1)


if __name__ == '__main__':
    main()
