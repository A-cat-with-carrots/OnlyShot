#!/usr/bin/env python3
"""
extract_prompts.py — 从 skill 圣经 / IP 简报 提取 prompt。

模式 1：提取 ref prompt（圣经 markdown 末尾的「即梦 X 参考图生成包」段）
    用法：python extract_prompts.py <md 文件> <段标题>
    例：python extract_prompts.py 05_角色圣经.md "即梦角色参考图生成包"
    输出：每行 name<TAB>prompt

模式 2：提取视觉指纹（IP 简报里「视觉指纹」段下的 ``` 代码块）
    用法：python extract_prompts.py --fingerprint <02_IP简报.md>
    输出：单行视觉指纹字符串
"""

import sys
import re
from pathlib import Path

# 强制 stdout UTF-8（防 Windows GBK 截断）
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def extract_refs(md_path: Path, section_marker: str):
    """提取段下每个 ### <名>.png 的 > prompt 引用块。"""
    if not md_path.exists():
        print(f"❌ 文件不存在：{md_path}", file=sys.stderr)
        sys.exit(1)
    text = md_path.read_text(encoding="utf-8")
    section_pat = rf"##\s+{re.escape(section_marker)}.*?(?=^##\s|\Z)"
    m = re.search(section_pat, text, re.DOTALL | re.MULTILINE)
    if not m:
        print(f"⚠️ 段「{section_marker}」未找到", file=sys.stderr)
        return
    section_text = m.group(0)
    pattern = re.compile(
        r"^###\s+([^\n]+\.png)\s*\n"
        r"(?:[^\n]*\n)*?"
        r"^>\s*(.+?)(?=\n[^>\n]|\n\n|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    for match in pattern.finditer(section_text):
        name = match.group(1).strip()
        prompt = match.group(2).strip()
        prompt_lines = [line.lstrip("> ").rstrip() for line in prompt.split("\n")]
        prompt_clean = " ".join(line for line in prompt_lines if line.strip())
        print(f"{name}\t{prompt_clean}")


def extract_fingerprint(md_path: Path):
    """提取视觉指纹（02_IP简报.md「视觉指纹」段下第一个 ``` 代码块）。"""
    if not md_path.exists():
        print("", end='')
        return
    text = md_path.read_text(encoding="utf-8")
    # 找「视觉指纹」段
    section_pat = r"##\s+.*?视觉指纹.*?\n(.+?)(?=^##\s|\Z)"
    m = re.search(section_pat, text, re.DOTALL | re.MULTILINE)
    if not m:
        print("", end='')
        return
    section = m.group(1)
    # 提取第一个 ``` 代码块
    code_block = re.search(r"```\s*\n(.+?)\n```", section, re.DOTALL)
    if not code_block:
        print("", end='')
        return
    fingerprint = code_block.group(1).strip()
    # 折叠多行为单行（去换行 + 多空格压一）
    fingerprint = re.sub(r"\s+", " ", fingerprint)
    print(fingerprint, end='')


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--fingerprint":
        if len(sys.argv) < 3:
            print("用法：python extract_prompts.py --fingerprint <02_IP简报.md>", file=sys.stderr)
            sys.exit(1)
        extract_fingerprint(Path(sys.argv[2]))
    elif len(sys.argv) == 3:
        extract_refs(Path(sys.argv[1]), sys.argv[2])
    else:
        print("用法：", file=sys.stderr)
        print("  ref 模式：python extract_prompts.py <md 文件> <段标题>", file=sys.stderr)
        print("  指纹模式：python extract_prompts.py --fingerprint <02_IP简报.md>", file=sys.stderr)
        sys.exit(1)
