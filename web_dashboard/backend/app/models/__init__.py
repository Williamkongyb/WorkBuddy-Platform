# 数据库模型包
from app.models.models import Base

# 导入所有模型以确保被Base识别
from app.models.models import (
    Workflow, WorkflowExecution, VideoGeneration,
    PlatformData, CostRecord, Notification, SystemConfig
)
