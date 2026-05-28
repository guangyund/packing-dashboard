#!/bin/bash
# ============================================================
# dashboard 回滚脚本
# 用法：
#   ./rollback.sh         # 交互式选择回滚版本
#   ./rollback.sh v1.0.0  # 直接回滚到指定 tag
# ============================================================
set -e

PROJECT_DIR="/opt/dashboard"
BACKEND_SERVICE="dashboard"
FRONTEND_DIR="$PROJECT_DIR/frontend"

cd "$PROJECT_DIR"
git fetch --tags origin

CURRENT=$(git describe --tags --abbrev=0 2>/dev/null || echo "未知")
echo "当前版本：$CURRENT"
echo ""
echo "可用历史版本："
git tag --sort=-version:refname | head -10

# 确定回滚目标
if [ -n "$1" ]; then
    TARGET="$1"
else
    echo ""
    read -p "请输入要回滚到的版本（如 v1.0.0）：" TARGET
fi

if [ -z "$TARGET" ]; then
    echo "❌ 未指定版本，取消回滚"
    exit 1
fi

echo ""
echo "⚠️  即将从 $CURRENT 回滚到 $TARGET，是否继续？(y/N)"
read -r CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    echo "已取消"
    exit 0
fi

# ── 切换版本 ────────────────────────────────────────────────
git checkout "$TARGET"

# ── 前端：重新构建旧版本 ─────────────────────────────────────
echo "🔨 构建前端旧版本..."
cd "$FRONTEND_DIR"
npm install --silent
npm run build
cd "$PROJECT_DIR"

# ── 重启服务 ────────────────────────────────────────────────
echo "🔄 重启服务 $BACKEND_SERVICE ..."
sudo systemctl restart "$BACKEND_SERVICE"
sleep 2
sudo systemctl status "$BACKEND_SERVICE" --no-pager -l

echo ""
echo "✅ 已回滚到：$TARGET"
