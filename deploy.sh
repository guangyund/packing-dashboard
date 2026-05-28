#!/bin/bash
# ============================================================
# dashboard 部署脚本（FastAPI backend + Vue3 frontend）
# 用法：
#   ./deploy.sh           # 部署最新 tag
#   ./deploy.sh v1.0.1    # 部署指定 tag
# ============================================================
set -e

PROJECT_DIR="/opt/dashboard"
BACKEND_SERVICE="dashboard"     # systemctl 服务名，按实际改
FRONTEND_DIR="$PROJECT_DIR/frontend"

cd "$PROJECT_DIR"

# ── 拉取最新代码和标签 ──────────────────────────────────────
echo "📦 拉取最新代码..."
git fetch --tags origin

# 确定目标版本
if [ -n "$1" ]; then
    TARGET="$1"
else
    TARGET=$(git tag --sort=-version:refname | head -1)
fi

CURRENT=$(git describe --tags --abbrev=0 2>/dev/null || echo "无")
echo "当前版本：$CURRENT  →  目标版本：$TARGET"

# ── 切换版本 ────────────────────────────────────────────────
git checkout "$TARGET"

# ── 后端：更新依赖 ───────────────────────────────────────────
echo "📥 更新 Python 依赖..."
pip install -r backend/requirements.txt -q 2>/dev/null || true

# ── 前端：构建 ──────────────────────────────────────────────
echo "🔨 构建前端..."
cd "$FRONTEND_DIR"
npm install --silent
npm run build
cd "$PROJECT_DIR"

# ── 重启后端服务 ─────────────────────────────────────────────
echo "🔄 重启服务 $BACKEND_SERVICE ..."
sudo systemctl restart "$BACKEND_SERVICE"
sleep 2
sudo systemctl status "$BACKEND_SERVICE" --no-pager -l

echo ""
echo "✅ 部署完成：$TARGET"
