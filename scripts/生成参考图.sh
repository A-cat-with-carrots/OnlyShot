#!/usr/bin/env bash
# 生成参考图.sh v0.1.3
# 改进：
#  1. 自动从 02_IP简报.md 提取视觉指纹追加到每个 prompt（视觉一致性）
#  2. 不依赖 dreamina query_result 的 exit code，直接看文件落盘
#  3. 文件落盘后按 <name>_ref.png 重命名
#
# 用法：bash 生成参考图.sh <项目目录>

set -e

if [ -z "$1" ]; then
    echo "用法：bash 生成参考图.sh <项目目录>"
    exit 1
fi

PROJECT_DIR="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXTRACTOR="$SCRIPT_DIR/extract_prompts.py"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ 项目目录不存在：$PROJECT_DIR"
    exit 1
fi

if [ ! -f "$EXTRACTOR" ]; then
    echo "❌ extract_prompts.py 不存在：$EXTRACTOR"
    exit 1
fi

if ! command -v dreamina &> /dev/null; then
    echo "❌ dreamina CLI 未装。先跑 setup-jimeng.sh"
    exit 1
fi

# 优先 python（避免 Windows MS Store python3 stub 静默失败）
PYTHON_CMD=$(command -v python || command -v python3)
if ! "$PYTHON_CMD" -c "print('ok')" >/dev/null 2>&1; then
    echo "❌ python 解释器无效（可能是 Microsoft Store stub）：$PYTHON_CMD"
    exit 1
fi

if ! dreamina user_credit > /dev/null 2>&1; then
    echo "❌ dreamina 未登录"
    exit 1
fi

# 提取 IP 视觉指纹（02_IP简报.md）— v0.1.3 新增
IP_BRIEF="$PROJECT_DIR/02_IP简报.md"
VISUAL_FINGERPRINT=""
if [ -f "$IP_BRIEF" ]; then
    VISUAL_FINGERPRINT=$("$PYTHON_CMD" "$EXTRACTOR" --fingerprint "$IP_BRIEF" 2>/dev/null)
fi

if [ -z "$VISUAL_FINGERPRINT" ]; then
    echo "⚠️ 未在 02_IP简报.md 找到视觉指纹段。所有 prompt 不会自动 append 风格词，可能导致风格漂移。"
    echo "   建议：在 02_IP简报.md 顶部加「视觉指纹」段（含 \`\`\` 代码块）"
    echo ""
fi

echo "==============================================="
echo "  批量生成 ref 图（v0.1.3，自动追加视觉指纹）"
echo "  项目：$PROJECT_DIR"
echo "==============================================="
if [ -n "$VISUAL_FINGERPRINT" ]; then
    echo ""
    echo "📐 视觉指纹（自动 append 到每个 prompt 末尾）："
    echo "   ${VISUAL_FINGERPRINT:0:120}..."
fi
echo ""

mkdir -p "$PROJECT_DIR/ref图/角色"
mkdir -p "$PROJECT_DIR/ref图/场景"
mkdir -p "$PROJECT_DIR/ref图/道具"

