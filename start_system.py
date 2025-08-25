#!/usr/bin/env python3
"""
智能作文评价系统启动器

通过命令行参数控制启动不同的服务：
- web服务：处理用户交互
- 报告服务：提供报告下载
- 完整系统：同时启动所有服务

使用示例：
    python start_system.py --help
    python start_system.py --web-only
    python start_system.py --reports-only
    python start_system.py --full-system
"""

import argparse
import sys
import os
import subprocess
import time
from pathlib import Path

try:
    import logging
    import uvicorn
    from utils.oxygent_error_handler import get_error_handler
    HAS_LOGGING = True
except ImportError:
    HAS_LOGGING = False

class SystemLauncher:
    """系统启动器"""
    
    def __init__(self):
        self.processes = []
        
        # 设置日志
        if HAS_LOGGING:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s | %(levelname)-8s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = None
    
    def log(self, message, level="INFO"):
        """统一日志输出"""
        if self.logger:
            if level == "INFO":
                self.logger.info(message)
            elif level == "ERROR":
                self.logger.error(message)
            elif level == "WARNING":
                self.logger.warning(message)
        else:
            print(f"[{level}] {message}")
    
    def check_dependencies(self):
        """检查必要依赖"""
        required_modules = [
            'fastapi', 'uvicorn', 'loguru', 'pydantic', 
            'langextract', 'oxygent', 'dotenv'
        ]
        
        missing = []
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing.append(module)
        
        if missing:
            self.log(f"缺少依赖: {', '.join(missing)}", "ERROR")
            self.log("请运行: pip install -r requirements.txt", "INFO")
            return False
        return True
    
    def start_web_service(self, host="127.0.0.1", port=8000, debug=False):
        """启动Web服务"""
        try:
            self.log(f"🚀 启动Web服务: http://{host}:{port}")
            
            # 检查web服务文件
            web_file = Path("main.py")
            if not web_file.exists():
                self.log("main.py 文件不存在，创建示例服务...", "WARNING")
                self._create_simple_web_service()
                return
            
            # 创建必要的目录
            Path("logs").mkdir(exist_ok=True)
            Path("data/reports").mkdir(parents=True, exist_ok=True)
            
            # 使用subprocess启动服务
            cmd = [sys.executable, "main.py"]
            
            # Windows系统
            if os.name == 'nt':
                process = subprocess.Popen(
                    cmd,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                # Unix系统
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            self.processes.append(process)
            time.sleep(3)
            
            if process.poll() is None:
                self.log(f"✅ Web服务已启动: http://{host}:{port}")
                return True
            else:
                self.log("❌ Web服务启动失败", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"启动Web服务失败: {e}", "ERROR")
            return False
    
    def start_reports_service(self, host="127.0.0.1", port=8081):
        """启动报告服务"""
        try:
            self.log(f"📊 启动报告服务: http://{host}:{port}")
            
            # 检查报告服务文件
            reports_file = Path("reports_server.py")
            if reports_file.exists():
                cmd = [sys.executable, "reports_server.py", f"--host={host}", f"--port={port}"]
            else:
                # 使用内置的报告服务
                self._create_reports_server()
                cmd = [sys.executable, "reports_server.py", f"--host={host}", f"--port={port}"]
            
            # Windows系统
            if os.name == 'nt':
                process = subprocess.Popen(
                    cmd,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                # Unix系统
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            self.processes.append(process)
            time.sleep(2)
            
            if process.poll() is None:
                self.log(f"✅ 报告服务已启动: http://{host}:{port}")
                return True
            else:
                self.log("❌ 报告服务启动失败", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"启动报告服务失败: {e}", "ERROR")
            return False
    
    def _create_simple_web_service(self):
        """创建简单的web服务"""
        web_content = '''#!/usr/bin/env python3
"""
智能作文评价系统 - Web界面
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI(
    title="智能作文评价系统",
    description="基于OxyGent多智能体框架的作文智能评价系统",
    version="1.0.0"
)

# 确保目录存在
import os
os.makedirs("data/reports", exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>智能作文评价系统</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container { 
                max-width: 800px; 
                margin: 0 auto; 
                background: white; 
                border-radius: 15px; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.1); 
                overflow: hidden;
            }
            .header { 
                background: linear-gradient(135deg, #4CAF50, #45a049); 
                color: white; 
                padding: 40px 30px; 
                text-align: center;
            }
            .feature { 
                margin: 30px; 
                padding: 25px; 
                border-left: 5px solid #4CAF50; 
                background: #f9f9f9;
                border-radius: 10px;
            }
            .btn {
                display: inline-block;
                padding: 12px 24px;
                background: #4CAF50;
                color: white;
                text-decoration: none;
                border-radius: 25px;
                margin: 10px 5px;
                transition: background 0.3s;
            }
            .btn:hover {
                background: #45a049;
            }
            .services {
                background: #f0f8ff;
                margin: 30px;
                padding: 25px;
                border-radius: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📝 智能作文评价系统</h1>
                <p>基于OxyGent多智能体框架的作文智能评价系统</p>
                <p>让每个学生都能得到个性化的写作指导</p>
            </div>
            
            <div class="services">
                <h3>🚀 系统服务</h3>
                <p><strong>Web服务:</strong> <a href="http://127.0.0.1:8080" class="btn">访问主界面</a></p>
                <p><strong>报告服务:</strong> <a href="http://127.0.0.1:8081" class="btn">查看报告</a></p>
            </div>
            
            <div class="feature">
                <h3>🎯 系统功能</h3>
                <ul>
                    <li>📚 <strong>智能作文评价</strong> - 基于AI的多维度分析</li>
                    <li>🤖 <strong>多智能体协作</strong> - 专业团队协同工作</li>
                    <li>📊 <strong>个性化报告</strong> - 针对每个学生的特点</li>
                    <li>🎨 <strong>可视化展示</strong> - 直观的评价结果</li>
                </ul>
            </div>
            
            <div class="feature">
                <h3>🚀 快速开始</h3>
                <ol>
                    <li>点击上方的"访问主界面"进入系统</li>
                    <li>选择 "master_agent" 智能体</li>
                    <li>按照提示输入作文内容和相关信息</li>
                    <li>等待系统生成个性化评价报告</li>
                </ol>
                
                <div style="text-align: center; margin-top: 20px;">
                    <a href="http://127.0.0.1:8080" class="btn">立即开始评价</a>
                    <a href="http://127.0.0.1:8081" class="btn">查看示例报告</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "智能作文评价系统"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
'''
        
        with open("simple_web.py", "w", encoding="utf-8") as f:
            f.write(web_content)
        return True
    
    def _create_reports_server(self):
        """创建报告服务器"""
        server_content = '''#!/usr/bin/env python3
"""
报告文件服务器
提供作文评价报告的HTTP访问
"""

import http.server
import socketserver
import os
import argparse
from pathlib import Path

class ReportsHandler(http.server.SimpleHTTPRequestHandler):
    """自定义报告处理器"""
    
    def __init__(self, *args, **kwargs):
        # 设置服务目录
        reports_dir = Path("data/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        super().__init__(*args, directory=str(reports_dir), **kwargs)
    
    def end_headers(self):
        # 添加CORS支持
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()
    
    def do_GET(self):
        """处理GET请求"""
        if self.path == '/':
            self.path = '/index.html'
        
        # 如果请求的是根目录，创建索引页面
        if self.path == '/index.html':
            self._create_index_page()
        
        super().do_GET()
    
    def _create_index_page(self):
        """创建报告索引页面"""
        reports_dir = Path("data/reports")
        reports = list(reports_dir.glob("*.md")) + list(reports_dir.glob("*.html"))
        
        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <title>作文评价报告 - 智能系统</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        .report {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }}
        .report a {{ text-decoration: none; color: #4CAF50; font-weight: bold; }}
        .empty {{ text-align: center; color: #666; margin: 40px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 作文评价报告</h1>
        <p>这里展示所有生成的作文评价报告</p>
        
        <div class="reports">
        '''
        
        if reports:
            for report in sorted(reports, key=lambda x: x.stat().st_mtime, reverse=True):
                html_content += f'''
                <div class="report">
                    <a href="{report.name}">{report.name}</a>
                    <span style="color: #666; margin-left: 20px;">
                        {report.stat().st_mtime.strftime('%Y-%m-%d %H:%M')}
                    </span>
                </div>
                '''
        else:
            html_content += '''
                <div class="empty">
                    <h3>暂无报告</h3>
                    <p>请先使用评价系统生成作文评价报告</p>
                </div>
            '''
        
        html_content += '''
        </div>
    </div>
</body>
</html>
        '''
        
        index_path = reports_dir / "index.html"
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(html_content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="报告文件服务器")
    parser.add_argument('--host', default='127.0.0.1', help='主机地址')
    parser.add_argument('--port', type=int, default=8081, help='端口号')
    args = parser.parse_args()
    
    # 确保目录存在
    os.makedirs("data/reports", exist_ok=True)
    
    handler = ReportsHandler
    with socketserver.TCPServer((args.host, args.port), handler) as httpd:
        print(f"📊 报告服务运行在: http://{args.host}:{args.port}")
        print(f"📁 报告目录: {Path('data/reports').absolute()}")
        print("🚀 按 Ctrl+C 停止服务")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 服务已停止")
'''
        
        with open("reports_server.py", "w", encoding="utf-8") as f:
            f.write(server_content)
        return True
    
    def start_full_system(self, web_host="127.0.0.1", web_port=8000, reports_host="127.0.0.1", reports_port=8081, debug=False):
        """启动完整系统"""
        self.log("🚀 启动完整智能作文评价系统...")
        
        # 创建必要的目录
        Path("logs").mkdir(exist_ok=True)
        Path("data/reports").mkdir(parents=True, exist_ok=True)
        
        # 启动报告服务
        if not self.start_reports_service(reports_host, reports_port):
            return False
        
        time.sleep(1)
        
        # 启动Web服务
        if not self.start_web_service(web_host, web_port, debug):
            self.shutdown()
            return False
        
        self.log("=" * 60)
        self.log("🎉 完整系统已启动")
        self.log(f"🌐 Web服务: http://{web_host}:{web_port}")
        self.log(f"📊 报告服务: http://{reports_host}:{reports_port}")
        self.log("💡 服务已在后台运行，按 Ctrl+C 停止")
        self.log("=" * 60)
        
        try:
            # 保持主进程运行
            while True:
                time.sleep(1)
                # 检查子进程状态
                for process in self.processes:
                    if process.poll() is not None:
                        self.log("检测到服务异常退出，正在重启...", "WARNING")
                        break
        except KeyboardInterrupt:
            self.log("🛑 正在停止所有服务...")
            self.shutdown()
    
    def shutdown(self):
        """优雅关闭所有服务"""
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except:
                pass
        self.log("✅ 所有服务已停止")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="智能作文评价系统启动器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  python start_system.py --web-only                    # 仅启动Web服务
  python start_system.py --reports-only               # 仅启动报告服务  
  python start_system.py --full-system                # 启动完整系统（默认）
  python start_system.py --full-system --debug        # 调试模式启动
  python start_system.py --web-port 9000              # 自定义端口
  python start_system.py --check-deps                 # 检查依赖
        """
    )
    
    # 启动模式
    parser.add_argument('--web-only', action='store_true', 
                       help='仅启动Web服务')
    parser.add_argument('--reports-only', action='store_true', 
                       help='仅启动报告服务')
    parser.add_argument('--full-system', action='store_true', 
                       help='启动完整系统（默认）')
    
    # 网络配置
    parser.add_argument('--web-host', default='127.0.0.1', 
                       help='Web服务主机地址 (默认: 127.0.0.1)')
    parser.add_argument('--web-port', type=int, default=8000, 
                       help='Web服务端口 (默认: 8000)')
    parser.add_argument('--reports-host', default='127.0.0.1', 
                       help='报告服务主机地址 (默认: 127.0.0.1)')
    parser.add_argument('--reports-port', type=int, default=8081, 
                       help='报告服务端口 (默认: 8081)')
    
    # 调试选项
    parser.add_argument('--debug', action='store_true', 
                       help='启用调试模式')
    
    # 检查依赖
    parser.add_argument('--check-deps', action='store_true', 
                       help='检查依赖并退出')
    
    args = parser.parse_args()
    
    launcher = SystemLauncher()
    
    # 检查依赖
    if args.check_deps:
        if launcher.check_dependencies():
            print("✅ 所有依赖已安装")
        else:
            print("❌ 存在缺失依赖")
        return
    
    # 检查依赖
    if not launcher.check_dependencies():
        return
    
    try:
        if args.web_only:
            launcher.start_web_service(args.web_host, args.web_port, args.debug)
            # 保持运行
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                launcher.shutdown()
        elif args.reports_only:
            launcher.start_reports_service(args.reports_host, args.reports_port)
            # 保持运行
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                launcher.shutdown()
        else:
            # 默认启动完整系统
            launcher.start_full_system(
                args.web_host, args.web_port, 
                args.reports_host, args.reports_port, 
                args.debug
            )
    except Exception as e:
        launcher.log(f"启动失败: {e}", "ERROR")
        launcher.shutdown()

if __name__ == "__main__":
    main()