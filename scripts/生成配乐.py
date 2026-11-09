"""
生成配乐.py（Sonilo 集成 v0.1.0）
阶段 4.D 剪辑的可选自动化：初剪拼好后，按成片生成 BGM / 音效。

两种模式：

| 模式 | 接口 | 视频上限 | 用途 |
|------|------|---------|------|
| 配乐（默认） | video-to-music | 6 分钟 | 整集初剪 BGM：读剪辑点与情绪节奏生成，时长自动对齐 |
| 音效（--sfx） | video-to-sfx | 8 分钟 | 关键段或整集同步音效：按画面生成 |

- 第三方付费服务（Sonilo）：视频会上传到 Sonilo 处理；免费档仅限个人非商用，商用以 Sonilo 条款为准
- 每条音轨带 license_id，自动存 *_授权.json 留档
- 按视频秒数计费，生成失败自动退款；超时长上限接口直接拒绝（不扣费）
- 纯标准库，无第三方依赖（和本仓库其他脚本一致）

准备：
  1. https://sonilo.com 注册拿 API Key（免费档每两周 2,000 积分，约够 110 秒，仅限个人非商用）
  2. export SONILO_API_KEY=sk-xxx    # 只走环境变量，绝不写进代码/配置/仓库

用法：
  python 生成配乐.py <视频文件> [--prompt "风格提示"]
  python 生成配乐.py <视频文件> --sfx [--segments 分段.json]
  python 生成配乐.py --resume <task_id>     # 找回超时/中断的任务
  python 生成配乐.py --self-test            # 离线自检（不联网、不扣费）
  例：
    python 生成配乐.py 分集/第01集_胡同重生/初剪.mp4
    python 生成配乐.py 分集/第01集_胡同重生/初剪.mp4 --prompt "国风悬疑，30 秒爆破点跟着踢门动作起"
    python 生成配乐.py 分集/第01集_胡同重生/视频段/段13.mp4 --sfx --segments 音效分段.json

详见 references/sonilo-audio-guide.md（3 个完整示例 + prompt 写法 + segments 规则）。
"""
import argparse
import json
import os
import subprocess
import sys
import time
import uuid
import urllib.error
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

DEFAULT_BASE_URL = 'https://api.sonilo.com'
MUSIC_MAX_SECONDS = 360   # 配乐接口视频上限 6 分钟
SFX_MAX_SECONDS = 480     # 音效接口视频上限 8 分钟（2026-11 官方 OpenAPI）
UPLOAD_SIZE_WARN_MB = 300 # 常见账户上传体积上限
POLL_INTERVAL_SECONDS = 5
DEFAULT_TIMEOUT_SECONDS = 600
_QUERY_TIMEOUT_SECONDS = 30

# 测试接缝：自检时替换为 no-op / 假实现，避免真实等待和真实网络
_sleep = time.sleep


class SoniloError(Exception):
    """Sonilo 请求 / 生成失败。"""


def get_base_url() -> str:
    return (os.environ.get('SONILO_BASE_URL', '').strip() or DEFAULT_BASE_URL).rstrip('/')


def get_api_key() -> str:
    key = os.environ.get('SONILO_API_KEY', '').strip()
    if not key:
        raise SoniloError(
            '未配置 SONILO_API_KEY 环境变量。\n'
            '  https://sonilo.com 注册拿 API Key（免费档仅限个人非商用），然后：\n'
            '  export SONILO_API_KEY=sk-xxx'
        )
    return key


def probe_duration(video: Path) -> float:
    """尽力而为的本地时长预检。ffprobe 不在 / 失败就返回 0，
    交给后端做最终校验（超上限直接 422 拒绝，不创建任务、不扣费）。"""
    try:
        ret = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', str(video)],
            capture_output=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0.0
    if ret.returncode != 0:
        return 0.0
    try:
        return float(json.loads(ret.stdout)['format']['duration'])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return 0.0