# 单图生成（v0.1.3 — 不依赖 exit code，直接看文件落盘）
generate_one_image() {
    local name="$1"          # 输出文件名（含 .png）
    local prompt="$2"        # 提示词
    local ratio="$3"         # 9:16 / 16:9 / 1:1
    local out_dir="$4"       # 落盘目录
    local out_path="$out_dir/$name"

    if [ -f "$out_path" ]; then
        echo "  ✅ 已存在：$name（跳过；如要重生删除该文件）"
        return 0
    fi

    # append 视觉指纹
    local full_prompt="$prompt"
    if [ -n "$VISUAL_FINGERPRINT" ]; then
        full_prompt="$prompt. $VISUAL_FINGERPRINT"
    fi

    echo "  ⏳ 生成 $name（ratio=$ratio）..."

    # 1. 提交 + 等任务完成
    local submit_json
    submit_json=$(dreamina text2image \
        --prompt="$full_prompt" \
        --ratio="$ratio" \
        --resolution_type=2k \
        --poll=180 2>&1) || {
        echo "  ❌ text2image 提交失败"
        echo "$submit_json" | head -5
        return 1
    }

    # 2. 提取 submit_id
    local submit_id
    submit_id=$(echo "$submit_json" | grep -oE '"submit_id"\s*:\s*"[^"]+"' | head -1 | grep -oE '"[^"]+"$' | tr -d '"')

    if [ -z "$submit_id" ]; then
        echo "  ❌ 没拿到 submit_id"
        return 1
    fi

    # 3. 触发下载（去掉 --poll，因为 text2image 阶段已完成；--poll 会导致下载行为异常）
    dreamina query_result \
        --submit_id="$submit_id" \
        --download_dir="$out_dir" > /dev/null 2>&1 || true

    # 4. 看文件是否落盘（dreamina 默认命名：<submit_id>_image_*.png）
    local downloaded
    downloaded=$(ls "$out_dir/${submit_id}"_image_*.png 2>/dev/null | head -1)

    if [ -n "$downloaded" ] && [ -f "$downloaded" ]; then
        # 重命名到目标文件名
        mv "$downloaded" "$out_path"
        echo "  ✅ 落盘：$name"
        return 0
    else
        # 兜底：找最新 png 重命名（如果命名规则变化）
        local latest
        latest=$(ls -t "$out_dir"/*.png 2>/dev/null | head -1)
        if [ -n "$latest" ] && [ -f "$latest" ]; then
            # 检查是否是孤儿（不在已知 ref 名单里）
            local basename
            basename=$(basename "$latest")
            if [[ "$basename" != *"_ref.png" ]] && [[ "$basename" != "$name" ]]; then
                mv "$latest" "$out_path"
                echo "  ✅ 落盘（兜底重命名）：$name"
                return 0
            fi
        fi
        echo "  ❌ 下载失败：$name (submit_id=$submit_id)"
        echo "     建议手动跑：dreamina query_result --submit_id=$submit_id --download_dir=$out_dir"
        return 1
    fi
}

extract_and_run() {
    local md_file="$1"
    local section="$2"
    local ratio="$3"
    local out_dir="$4"

    if [ ! -f "$md_file" ]; then
        echo "⚠️ 文件不存在：$md_file"
        return
    fi

    "$PYTHON_CMD" "$EXTRACTOR" "$md_file" "$section" \
    | while IFS=$'\t' read -r name prompt; do
        if [ -z "$name" ] || [ -z "$prompt" ]; then continue; fi
        generate_one_image "$name" "$prompt" "$ratio" "$out_dir" || true
    done
}

# === 角色 ref ===
echo "📍 第 1 步：生成角色 ref 图（9:16）..."
extract_and_run "$PROJECT_DIR/05_角色圣经.md" "即梦角色参考图生成包" "9:16" "$PROJECT_DIR/ref图/角色"

# === 场景 ref ===
echo ""
echo "📍 第 2 步：生成场景 ref 图（16:9）..."
extract_and_run "$PROJECT_DIR/06_场景圣经.md" "即梦场景参考图生成包" "16:9" "$PROJECT_DIR/ref图/场景"

# === 道具 ref ===
echo ""
echo "📍 第 3 步：生成道具 ref 图（1:1）..."
extract_and_run "$PROJECT_DIR/07_道具圣经.md" "即梦道具参考图生成包" "1:1" "$PROJECT_DIR/ref图/道具"

echo ""
echo "==============================================="
echo "  ✅ ref 图生成完成（v0.1.3）"
echo "==============================================="

CHAR_COUNT=$(find "$PROJECT_DIR/ref图/角色" -name "*.png" 2>/dev/null | wc -l)
SCENE_COUNT=$(find "$PROJECT_DIR/ref图/场景" -name "*.png" 2>/dev/null | wc -l)
PROP_COUNT=$(find "$PROJECT_DIR/ref图/道具" -name "*.png" 2>/dev/null | wc -l)

echo "📊 落盘统计："
echo "   角色：$CHAR_COUNT 张"
echo "   场景：$SCENE_COUNT 张"
echo "   道具：$PROP_COUNT 张"
echo ""
echo "下一步：用户检验 ref 图风格一致性。"
echo "  - 风格漂移（真人 / 写实 / 偏离 manhua）→ 删该 png + 改 02_IP简报.md 视觉指纹 + 重跑"
echo "  - 全部一致 → 进 Phase 2 出片"
