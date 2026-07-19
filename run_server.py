"""
打印机耗材管理系统 — 一键启动程序
双击此文件即可启动服务，自动打开浏览器
打包: pyinstaller --onefile --name 耗材管理系统 run_server.py
"""
import os
import sys
import time
import threading
import webbrowser
import socket


def find_free_port(start=8000):
    """找一个可用端口"""
    for port in range(start, start + 100):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('', port))
            s.close()
            return port
        except OSError:
            continue
    return 8000


def main():
    # 确保在项目目录下
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    port = find_free_port()
    url = f"http://127.0.0.1:{port}/static/login.html"

    print("=" * 55)
    print("     🖨️  打印机耗材管理系统")
    print("=" * 55)
    print(f"     服务地址: http://localhost:{port}")
    print(f"     管理后台: http://localhost:{port}/static/login.html")
    print(f"     默认管理员: admin / admin123")
    print("=" * 55)
    print()

    # 在新线程启动浏览器
    def open_browser():
        time.sleep(1.5)
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()

    # 确保所有模块加载
    import backend.routers.static  # noqa
    # 启动 FastAPI
    import uvicorn
    from backend.main import app

    print("正在启动服务...")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