def _http(method: str, url: str, headers: dict | None = None,
          body: bytes | None = None, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> tuple[int, bytes]:
    """统一 HTTP 出口（自检时整体替换成假实现）。返回 (status, body)。"""
    req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except (urllib.error.URLError, OSError) as e:
        reason = getattr(e, 'reason', e)
        raise SoniloError(f'网络请求失败: {reason}') from e


def _error_detail(body: bytes) -> str:
    try:
        parsed = json.loads(body.decode('utf-8', errors='replace'))
    except (json.JSONDecodeError, ValueError):
        return body.decode('utf-8', errors='replace')[:300]
    if isinstance(parsed, dict):
        detail = parsed.get('detail') or parsed.get('message') or parsed.get('error')
        if isinstance(detail, str) and detail.strip():
            return detail.strip()
    return body.decode('utf-8', errors='replace')[:300]


def http_error_message(status: int, body: bytes) -> str:
    detail = _error_detail(body)
    if status == 401:
        return 'API Key 无效，检查 SONILO_API_KEY 是否填对'
    if status == 402:
        return f'账户余额不足（sonilo.com 可查用量 / 充值）: {detail}'
    if status == 413:
        return f'视频文件过大（剪映导出用 1080p / 中码率可减小体积）: {detail}'
    if status == 422:
        return f'参数不合法（常见：视频超时长上限、segments 不满足规则）: {detail}'
    if status == 429:
        return f'触发频率限制，稍等再跑: {detail}'
    return f'接口错误 ({status}): {detail}'


def encode_multipart(fields: dict[str, str], file_field: str, file_path: Path) -> tuple[bytes, str]:
    """标准库版 multipart/form-data 编码（避免引入第三方依赖）。"""
    boundary = uuid.uuid4().hex
    parts = []
    for name, value in fields.items():
        parts.append(
            (f'--{boundary}\r\n'
             f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
             f'{value}\r\n').encode('utf-8')
        )
    parts.append(
        (f'--{boundary}\r\n'
         f'Content-Disposition: form-data; name="{file_field}"; filename="{file_path.name}"\r\n'
         f'Content-Type: video/mp4\r\n\r\n').encode('utf-8')
    )
    parts.append(file_path.read_bytes())
    parts.append(f'\r\n--{boundary}--\r\n'.encode('utf-8'))
    return b''.join(parts), f'multipart/form-data; boundary={boundary}'


def validate_segments(segments) -> list[str]:
    """音效 segments 本地预检。后端同样强校验（验不过整单拒绝、不扣费），
    这里提前拦住，报错信息更好读。返回错误列表（空 = 通过）。"""
    errs = []
    if not isinstance(segments, list) or not segments:
        return ['segments 必须是非空 JSON 数组']
    if len(segments) > 30:
        errs.append(f'segments 最多 30 段（当前 {len(segments)} 段），次要声音事件并入相邻主导段')
    prev_end = None
    for i, seg in enumerate(segments, 1):
        if not isinstance(seg, dict):
            errs.append(f'第 {i} 段不是对象')
            continue
        start, end, prompt = seg.get('start'), seg.get('end'), seg.get('prompt')
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            errs.append(f'第 {i} 段 start/end 必须是数字')
            continue
        if i == 1 and abs(start) > 1e-3:
            errs.append('第 1 段 start 必须是 0')
        if prev_end is not None and abs(start - prev_end) > 0.01:
            errs.append(f'第 {i} 段 start({start}) 必须等于上一段 end({prev_end})，段间要首尾相接')
        if end <= start:
            errs.append(f'第 {i} 段 end({end}) 必须大于 start({start})')
        if not isinstance(prompt, str) or not prompt.strip():
            errs.append(f'第 {i} 段 prompt 不能为空')
        elif len(prompt) > 200:
            errs.append(f'第 {i} 段 prompt 超 200 字符（当前 {len(prompt)}）')
        prev_end = end
    return errs


def submit_task(video: Path, kind: str, prompt: str, segments: list | None) -> str:
    """提交生成任务，返回 task_id。任务受理即计费（失败自动退款），不做自动重试。"""
    fields: dict[str, str] = {}
    if prompt:
        fields['prompt'] = prompt
    if kind == 'music':
        api_path = '/v1/video-to-music'
        fields['mode'] = 'async'  # 异步任务：拿 task_id 轮询，超时可 --resume 找回
    else:
        api_path = '/v1/video-to-sfx'  # 音效接口本身就是异步任务
        if segments is not None:
            fields['segments'] = json.dumps(segments, ensure_ascii=False)

    body, content_type = encode_multipart(fields, 'video', video)
    headers = {
        'Authorization': f'Bearer {get_api_key()}',
        'Content-Type': content_type,
    }
    status, resp = _http('POST', get_base_url() + api_path, headers, body)
    if status >= 400:
        raise SoniloError(http_error_message(status, resp))
    try:
        task_id = json.loads(resp).get('task_id')
    except (json.JSONDecodeError, ValueError, AttributeError):
        task_id = None
    if not task_id:
        raise SoniloError('任务已受理但未返回 task_id，联系 sonilo.com 支持并附上时间点')
    return str(task_id)


def poll_task(task_id: str, timeout: float) -> dict:
    """轮询 GET /v1/tasks/{task_id} 直到终态（succeeded/failed）。
    轮询是免费且幂等的查询，网络抖动 / 5xx 不该报废一次已计费的任务，
    在时限内继续重试；超时给出 --resume 找回指引。"""
    headers = {'Authorization': f'Bearer {get_api_key()}'}
    deadline = time.monotonic() + timeout
    while True:
        status = None
        resp = b''
        try:
            status, resp = _http(
                'GET', f'{get_base_url()}/v1/tasks/{task_id}',
                headers, timeout=_QUERY_TIMEOUT_SECONDS,
            )
        except SoniloError as e:
            print(f'  ⚠ 查询失败将重试: {e}', flush=True)

        if status is not None:
            if status >= 500:
                print(f'  ⚠ 查询返回 {status}，将重试', flush=True)
            elif status >= 400:
                raise SoniloError(f'{http_error_message(status, resp)}（task_id: {task_id}）')
            else:
                try:
                    task = json.loads(resp)
                except (json.JSONDecodeError, ValueError):
                    task = None
                if isinstance(task, dict):
                    st = task.get('status')
                    if st == 'succeeded':
                        return task
                    if st == 'failed':
                        raise SoniloError(_task_failure_message(task, task_id))
                # 非终态（pending / processing 等）继续等

        if time.monotonic() >= deadline:
            raise SoniloError(
                f'等待生成超时（{timeout:.0f}s）。任务仍在后台跑（已计费不浪费），稍后找回：\n'
                f'  python scripts/生成配乐.py --resume {task_id}'
            )
        _sleep(POLL_INTERVAL_SECONDS)


def _task_failure_message(task: dict, task_id: str) -> str:
    err = task.get('error')
    if isinstance(err, dict):
        message = err.get('message') or err.get('code') or '生成失败'
    elif isinstance(err, str) and err:
        message = err
    else:
        message = '生成失败'
    refund_note = '，费用已自动退还' if task.get('refunded') is True else ''
    return f'生成失败: {message}（task_id: {task_id}{refund_note}）'


def extract_tracks(task: dict) -> list[dict]:
    """取出任务结果里的所有音轨：[{'name', 'url', 'license_id'}]，主音轨在前。
    附加音轨（如人声压低版）字段可能随接口演进，做成 schema 宽容：
    凡带 url 的对象都收，license_id 有就带上。"""
    tracks: list[dict] = []

    def add(name: str, item) -> None:
        if isinstance(item, dict) and isinstance(item.get('url'), str) and item['url']:
            tracks.append({'name': name, 'url': item['url'], 'license_id': item.get('license_id')})

    add('audio', task.get('audio'))
    for key, val in task.items():
        if key == 'audio':
            continue
        if isinstance(val, dict):
            add(key, val)
        elif isinstance(val, list):
            for i, item in enumerate(val):
                add(f'{key}_{i + 1}', item)
    return tracks


def download_url(url: str) -> bytes:
    """下载结果音频。结果地址是预签名 URL、自带鉴权 ——
    绝不能把 API Key 发给存储域名，这里不带任何鉴权头。"""
    status, body = _http('GET', url)
    if status >= 400:
        raise SoniloError(f'结果下载失败 (HTTP {status})')
    if not body:
        raise SoniloError('结果音频为空')
    return body


def _ext_from_url(url: str, default: str = '.m4a') -> str:
    path_part = url.split('?', 1)[0]
    ext = os.path.splitext(path_part)[1].lower()
    return ext if ext in ('.m4a', '.wav', '.mp3', '.aac', '.flac', '.mp4') else default


def save_results(task: dict, task_id: str, label: str, out_base: Path) -> list[Path]:
    """下载全部音轨 + 写授权留档 JSON。out_base 形如 <目录>/<视频名去后缀>。
    返回落盘文件列表（音轨在前，授权 JSON 在最后）。"""
    tracks = extract_tracks(task)
    if not tracks:
        raise SoniloError(f'任务成功但没有音轨结果 (task_id: {task_id})')

    saved: list[Path] = []
    license_entries = []
    for i, t in enumerate(tracks):
        suffix = '' if t['name'] == 'audio' else f'_{t["name"]}'
        dest = out_base.parent / f'{out_base.name}_{label}{suffix}{_ext_from_url(t["url"])}'
        dest.write_bytes(download_url(t['url']))
        saved.append(dest)
        license_entries.append({
            '文件': dest.name,
            '音轨': t['name'],
            'license_id': t['license_id'],
        })

    license_path = out_base.parent / f'{out_base.name}_{label}_授权.json'
    license_path.write_text(
        json.dumps({
            'task_id': task_id,
            '生成时间': time.strftime('%Y-%m-%d %H:%M:%S'),
            '音轨': license_entries,
            '原始结果': task,  # 完整留档，license_id / 结果字段以此为准
        }, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    saved.append(license_path)
    return saved


def run_generate(args) -> None:
    video = Path(args.video).resolve()
    if not video.is_file():
        print(f'❌ 视频文件不存在: {video}')
        sys.exit(1)

    kind = 'sfx' if args.sfx else 'music'
    label = '音效' if args.sfx else '配乐'
    cap = SFX_MAX_SECONDS if args.sfx else MUSIC_MAX_SECONDS

    # segments 只对音效有意义
    segments = None
    if args.segments:
        if not args.sfx:
            print('❌ --segments 只配合 --sfx 使用（配乐用 --prompt 描述结构即可）')
            sys.exit(1)
        seg_path = Path(args.segments)
        if not seg_path.is_file():
            print(f'❌ 分段文件不存在: {seg_path}')
            sys.exit(1)
        try:
            segments = json.loads(seg_path.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, ValueError) as e:
            print(f'❌ 分段文件不是合法 JSON: {e}')
            sys.exit(1)
        errs = validate_segments(segments)
        if errs:
            print('❌ segments 预检不通过（规则见 references/sonilo-audio-guide.md）:')
            for e in errs:
                print(f'  - {e}')
            sys.exit(1)

    # 时长预检（尽力而为）：超上限没必要白传一遍大文件
    duration = probe_duration(video)
    if duration and duration > cap:
        print(f'❌ 视频 {duration:.1f}s 超过{label}接口上限 {cap}s')
        if args.sfx:
            print('  两个办法：')
            print('  1. 对关键段单跑（视频段/段XX.mp4，每段 4-10s）—— 推荐，按秒计费也更省')
            print('  2. 剪映里导出 ≤8 分钟的段落再跑')
        else:
            print('  剪映里把初剪切到 6 分钟以内再导出')
        sys.exit(1)
    if not duration:
        print('  ⚠ 未找到 ffprobe，跳过本地时长预检（超上限会被接口拒绝，不扣费）')

    size_mb = video.stat().st_size / 1024 / 1024
    if size_mb > UPLOAD_SIZE_WARN_MB:
        print(f'  ⚠ 文件 {size_mb:.0f} MB，可能超上传体积上限被拒（413）；剪映导出用 1080p / 中码率可减小体积')

    out_base = (Path(args.output_dir).resolve() if args.output_dir else video.parent) / video.stem

    print(f'\n=== Sonilo {label}（video-to-{ "sfx" if args.sfx else "music" }）===')
    print(f'  视频: {video.name}（{duration:.1f}s / {size_mb:.1f} MB）' if duration
          else f'  视频: {video.name}（{size_mb:.1f} MB）')
    print(f'  风格提示: {args.prompt}' if args.prompt else '  风格提示: 无（完全按画面生成）')
    if segments:
        print(f'  分段: {len(segments)} 段（本地预检通过）')
    print('  计费: 按视频秒数计费，生成失败自动退款')

    try:
        get_api_key()  # 先验 Key，别传完文件才报错
        print('📤 上传并提交任务...', flush=True)
        task_id = submit_task(video, kind, args.prompt.strip(), segments)
        print(f'  ✓ task_id={task_id}（受理即计费；中断可 --resume 找回）', flush=True)
        print(f'⏳ 等待生成（每 {POLL_INTERVAL_SECONDS}s 查询一次，上限 {args.timeout:.0f}s）...', flush=True)
        t0 = time.monotonic()
        task = poll_task(task_id, args.timeout)
        print(f'  ✓ 生成完成（{time.monotonic() - t0:.0f}s）', flush=True)
        saved = save_results(task, task_id, label, out_base)
    except SoniloError as e:
        print(f'❌ {e}')
        sys.exit(1)

    for f in saved[:-1]:
        print(f'  ✓ {f.name} 落盘（{f.stat().st_size / 1024 / 1024:.1f} MB）')
    print(f'  ✓ 授权留档: {saved[-1].name}（含每条音轨的 license_id，商用留档用）')
    if args.sfx:
        print(f'🎬 下一步: 把{label}导回剪映音效轨，对齐该段起点')
    else:
        print(f'🎬 下一步: 把{label}导回剪映当 BGM 轨（有配音的成片，人声处音乐会尽力自动压低）')


def run_resume(args) -> None:
    task_id = args.resume
    out_dir = Path(args.output_dir).resolve() if args.output_dir else Path.cwd()
    out_base = out_dir / f'sonilo_{task_id[:8]}'
    print(f'\n=== 找回任务 {task_id} ===')
    try:
        print(f'⏳ 查询任务状态（上限 {args.timeout:.0f}s）...', flush=True)
        task = poll_task(task_id, args.timeout)
        saved = save_results(task, task_id, '音频', out_base)
    except SoniloError as e:
        print(f'❌ {e}')
        sys.exit(1)
    for f in saved[:-1]:
        print(f'  ✓ {f.name} 落盘（{f.stat().st_size / 1024 / 1024:.1f} MB）')
    print(f'  ✓ 授权留档: {saved[-1].name}')


# ---------- 离线自检（--self-test，不联网、不扣费） ----------


def run_self_test() -> None:
    import tempfile

    global _http, _sleep
    real_http, real_sleep = _http, _sleep
    real_key = os.environ.get('SONILO_API_KEY')
    passed = 0

    def ok(name: str) -> None:
        nonlocal passed
        passed += 1
        print(f'  ✓ {name}')

    try:
        _sleep = lambda _s: None  # noqa: E731

        # 1. segments 预检：合法样例通过
        good = [
            {'start': 0, 'end': 1.5, 'prompt': '皮鞋踩过散落玻璃碴'},
            {'start': 1.5, 'end': 3, 'prompt': '木门被一脚踹开，门框断裂'},
        ]
        assert validate_segments(good) == []
        ok('segments 合法样例通过')

        # 2. segments 预检：抓出首段非 0 / 不相接 / 空 prompt / 超长 prompt
        bad = [
            {'start': 1, 'end': 2, 'prompt': ''},
            {'start': 3, 'end': 2.5, 'prompt': 'x' * 201},
        ]
        errs = validate_segments(bad)
        assert any('第 1 段 start' in e for e in errs)
        assert any('首尾相接' in e for e in errs)
        assert any('不能为空' in e for e in errs)
        assert any('200 字符' in e for e in errs)
        assert any('大于 start' in e for e in errs)
        ok('segments 非法样例全部抓出')

        # 3. segments 预检：超 30 段
        many = [{'start': i, 'end': i + 1, 'prompt': 'p'} for i in range(31)]
        assert any('最多 30 段' in e for e in validate_segments(many))
        ok('segments 超 30 段抓出')

        # 4. multipart 编码：含字段、文件名、文件内容
        with tempfile.TemporaryDirectory() as td:
            fake = Path(td) / '初剪.mp4'
            fake.write_bytes(b'fake-video-bytes')
            body, ctype = encode_multipart({'prompt': '国风悬疑', 'mode': 'async'}, 'video', fake)
            assert ctype.startswith('multipart/form-data; boundary=')
            assert '国风悬疑'.encode('utf-8') in body
            assert b'name="mode"' in body and b'async' in body
            assert '初剪.mp4'.encode('utf-8') in body
            assert b'fake-video-bytes' in body
            ok('multipart 编码正确')

            # 5. 提交任务：解析 task_id + 带 Bearer 头
            calls = []

            def fake_http(method, url, headers=None, body=None, timeout=None):
                calls.append({'method': method, 'url': url, 'headers': headers or {}})
                if url.endswith('/v1/video-to-music'):
                    return 202, json.dumps({'task_id': 'task-abc'}).encode()
                raise AssertionError(f'意外请求: {url}')

            _http = fake_http
            os.environ['SONILO_API_KEY'] = 'sk-selftest'
            tid = submit_task(fake, 'music', '国风悬疑', None)
            assert tid == 'task-abc'
            assert calls[0]['headers']['Authorization'] == 'Bearer sk-selftest'
            ok('提交任务返回 task_id')

            # 6. 轮询：processing → succeeded
            seq = [
                (200, json.dumps({'status': 'processing'}).encode()),
                (200, json.dumps({'status': 'succeeded',
                                  'audio': {'url': 'https://cdn.example/x.m4a',
                                            'license_id': 'lic-1'}}).encode()),
            ]
            _http = lambda *a, **k: seq.pop(0)  # noqa: E731
            task = poll_task('task-abc', timeout=60)
            assert task['status'] == 'succeeded'
            ok('轮询到 succeeded')

            # 7. 轮询：failed 带 task_id + 退款说明
            _http = lambda *a, **k: (200, json.dumps({  # noqa: E731
                'status': 'failed', 'error': {'message': 'boom'}, 'refunded': True}).encode())
            try:
                poll_task('task-abc', timeout=60)
                raise AssertionError('failed 状态应抛错')
            except SoniloError as e:
                assert 'task-abc' in str(e) and 'boom' in str(e) and '退还' in str(e)
            ok('failed 状态报错含 task_id + 退款说明')

            # 8. 音轨提取：主音轨 + 附加音轨 + license_id
            tracks = extract_tracks({
                'status': 'succeeded',
                'audio': {'url': 'https://cdn.example/a.m4a', 'license_id': 'lic-a'},
                'ducked': [{'url': 'https://cdn.example/b.m4a', 'license_id': 'lic-b'}],
            })
            assert tracks[0] == {'name': 'audio', 'url': 'https://cdn.example/a.m4a', 'license_id': 'lic-a'}
            assert {'name': 'ducked_1', 'url': 'https://cdn.example/b.m4a', 'license_id': 'lic-b'} in tracks
            ok('音轨提取含 license_id（附加音轨宽容处理）')

            # 9. 结果下载：预签名 URL 不带鉴权头
            dl_calls = []

            def fake_dl(method, url, headers=None, body=None, timeout=None):
                dl_calls.append(headers or {})
                return 200, b'audio-bytes'

            _http = fake_dl
            assert download_url('https://cdn.example/a.m4a') == b'audio-bytes'
            assert 'Authorization' not in dl_calls[0]
            ok('预签名 URL 下载不带 API Key')

            # 10. 落盘：音轨文件 + 授权 JSON
            out_base = Path(td) / '初剪'
            saved = save_results(
                {'audio': {'url': 'https://cdn.example/a.m4a', 'license_id': 'lic-a'}},
                'task-abc', '配乐', out_base)
            assert saved[0].name == '初剪_配乐.m4a' and saved[0].read_bytes() == b'audio-bytes'
            record = json.loads(saved[-1].read_text(encoding='utf-8'))
            assert record['task_id'] == 'task-abc'
            assert record['音轨'][0]['license_id'] == 'lic-a'
            ok('落盘含授权 JSON（license_id 留档）')

            # 11. HTTP 错误映射
            assert '余额不足' in http_error_message(402, b'{"detail": "no credits"}')
            assert 'API Key' in http_error_message(401, b'')
            assert 'segments' in http_error_message(422, b'{"message": "bad segments"}')
            ok('HTTP 错误信息映射')

    finally:
        _http, _sleep = real_http, real_sleep
        if real_key is None:
            os.environ.pop('SONILO_API_KEY', None)
        else:
            os.environ['SONILO_API_KEY'] = real_key

    print(f'\n✅ 自检通过（{passed}/11 项，全程未联网、未扣费）')


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Sonilo 配乐 / 音效生成（阶段 4.D 可选自动化）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='示例见 references/sonilo-audio-guide.md',
    )
    parser.add_argument('video', nargs='?', help='视频文件（整集初剪 MP4，或 视频段/段XX.mp4）')
    parser.add_argument('--sfx', action='store_true', help='生成音效（默认生成配乐）')
    parser.add_argument('--prompt', default='', help='可选风格提示，留空完全按画面生成')
    parser.add_argument('--segments', help='音效分段 JSON 文件（仅 --sfx）')
    parser.add_argument('--output-dir', help='输出目录（默认视频同目录）')
    parser.add_argument('--timeout', type=float, default=DEFAULT_TIMEOUT_SECONDS,
                        help=f'等待生成上限秒数（默认 {DEFAULT_TIMEOUT_SECONDS}）')
    parser.add_argument('--resume', metavar='TASK_ID', help='找回超时/中断的任务')
    parser.add_argument('--self-test', action='store_true', help='离线自检（不联网、不扣费）')
    args = parser.parse_args()

    if args.self_test:
        run_self_test()
        return
    if args.resume:
        run_resume(args)
        return
    if not args.video:
        parser.print_help()
        sys.exit(1)
    run_generate(args)


if __name__ == '__main__':
    main()
