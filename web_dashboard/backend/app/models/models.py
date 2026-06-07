from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, JSON
from sqlalchemy.ext.declarative import declaritive_base
from datetime import datetime

Base = declaritive_base()

class Workflow(Base):
    """工作流表"""
    __tablename__ = "workflows"
    
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    nodes = Column(JSON, nullable=False)  # 节点配置（JSON）
    edges = Column(JSON, nullable=False)  # 连接线配置（JSON）
    status = Column(String(20), default="inactive")  # active/inactive/running/error
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = Column(String(50), nullable=True)
    is_template = Column(Boolean, default=False)  # 是否模板


class WorkflowExecution(Base):
    """工作流执行记录表"""
    __tablename__ = "workflow_executions"
    
    id = Column(String(50), primary_key=True, index=True)
    workflow_id = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False)  # pending/running/success/failed
    started_at = Column(DateTime, default=datetime.now)
    finished_at = Column(DateTime, nullable=True)
    nodes_executed = Column(JSON, nullable=True)  # 已执行节点记录
    error_message = Column(Text, nullable=True)
    total_cost = Column(Float, default=0.0)  # 总成本（元）
    triggered_by = Column(String(50), nullable=True)  # 触发方式


class VideoGeneration(Base):
    """视频生成记录表"""
    __tablename__ = "video_generations"
    
    id = Column(String(50), primary_key=True, index=True)
    workflow_execution_id = Column(String(50), nullable=True, index=True)
    product_name = Column(String(200), nullable=False)
    platform = Column(String(50), nullable=False)  # 抖音/小红书/B站
    script = Column(Text, nullable=True)  # 生成的文案
    video_path = Column(String(500), nullable=True)  # 视频文件路径
    status = Column(String(20), default="pending")  # pending/generating/uploading/published/failed
    duration = Column(Float, nullable=True)  # 视频时长（秒）
    file_size = Column(Integer, nullable=True)  # 文件大小（字节）
    created_at = Column(DateTime, default=datetime.now)
    published_at = Column(DateTime, nullable=True)


class PlatformData(Base):
    """平台数据表（每日快照）"""
    __tablename__ = "platform_data"
    
    id = Column(String(50), primary_key=True, index=True)
    video_generation_id = Column(String(50), nullable=True, index=True)
    platform = Column(String(50), nullable=False)  # 抖音/小红书/B站
    date = Column(DateTime, nullable=False, index=True)
    views = Column(Integer, default=0)  # 播放量
    likes = Column(Integer, default=0)  # 点赞数
    comments = Column(Integer, default=0)  # 评论数
    shares = Column(Integer, default=0)  # 分享数
    completion_rate = Column(Float, default=0.0)  # 完播率（%）
    two_sec_dropoff = Column(Float, default=0.0)  # 2秒跳出率（%）
    traffic_index = Column(Float, default=0.0)  # 推流指数
    revenue = Column(Float, default=0.0)  # 转化收入（元）


class CostRecord(Base):
    """成本记录表"""
    __tablename__ = "cost_records"
    
    id = Column(String(50), primary_key=True, index=True)
    workflow_execution_id = Column(String(50), nullable=True, index=True)
    service = Column(String(50), nullable=False)  # GPT-4/Seedance/合规自检/AI超级员工
    api_calls = Column(Integer, default=1)  # API调用次数
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost = Column(Float, nullable=False)  # 成本（元）
    created_at = Column(DateTime, default=datetime.now)


class Notification(Base):
    """通知记录表"""
    __tablename__ = "notifications"
    
    id = Column(String(50), primary_key=True, index=True)
    workflow_execution_id = Column(String(50), nullable=True, index=True)
    type = Column(String(50), nullable=False)  # execution_success/execution_failed/alert
    channel = Column(String(50), nullable=False)  # 企微/钉钉/飞书/Discord
    message = Column(Text, nullable=False)
    status = Column(String(20), default="pending")  # pending/sent/failed
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = "system_config"
    
    id = Column(String(50), primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
