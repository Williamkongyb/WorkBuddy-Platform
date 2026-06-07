from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime

from app.db.session import get_db
from app.models.models import Workflow, WorkflowExecution, VideoGeneration, CostRecord
from app.schemas.workflow import (
    WorkflowCreate, WorkflowUpdate, WorkflowResponse,
    WorkflowExecuteRequest, WorkflowExecutionResponse, NodeExecutionResult,
    NodeType, NODE_TYPE_DISPLAY
)
from app.core.workflow_engine import execute_workflow  # 后续创建

router = APIRouter()

# ============ 工作流 CRUD ============

@router.post("", response_model=WorkflowResponse)
def create_workflow(workflow: WorkflowCreate, db: Session = Depends(get_db)):
    """创建工作流"""
    workflow_id = str(uuid.uuid4())
    db_workflow = Workflow(
        id=workflow_id,
        name=workflow.name,
        description=workflow.description,
        nodes=workflow.nodes,
        edges=workflow.edges,
        status="inactive",
        is_template=workflow.is_template,
        created_by="admin"  # TODO: 从JWT获取
    )
    db.add(db_workflow)
    db.commit()
    db.refresh(db_workflow)
    return db_workflow


@router.get("", response_model=List[WorkflowResponse])
def list_workflows(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    is_template: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """列出工作流"""
    query = db.query(Workflow)
    if status:
        query = query.filter(Workflow.status == status)
    if is_template is not None:
        query = query.filter(Workflow.is_template == is_template)
    return query.offset(skip).limit(limit).all()


@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """获取单个工作流"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.put("/{workflow_id}", response_model=WorkflowResponse)
def update_workflow(
    workflow_id: str,
    workflow_update: WorkflowUpdate,
    db: Session = Depends(get_db)
):
    """更新工作流"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    update_data = workflow_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workflow, field, value)
    
    workflow.updated_at = datetime.now()
    db.commit()
    db.refresh(workflow)
    return workflow


@router.delete("/{workflow_id}")
def delete_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """删除工作流"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    db.delete(workflow)
    db.commit()
    return {"message": "Workflow deleted successfully"}


# ============ 工作流执行 ============

@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
def execute_workflow_endpoint(
    workflow_id: str,
    request: WorkflowExecuteRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """执行工作流"""
    # 查找工作流
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # 创建执行记录
    execution_id = str(uuid.uuid4())
    db_execution = WorkflowExecution(
        id=execution_id,
        workflow_id=workflow_id,
        status="pending",
        triggered_by=request.trigger
    )
    db.add(db_execution)
    db.commit()
    db.refresh(db_execution)
    
    # 后台执行工作流
    if not request.dry_run:
        background_tasks.add_task(
            execute_workflow,
            execution_id=execution_id,
            workflow=workflow,
            db=db
        )
        # 更新工作流状态
        workflow.status = "running"
        db.commit()
    else:
        # 试运行：只验证不执行
        db_execution.status = "success"
        db_execution.finished_at = datetime.now()
        db_execution.nodes_executed = [{"node_id": "test", "status": "skipped", "output": {"dry_run": True}}]
        db.commit()
    
    return {
        "execution_id": execution_id,
        "workflow_id": workflow_id,
        "status": db_execution.status,
        "started_at": db_execution.started_at,
        "finished_at": db_execution.finished_at,
        "nodes_executed": db_execution.nodes_executed or [],
        "total_cost": db_execution.total_cost,
        "error_message": db_execution.error_message
    }


@router.get("/executions/{execution_id}", response_model=WorkflowExecutionResponse)
def get_execution(execution_id: str, db: Session = Depends(get_db)):
    """获取执行记录"""
    execution = db.query(WorkflowExecution).filter(WorkflowExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return {
        "execution_id": execution.id,
        "workflow_id": execution.workflow_id,
        "status": execution.status,
        "started_at": execution.started_at,
        "finished_at": execution.finished_at,
        "nodes_executed": execution.nodes_executed or [],
        "total_cost": execution.total_cost,
        "error_message": execution.error_message
    }


@router.get("/{workflow_id}/executions", response_model=List[WorkflowExecutionResponse])
def list_executions(
    workflow_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """列出工作流的执行记录"""
    query = db.query(WorkflowExecution).filter(WorkflowExecution.workflow_id == workflow_id)
    executions = query.offset(skip).limit(limit).all()
    
    return [
        {
            "execution_id": e.id,
            "workflow_id": e.workflow_id,
            "status": e.status,
            "started_at": e.started_at,
            "finished_at": e.finished_at,
            "nodes_executed": e.nodes_executed or [],
            "total_cost": e.total_cost,
            "error_message": e.error_message
        }
        for e in executions
    ]


# ============ 工作流模板 ============

@router.get("/templates", response_model=List[WorkflowResponse])
def list_templates(db: Session = Depends(get_db)):
    """列出工作流模板"""
    return db.query(Workflow).filter(Workflow.is_template == True).all()


@router.post("/{workflow_id}/save_as_template")
def save_as_template(workflow_id: str, db: Session = Depends(get_db)):
    """保存为模板"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow.is_template = True
    db.commit()
    return {"message": "Workflow saved as template"}


# ============ 节点类型信息 ============

@router.get("/node_types/info")
def get_node_types_info():
    """获取所有节点类型信息（用于前端渲染）"""
    return {
        "node_types": [
            {
                "type": node_type,
                "display_name": NODE_TYPE_DISPLAY[node_type],
                "icon": __import__("app.schemas.workflow", fromlist=["NODE_TYPE_ICON"]).NODE_TYPE_ICON[node_type],
                "color": __import__("app.schemas.workflow", fromlist=["NODE_TYPE_COLOR"]).NODE_TYPE_COLOR[node_type]
            }
            for node_type in NodeType.__dict__.values()
            if not node_type.startswith("_")
        ]
    }
