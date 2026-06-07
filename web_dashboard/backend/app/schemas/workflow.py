from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# ============ 工作流 Schema ============

class WorkflowBase(BaseModel):
    """工作流基础Schema"""
    name: str = Field(..., description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    nodes: List[Dict[str, Any]] = Field(default=[], description="节点配置")
    edges: List[Dict[str, Any]] = Field(default=[], description="连接线配置")
    is_template: bool = Field(default=False, description="是否模板")


class WorkflowCreate(WorkflowBase):
    """创建工作流"""
    pass


class WorkflowUpdate(BaseModel):
    """更新工作流（部分字段可选）"""
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: Optional[List[Dict[str, Any]] = None
    edges: Optional[List[Dict[str, Any]] = None
    status: Optional[str] = None
    is_template: Optional[bool] = None


class WorkflowInDB(WorkflowBase):
    """数据库中的工作流"""
    id: str
    status: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    
    class Config:
        orm_mode = True


class WorkflowResponse(WorkflowInDB):
    """工作流响应"""
    pass


# ============ 工作流执行 Schema ============

class WorkflowExecuteRequest(BaseModel):
    """工作流执行请求"""
    workflow_id: str = Field(..., description="工作流ID")
    dry_run: bool = Field(default=False, description="试运行（不实际执行）")
    trigger: str = Field(default="manual", description="触发方式（manual/schedule/webhook）")


class NodeExecutionResult(BaseModel):
    """节点执行结果"""
    node_id: str
    node_type: str
    status: str  # success/failed/running/skipped
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    cost: float = 0.0


class WorkflowExecutionResponse(BaseModel):
    """工作流执行响应"""
    execution_id: str
    workflow_id: str
    status: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    nodes_executed: List[NodeExecutionResult] = []
    total_cost: float = 0.0
    error_message: Optional[str] = None


# ============ 节点类型定义 ============

class NodeType:
    """节点类型常量"""
    SCRIPT_GENERATE = "script_generate"  # 文案生成
    VIDEO_GENERATE = "video_generate"     # 视频生成
    VIDEO_PUBLISH = "video_publish"       # 视频发布
    DATA_MONITOR = "data_monitor"         # 数据监控
    AI_EMPLOYEE = "ai_employee"          # AI超级员工
    CONDITION = "condition"                # 条件判断
    NOTIFICATION = "notification"          # 通知


# 节点类型显示名称映射
NODE_TYPE_DISPLAY = {
    NodeType.SCRIPT_GENERATE: "智能文案生成",
    NodeType.VIDEO_GENERATE: "视频自动生成",
    NodeType.VIDEO_PUBLISH: "多平台发布",
    NodeType.DATA_MONITOR: "数据监控",
    NodeType.AI_EMPLOYEE: "AI超级员工",
    NodeType.CONDITION: "条件判断",
    NodeType.NOTIFICATION: "通知",
}

# 节点图标映射
NODE_TYPE_ICON = {
    NodeType.SCRIPT_GENERATE: "📝",
    NodeType.VIDEO_GENERATE: "🎬",
    NodeType.VIDEO_PUBLISH: "📤",
    NodeType.DATA_MONITOR: "📊",
    NodeType.AI_EMPLOYEE: "🤖",
    NodeType.CONDITION: "🔀",
    NodeType.NOTIFICATION: "🔔",
}

# 节点颜色映射
NODE_TYPE_COLOR = {
    NodeType.SCRIPT_GENERATE: "#52c41a",  # 绿色
    NodeType.VIDEO_GENERATE: "#1890ff",    # 蓝色
    NodeType.VIDEO_PUBLISH: "#faad14",    # 黄色
    NodeType.DATA_MONITOR: "#722ed1",     # 紫色
    NodeType.AI_EMPLOYEE: "#13c2c2",     # 青色
    NodeType.CONDITION: "#eb2f96",        # 粉色
    NodeType.NOTIFICATION: "#fa8c16",     # 橙色
}
