#!/bin/bash
# ========================================
#  打印机耗材管理系统 — macOS/Linux 一键安装
#  用法: chmod +x install.sh && ./install.sh
# ========================================
set -e
cd "$(dirname "$0")"
INSTALL_DIR="$(pwd)"

echo "=========================================="
echo "   🖨️  打印机耗材管理系统 — 安装程序"
echo "=========================================="

# 检查 Python
if ! command -v python3 &>/dev/null; then
    echo "❌ 未找到 Python3，请先安装 Python 3.8+"
    echo "   macOS: brew install python3"
    echo "   或下载: https://www.python.org/downloads/"
    exit 1
fi
echo "✅ Python: $(python3 --version)"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 安装依赖
echo "📦 安装依赖包..."
source venv/bin/activate
pip install -r backend/requirements.txt -q
echo "✅ 依赖安装完成"

# 创建启动器
cat > "$INSTALL_DIR/启动服务.command" << 'STARTUP'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
IP=$(ipconfig getifaddr en0 2>/dev/null || hostname -I 2>/dev/null | awk "{print $1}" || echo "localhost")
echo ""
echo "=========================================="
echo "  🖨️  打印机耗材管理系统"
echo "  本机访问: http://localhost:8000/static/login.html"
echo "  局域网内: http://$IP:8000/static/login.html"
echo "  按 Ctrl+C 停止"
echo "=========================================="
echo ""
open http://localhost:8000/static/login.html 2>/dev/null || true
python run_server.py
STARTUP
chmod +x "$INSTALL_DIR/启动服务.command"

# 桌面快捷方式
if [ -d "$HOME/Desktop" ]; then
    ln -sf "$INSTALL_DIR/启动服务.command" "$HOME/Desktop/耗材管理系统.command" 2>/dev/null || true
    echo "✅ 桌面快捷方式已创建"
fi

echo ""
echo "=========================================="
echo "  ✅ 安装完成！"
echo "  双击桌面「耗材管理系统.command」启动"
echo "  管理端: http://localhost:8000/static/login.html"
echo "  账号:   admin / admin123"
echo "=========================================="
