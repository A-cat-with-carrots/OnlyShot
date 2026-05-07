#!/usr/bin/env bash
# 生成分集视频.sh v0.1.5
# 改进（v0.1.5）：
#  1. 切换 multimodal2video（全能参考）替代 image2video — 多 ref 输入，角色一致性最稳
#  2. seedance2.0fast_vip 旗舰模型（user maestro vip）
#  3. 5s 默认（multimodal 最低 4s）
#  4. 9:16 强制
#  5. 自动从每段 prompt 提取所有 (@xxx_ref.png) 引用 → 全传入 --image stringArray（最多 9 张）
#
# 用法：bash 生成分集视频.sh <项目目录> <集编号>

set -e

if [ -z "$2" ]; then
    echo "用法：bash 生成分集视频.sh <项目目录> <集编号> [段数上限]"
    echo "  段数上限可选 - 不传则全跑，传数字则只跑前 N 段（B 试水模式）"
    exit 1
fi

PROJECT_DIR="$1"
EP_NUM=$(printf "%02d" "$2")
LIMIT="${3:-0}"  # 0 = 全跑
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXTRACTOR="$SCRIPT_DIR/extract_prompts.py"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ 项目目录不存在：$PROJECT_DIR"
    exit 1
fi

EP_DIR=$(find "$PROJECT_DIR/分集" -maxdepth 1 -type d -name "第${EP_NUM}集_*" | head -1)
if [ -z "$EP_DIR" ] || [ ! -d "$EP_DIR" ]; then
    echo "❌ 第 ${EP_NUM} 集目录未找到"
    exit 1
fi

BATCH_FILE="$EP_DIR/即梦批量包.md"
VIDEO_DIR="$EP_DIR/视频段"
FAIL_LOG="$EP_DIR/失败段.log"

if [ ! -f "$BATCH_FILE" ]; then
    echo "❌ 即梦批量包.md 未找到"
    exit 1
fi

if ! command -v dreamina &> /dev/null; then
    echo "❌ dreamina CLI 未装"
    exit 1
fi

PYTHON_CMD=$(command -v python || command -v python3)
if ! "$PYTHON_CMD" -c "print('ok')" >/dev/null 2>&1; then
    echo "❌ python 解释器无效"
    exit 1
fi

if ! dreamina user_credit > /dev/null 2>&1; then
    echo "❌ dreamina 未登录"
    exit 1
fi

# 提取 IP 视觉指纹
IP_BRIEF="$PROJECT_DIR/02_IP简报.md"
VISUAL_FINGERPRINT=""
if [ -f "$IP_BRIEF" ]; then
    VISUAL_FINGERPRINT=$("$PYTHON_CMD" "$EXTRACTOR" --fingerprint "$IP_BRIEF" 2>/dev/null)
fi

mkdir -p "$VIDEO_DIR"
> "$FAIL_LOG"

echo "==============================================="
echo "  生成第 ${EP_NUM} 集视频（v0.1.6）"
echo "  模式：multimodal2video（全能参考）"
echo "  模型：seedance2.0fast_vip"
echo "  集目录：$EP_DIR"
if [ "$LIMIT" -gt 0 ]; then
    echo "  ⚠️ B 试水模式：只跑前 $LIMIT 段"
fi
echo "==============================================="
if [ -n "$VISUAL_FINGERPRINT" ]; then
    echo ""
    echo "📐 视觉指纹（自动 append）："
    echo "   ${VISUAL_FINGERPRINT:0:100}..."
fi
echo ""
echo "💰 当前余额："
dreamina user_credit
echo ""

# 解析 即梦批量包.md（v0.1.5+ 支持变速：从「### 段 N（X-Ys / **Ds**）」提取 D）
extract_segments() {
    local file="$1"
    awk '
        /^### 段 [0-9]+/ {
            if (current_prompt != "") {
                print current_num "\t" current_dur "\t" current_prompt
            }
            # 提取段号（substr 字节切对 UTF-8 中文不安全 → 取整匹配段后 gsub 去非数字）
            if (match($0, /段 [0-9]+/)) {
                s = substr($0, RSTART, RLENGTH)
                gsub(/[^0-9]/, "", s)
                current_num = s
            }
            current_prompt = ""
            current_dur = "5"
            # 提取 **Ds** 时长（同样用整匹配 + gsub 数字）
            if (match($0, /\*\*[0-9]+s\*\*/)) {
                d = substr($0, RSTART, RLENGTH)
                gsub(/[^0-9]/, "", d)
                current_dur = d
            }
            in_prompt_block = 0
            next
        }
        /^> / && current_num != "" {
            sub(/^> /, "")
            if (current_prompt == "") current_prompt = $0
            else current_prompt = current_prompt " " $0
            in_prompt_block = 1
            next
        }
        /^---/ && in_prompt_block {
            print current_num "\t" current_dur "\t" current_prompt
            current_num = ""
            current_prompt = ""
            current_dur = "5"
            in_prompt_block = 0
        }
        END {
            if (current_prompt != "") print current_num "\t" current_dur "\t" current_prompt
        }
    ' "$file"
}

