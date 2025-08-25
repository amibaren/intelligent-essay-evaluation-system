#!/usr/bin/env python3
"""
简单的静态文件服务器 - 为reports目录提供HTTP访问
运行在端口8081，与主系统的8080端口并行工作
"""

import os
import asyncio
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from loguru import logger

app = FastAPI(title="Reports File Server", version="1.0.0")

# 添加CORS支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Reports目录路径
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

@app.get("/reports/{filename}")
async def get_report_file(filename: str):
    """获取报告文件"""
    file_path = REPORTS_DIR / filename
    
    if not file_path.exists():
        return Response(status_code=404, content=f"File {filename} not found")
    
    if not file_path.is_file():
        return Response(status_code=400, content=f"{filename} is not a file")
    
    # 根据文件扩展名设置Content-Type
    content_type = "text/plain"
    if filename.endswith('.html'):
        content_type = "text/html"
    elif filename.endswith('.md'):
        content_type = "text/markdown"
    
    logger.info(f"Serving file: {file_path}")
    return FileResponse(
        path=file_path,
        media_type=content_type,
        filename=filename,
        headers={
            "Content-Disposition": f"inline; filename={filename}",
            "Cache-Control": "no-cache"
        }
    )

@app.get("/reports")
async def list_report_files():
    """列出所有报告文件"""
    files = []
    for file_path in REPORTS_DIR.iterdir():
        if file_path.is_file():
            files.append({
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "url": f"/reports/{file_path.name}"
            })
    return {"files": files}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "reports-server"}

def start_reports_server(port: int = 8081):
    """启动报告文件服务器"""
    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    logger.info(f"启动报告文件服务器: http://127.0.0.1:{port}")
    return server

async def run_reports_server():
    """异步运行报告文件服务器"""
    server = start_reports_server()
    await server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(run_reports_server())
    except KeyboardInterrupt:
        logger.info("报告文件服务器已停止")