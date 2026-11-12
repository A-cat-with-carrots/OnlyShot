# OnlyShot: AI short drama pipeline for Claude Code

> One rough idea → market scan → script → storyboard → storyboard frames → video clips → auto rough cut → pre-release compliance check.
> Built for Chinese vertical short-drama platforms (Hongguo / Douyin), generating with Jimeng (Dreamina) and Seedance. · [中文](README.md)

[![Skill](https://img.shields.io/badge/Claude-Skill-blueviolet)](https://docs.anthropic.com/en/docs/claude-code)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)
[![Version](https://img.shields.io/badge/Version-v0.7.0-orange)](CHANGELOG.md)

https://github.com/user-attachments/assets/a9402992-87c8-4915-93d7-b781f6951587

## At a glance

- **What**: a Claude Code skill (skill name `ai-short-drama`). Give it one line of premise; it walks you through writing and producing a vertical short drama, and every step is saved as a file.
- **Why it is different**: it does not stop at the script. It drives the Dreamina CLI to actually generate reference images, storyboard frames and video clips. Storyboard frames come first, because fixing a frame costs about 3 credits and fixing a clip about 55. Seventeen Dreamina failure modes are documented with fixes. At the end it assembles a rough cut with subtitles and AI labels.
- **Cost**: at May 2026 prices, one 193-second episode is about 2,230 Dreamina credits (36 frames ≈ 108, clips ≈ 2,120). Run with `--dry-run` first to see the estimate for your episode without spending anything.
- **Works without Dreamina**: scripts, bibles, storyboards and per-shot prompts only need Claude Code (see "Light mode").
- **Compliance**: since 2026-09-01, Chinese rules require AI micro-dramas to carry an AI label in a visible position in every episode. `拼接初剪.py` adds a visible label and a metadata label. The checklist is in [`references/compliance-2026.md`](references/compliance-2026.md) (Chinese).

## Install

```bash
git clone https://github.com/A-cat-with-carrots/OnlyShot ~/.claude/skills/ai-short-drama
```

Restart Claude Code; the skill loads automatically. Update with `git pull`.

| Requirement | Used for | When |
|---|---|---|
| Claude Code | everything | always |
| Python 3.10+ | `scripts/` | generation, rough cut |
| Dreamina CLI | reference images, frames, clips | generation (not needed in light mode) |
| ffmpeg with libass | `拼接初剪.py` | rough cut |

Dreamina CLI: `curl -fsSL https://jimeng.jianying.com/cli | bash`, then `dreamina login` (OAuth device flow: open the printed URL and enter the code). Use the official URL only.

## Usage

In Claude Code, describe your premise, e.g. *"I want a short drama: a 996 programmer is reborn as Erlang Shen's celestial hound and unlocks an anti-PUA system."* The skill runs:

1. **Phase 1, writing**: market scan, IP brief, story architecture and beat map (7 hook points per episode), character / scene / prop bibles, reference images, self-critique.
2. **Phase 1.5, storyboard frames**: 1–4 candidate first frames per shot, picked before any video is generated.
3. **Phase 2, production** (per episode): video clips (4 modes chosen automatically), rough cut, optional music, edit, pre-release check.

```bash
python scripts/生成分镜图.py   <project> 01 --dry-run   # frames to generate, estimated credits, prompt length / sensitive-word checks
python scripts/生成分集视频.py <project> 01 --dry-run   # mode per shot, missing references, estimated credits
python scripts/生成分集视频.py <project> 01 5 --model-version seedance2.0fast   # without a Dreamina membership
python scripts/拼接初剪.py     <project> 01             # → 初剪.mp4: 1080×1920, burned-in subtitles, AI label, AIGC metadata
```

## Light mode (no Dreamina)

1. Go through Phase 1 with the skill; it only needs Claude Code.
2. After writing an episode's `分镜.json`, run `python scripts/派生分集文件.py 分集/第01集_<name>/分镜.json` to get `即梦批量包.md`, one ready-made prompt per shot.
3. Paste the prompts into the Dreamina web app (or another video model) and save the clips as `视频段/段01.mp4`, `段02.mp4`, ...
4. With ffmpeg installed, run `python scripts/拼接初剪.py <project> 01 --allow-missing` for a rough cut with subtitles and AI labels.

## Notes for international users

- The workflow, templates and references are written in Chinese and tuned for Chinese platforms. Claude can discuss them with you in English.
- Overseas apps (ReelShort, DramaBox, TikTok) have different formats and AI policies; check them yourself.
- The regulations in `compliance-2026.md` are Chinese (NRTA) rules, dated and sourced. They are not legal advice.
- Whether the Dreamina CLI works with international (CapCut Dreamina) accounts has not been verified.

## More

- Full Chinese README: [`README.md`](README.md)
- Changelog: [`CHANGELOG.md`](CHANGELOG.md)
- Contributing (including rules for third-party paid services): [`CONTRIBUTING.md`](CONTRIBUTING.md)
- License: MIT