# 从 prompt 提取所有 (@xxx_ref.png) 引用 → 返回找到的本地文件路径列表（最多 9 张）
collect_refs() {
    local prompt="$1"
    # 提取 @xxx_ref.png（去 @ + 去 .png 前缀的括号）
    local refs
    refs=$(echo "$prompt" | grep -oE '@[^[:space:]),]+_ref\.png' | tr -d '@' | sort -u)
    local found_paths=""
    local count=0
    for ref_name in $refs; do
        if [ "$count" -ge 9 ]; then break; fi
        # 优先角色，再场景，再道具
        for sub in 角色 场景 道具; do
            if [ -f "$PROJECT_DIR/ref图/$sub/$ref_name" ]; then
                found_paths+="--image=$PROJECT_DIR/ref图/$sub/$ref_name "
                count=$((count + 1))
                break
            fi
        done
    done
    echo "$found_paths"
}

generate_one_segment() {
    local seg_num="$1"
    local duration="$2"
    local prompt="$3"
    local out_file="$VIDEO_DIR/段$(printf "%02d" "$seg_num").mp4"

    if [ -f "$out_file" ]; then
        echo "  ✅ 段 $seg_num 已存在（跳过）"
        return 0
    fi

    # 收集所有 ref
    local ref_args
    ref_args=$(collect_refs "$prompt")
    if [ -z "$ref_args" ]; then
        echo "  ❌ 段 $seg_num 找不到任何 ref 图"
        echo "段 $seg_num: no ref" >> "$FAIL_LOG"
        return 1
    fi

    # append 视觉指纹
    local full_prompt="$prompt"
    if [ -n "$VISUAL_FINGERPRINT" ]; then
        full_prompt="$prompt. $VISUAL_FINGERPRINT"
    fi

    local ref_count
    ref_count=$(echo "$ref_args" | grep -oE '\-\-image=' | wc -l)
    echo "  ⏳ 段 $seg_num（refs=$ref_count, ${duration}s）..."

    # 1. multimodal2video 提交（duration 按变速时长）
    local submit_json
    submit_json=$(eval "dreamina multimodal2video \
        $ref_args \
        --prompt='$full_prompt' \
        --duration=$duration \
        --ratio=9:16 \
        --video_resolution=720p \
        --model_version=seedance2.0fast_vip \
        --poll=300 2>&1") || {
        echo "  ❌ 段 $seg_num 提交失败"
        echo "段 $seg_num: submit failed - $(echo "$submit_json" | head -3)" >> "$FAIL_LOG"
        return 1
    }

    # 2. 提取 submit_id
    local submit_id
    submit_id=$(echo "$submit_json" | grep -oE '"submit_id"\s*:\s*"[^"]+"' | head -1 | grep -oE '"[^"]+"$' | tr -d '"')
    if [ -z "$submit_id" ]; then
        echo "  ❌ 段 $seg_num 没拿到 submit_id"
        echo "段 $seg_num: no submit_id - $(echo "$submit_json" | head -5)" >> "$FAIL_LOG"
        return 1
    fi

    # 3. 触发下载（不带 --poll，看文件落盘）
    dreamina query_result \
        --submit_id="$submit_id" \
        --download_dir="$VIDEO_DIR" > /dev/null 2>&1 || true

    # 4. 看文件落盘（dreamina 默认 <submit_id>_video_*.mp4）
    local downloaded
    downloaded=$(ls "$VIDEO_DIR/${submit_id}"_video_*.mp4 2>/dev/null | head -1)

    if [ -n "$downloaded" ] && [ -f "$downloaded" ]; then
        mv "$downloaded" "$out_file"
        echo "  ✅ 段 $seg_num 落盘"
        return 0
    else
        echo "  ❌ 段 $seg_num 下载失败 (submit_id=$submit_id)"
        echo "段 $seg_num: submit_id=$submit_id, prompt: $prompt" >> "$FAIL_LOG"
        return 1
    fi
}

RAN=0
extract_segments "$BATCH_FILE" | while IFS=$'\t' read -r seg_num duration prompt; do
    if [ -z "$seg_num" ] || [ -z "$prompt" ]; then continue; fi
    if [ -z "$duration" ]; then duration=5; fi
    if [ "$LIMIT" -gt 0 ] && [ "$RAN" -ge "$LIMIT" ]; then
        echo "  ⏹ 已达 LIMIT=$LIMIT 段，停止"
        break
    fi
    generate_one_segment "$seg_num" "$duration" "$prompt" || true
    RAN=$((RAN + 1))
done

# 汇总
TOTAL_OUT=$(ls "$VIDEO_DIR"/段*.mp4 2>/dev/null | wc -l)
FAIL_COUNT=$(grep -c '^段' "$FAIL_LOG" 2>/dev/null || echo 0)

echo ""
echo "==============================================="
echo "  第 ${EP_NUM} 集生成完成"
echo "==============================================="
echo "  成功落盘段数：$TOTAL_OUT"
echo "  失败段数：$FAIL_COUNT"
echo ""

if [ "$FAIL_COUNT" -gt 0 ]; then
    echo "失败段记录：$FAIL_LOG"
    echo "建议：手动改 prompt 后重跑（脚本已存在跳过）"
fi

echo ""
echo "下一步："
echo "  1. 在剪映新建 9:16 / 1080×1920 / 30fps 项目"
echo "  2. 按 段01.mp4 → 段XX.mp4 顺序导入"
echo "  3. 段间过渡叠化 0.3s（爽点段白闪 0.2s）"
echo "  4. 加配音 + BGM + 字幕（中文括号）+ AIGC 标识"
echo "  5. 输出 MP4 H.264 / 1080P"
