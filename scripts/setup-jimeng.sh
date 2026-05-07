#!/usr/bin/env bash
# setup-jimeng.sh
# 一键安装 + 登录 + 自检 dreamina CLI
# 用法：bash scripts/setup-jimeng.sh

set -e

echo "==============================================="
echo "  dreamina CLI 安装 + 登录引导"
echo "==============================================="
echo ""

# 检查 curl
if ! command -v curl &> /dev/null; then
    echo "❌ curl 未安装。Mac/Linux 请装 curl，Windows 请确保使用 Git Bash。"
    exit 1
fi

# 1. 检查是否已装
if command -v dreamina &> /dev/null; then
    DREAMINA_VERSION=$(dreamina --version 2>&1 || echo "unknown")
    echo "✅ dreamina CLI 已安装：$DREAMINA_VERSION"
    echo ""
else
    echo "⏳ dreamina CLI 未安装，开始安装..."
    echo ""
    curl -fsSL https://jimeng.jianying.com/cli | bash
    echo ""

    # 检查 PATH
    if ! command -v dreamina &> /dev/null; then
        echo "⚠️ 安装完成但 dreamina 不在 PATH。请将以下路径加入 PATH："
        echo "    export PATH=\"\$HOME/.dreamina_cli/bin:\$PATH\""
        echo ""
        echo "    Windows Git Bash 把这行加到 ~/.bashrc 或 ~/.bash_profile"
        echo "    然后 source ~/.bashrc 或重开 Git Bash"
        exit 1
    fi

    echo "✅ dreamina CLI 安装成功：$(dreamina --version)"
    echo ""
fi

# 2. 检查登录态
echo "⏳ 检查登录态..."
if dreamina user_credit > /tmp/dreamina_credit_check.json 2>&1; then
    echo "✅ 已登录"
    echo "余额信息："
    cat /tmp/dreamina_credit_check.json
    rm -f /tmp/dreamina_credit_check.json
else
    echo "⏳ 未登录，启动登录流程..."
    echo ""
    echo "下一步：运行 'dreamina login' 在浏览器完成授权。"
    echo "如果浏览器没自动拉起，用 'dreamina login --debug' 看回调地址。"
    echo ""
    read -p "现在执行 dreamina login？(y/N) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        dreamina login
        echo ""
        echo "✅ 登录完成。再次检查余额："
        dreamina user_credit
    else
        echo "已跳过。请手动跑 dreamina login 后再继续。"
        exit 0
    fi
fi

echo ""
echo "==============================================="
echo "  ✅ 全部就绪。可以开始用 skill 生 ref 图 / 视频。"
echo "==============================================="
echo ""
echo "下一步建议："
echo "  - 在 Claude Code 里调 ai-short-drama skill"
echo "  - skill 阶段 3.5 自动调 dreamina text2image 生 ref 图"
echo "  - skill 阶段 4.C 自动调 dreamina image2video 生分集视频"
echo ""
