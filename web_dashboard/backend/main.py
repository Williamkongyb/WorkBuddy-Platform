from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# 创建FastAPI应用
app = FastAPI(
    title="WorkBuddy 短视频智能中台 API",
    description="基于 n8n + Coze 的优化方案 v4.0",
    version="4.0.0"
)

# 配置CORS（允许前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入路由
from app.api import workflow
app.include_router(workflow.router, prefix="/api/workflow", tags=["工作流"])

# TODO: 导入其他路由（后续创建）
# from app.api import dashboard, cost, notification
# app.include_router(dashboard.router, prefix="/api/dashboard", tags=["数据看板"])
# app.include_router(cost.router, prefix="/api/cost", tags=["成本追踪"])
# app.include_router(notification.router, prefix="/api/notification", tags=["通知管理"])

@app.get("/")
async def root():
    """API根路径"""
    return {
        "message": "WorkBuddy 短视频智能中台 API v4.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}

# 启动事件
@app.on_event("startup")
async def startup_event():
    print("🚀 WorkBuddy API 启动成功！")
    print("📊 访问 http://localhost:8000/docs 查看API文档")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
