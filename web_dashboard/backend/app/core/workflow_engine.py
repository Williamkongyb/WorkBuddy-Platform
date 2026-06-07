from typing import Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime
import time

from app.models.models import WorkflowExecution, VideoGeneration, PlatformData, CostRecord
from app.schemas.workflow import NodeType, NodeExecutionResult


def execute_workflow(execution_id: str, workflow: Any, db: Session):
    """
    执行工作流（后台任务）
    
    Args:
        execution_id: 执行记录ID
        workflow: 工作流对象（包含nodes和edges）
        db: 数据库会话
    """
    # 获取执行记录
    execution = db.query(WorkflowExecution).filter(WorkflowExecution.id == execution_id).first()
    if not execution:
        print(f"❌ 执行记录不存在: {execution_id}")
        return
    
    try:
        # 更新状态为运行中
        execution.status = "running"
        db.commit()
        
        print(f"🚀 开始执行工作流: {workflow.name} (ID: {workflow.id})")
        
        # 解析节点和边
        nodes = workflow.nodes  # List[Dict]
        edges = workflow.edges  # List[Dict]
        
        # 构建节点ID -> 节点的映射
        node_map = {node["id"]: node for node in nodes}
        
        # 构建邻接表（用于拓扑排序）
        adj_list = {node["id"]: [] for node in nodes}
        in_degree = {node["id"]: 0 for node in nodes}
        
        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            if source in adj_list:
                adj_list[source].append(target)
                in_degree[target] = in_degree.get(target, 0) + 1
        
        # 拓扑排序（广度优先）
        queue = [node_id for node_id, deg in in_degree.items() if deg == 0]
        executed_nodes = []
        total_cost = 0.0
        
        while queue:
            current_node_id = queue.pop(0)
            current_node = node_map.get(current_node_id)
            
            if not current_node:
                continue
            
            # 执行节点
            node_result = execute_node(current_node, execution_id, db)
            executed_nodes.append(node_result.dict())
            total_cost += node_result.cost
            
            # 输出到日志
            status_icon = "✅" if node_result.status == "success" else "❌"
            print(f"{status_icon} 节点执行{'' if node_result.status == 'success' else '失败'}: {current_node.get('data', {}).get('label', current_node_id)}")
            
            if node_result.error:
                print(f"   错误: {node_result.error}")
            
            # 将相邻的未执行节点加入队列
            for neighbor in adj_list.get(current_node_id, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # 更新执行记录
        execution.status = "success"
        execution.finished_at = datetime.now()
        execution.nodes_executed = executed_nodes
        execution.total_cost = total_cost
        db.commit()
        
        print(f"✅ 工作流执行完成！总成本: ¥{total_cost:.2f}")
        
        # TODO: 发送通知（企微/钉钉/飞书）
        # send_notification(execution_id, "success", db)
        
    except Exception as e:
        # 执行失败
        execution.status = "failed"
        execution.finished_at = datetime.now()
        execution.error_message = str(e)
        db.commit()
        
        print(f"❌ 工作流执行失败: {str(e)}")
        
        # TODO: 发送失败通知
        # send_notification(execution_id, "failed", db)


def execute_node(node: Dict[str, Any], execution_id: str, db: Session) -> NodeExecutionResult:
    """
    执行单个节点
    
    Args:
        node: 节点配置（React Flow节点对象）
        execution_id: 执行记录ID
        db: 数据库会话
        
    Returns:
        NodeExecutionResult: 节点执行结果
    """
    node_id = node["id"]
    node_type = node.get("type", "")
    node_data = node.get("data", {})
    node_label = node_data.get("label", node_id)
    
    start_time = datetime.now()
    
    try:
        # 根据节点类型执行不同逻辑
        if node_type == "scriptGenerate" or node_data.get("nodeType") == NodeType.SCRIPT_GENERATE:
            # 文案生成节点
            result = execute_script_generate_node(node_data, db)
        
        elif node_type == "videoGenerate" or node_data.get("nodeType") == NodeType.VIDEO_GENERATE:
            # 视频生成节点
            result = execute_video_generate_node(node_data, db)
        
        elif node_type == "videoPublish" or node_data.get("nodeType") == NodeType.VIDEO_PUBLISH:
            # 视频发布节点
            result = execute_video_publish_node(node_data, db)
        
        elif node_type == "dataMonitor" or node_data.get("nodeType") == NodeType.DATA_MONITOR:
            # 数据监控节点
            result = execute_data_monitor_node(node_data, db)
        
        elif node_type == "aiEmployee" or node_data.get("nodeType") == NodeType.AI_EMPLOYEE:
            # AI超级员工节点
            result = execute_ai_employee_node(node_data, db)
        
        elif node_type == "condition" or node_data.get("nodeType") == NodeType.CONDITION:
            # 条件判断节点
            result = execute_condition_node(node_data, db)
        
        elif node_type == "notification" or node_data.get("nodeType") == NodeType.NOTIFICATION:
            # 通知节点
            result = execute_notification_node(node_data, db)
        
        else:
            # 未知节点类型
            raise Exception(f"未知节点类型: {node_type}")
        
        # 记录成本
        cost = result.get("cost", 0.0)
        if cost > 0:
            record_cost(execution_id, node_label, cost, db)
        
        return NodeExecutionResult(
            node_id=node_id,
            node_type=node_type,
            status="success",
            started_at=start_time,
            finished_at=datetime.now(),
            output=result,
            cost=cost
        )
        
    except Exception as e:
        return NodeExecutionResult(
            node_id=node_id,
            node_type=node_type,
            status="failed",
            started_at=start_time,
            finished_at=datetime.now(),
            error=str(e),
            cost=0.0
        )


# ============ 各类节点执行逻辑 ============

def execute_script_generate_node(node_data: Dict, db: Session) -> Dict:
    """执行文案生成节点"""
    print(f"  📝 执行文案生成节点...")
    
    # TODO: 调用1_generate_script.py
    # 这里先模拟执行
    time.sleep(2)
    
    product_name = node_data.get("productName", "未知产品")
    platforms = node_data.get("platforms", ["抖音"])
    
    result = {
        "product_name": product_name,
        "platforms": platforms,
        "scripts": [
            {"platform": platform, "script": f"这是为{platform}生成的文案关于{product_name}..."}
            for platform in platforms
        ],
        "cost": 0.5  # GPT-4调用成本
    }
    
    print(f"  ✅ 文案生成完成: {len(platforms)}个平台")
    return result


def execute_video_generate_node(node_data: Dict, db: Session) -> Dict:
    """执行视频生成节点"""
    print(f"  🎬 执行视频生成节点...")
    
    # TODO: 调用2_make_video.py 或 2_make_video_seedance.py
    # 这里先模拟执行
    time.sleep(5)
    
    method = node_data.get("method", "jianying")  # jianying/seedance/template
    
    result = {
        "method": method,
        "video_path": f"D:/WB_Workflow/final_videos/video_{int(time.time())}.mp4",
        "duration": 60.0,
        "cost": 15.0 if method == "seedance" else 0.0
    }
    
    # 保存视频生成记录到数据库
    video_record = VideoGeneration(
        id=str(__import__("uuid").uuid4()),
        workflow_execution_id=node_data.get("execution_id"),
        product_name=node_data.get("productName", "未知产品"),
        platform=node_data.get("platform", "抖音"),
        video_path=result["video_path"],
        status="generating",
        duration=result["duration"]
    )
    db.add(video_record)
    db.commit()
    
    print(f"  ✅ 视频生成完成: {result['video_path']}")
    return result


def execute_video_publish_node(node_data: Dict, db: Session) -> Dict:
    """执行视频发布节点"""
    print(f"  📤 执行视频发布节点...")
    
    # TODO: 调用3_auto_publish.py
    # 这里先模拟执行
    time.sleep(3)
    
    platforms = node_data.get("platforms", ["抖音"])
    
    result = {
        "platforms": platforms,
        "status": "published",
        "publish_time": datetime.now().isoformat()
    }
    
    print(f"  ✅ 视频发布完成: {', '.join(platforms)}")
    return result


def execute_data_monitor_node(node_data: Dict, db: Session) -> Dict:
    """执行数据监控节点"""
    print(f"  📊 执行数据监控节点...")
    
    # TODO: 调用data_monitor.py
    # 这里先模拟执行
    time.sleep(2)
    
    result = {
        "views": 128456,
        "likes": 8932,
        "comments": 432,
        "completion_rate": 42.3,
        "traffic_index": 86.5,
        "cost": 0.0
    }
    
    # 保存平台数据到数据库
    for platform in ["抖音", "小红书", "B站"]:
        data_record = PlatformData(
            id=str(__import__("uuid").uuid4()),
            platform=platform,
            date=datetime.now(),
            views=result["views"] // 3,
            likes=result["likes"] // 3,
            comments=result["comments"] // 3,
            completion_rate=result["completion_rate"],
            traffic_index=result["traffic_index"]
        )
        db.add(data_record)
    db.commit()
    
    print(f"  ✅ 数据监控完成: 播放{result['views']}, 点赞{result['likes']}")
    return result


def execute_ai_employee_node(node_data: Dict, db: Session) -> Dict:
    """执行AI超级员工节点"""
    print(f"  🤖 执行AI超级员工节点...")
    
    # TODO: 调用ai_super_employee.py
    # 这里先模拟执行
    time.sleep(3)
    
    result = {
        "report": "AI超级员工深度复盘报告已生成",
        "insights": [
            "建议优化开头3秒内容（2s跳出率偏高）",
            "完播率优于行业均值，保持当前节奏",
            "评论区正面反馈占比85%，可加大投放"
        ],
        "cost": 1.0
    }
    
    print(f"  ✅ AI超级员工分析完成: {len(result['insights'])}条建议")
    return result


def execute_condition_node(node_data: Dict, db: Session) -> Dict:
    """执行条件判断节点"""
    print(f"  🔀 执行条件判断节点...")
    
    # TODO: 实现条件判断逻辑
    # 这里先模拟执行
    time.sleep(1)
    
    condition = node_data.get("condition", "true")
    
    result = {
        "condition": condition,
        "result": True,  # 模拟条件为真
        "branch": "true_branch"
    }
    
    print(f"  ✅ 条件判断完成: {result['branch']}")
    return result


def execute_notification_node(node_data: Dict, db: Session) -> Dict:
    """执行通知节点"""
    print(f"  🔔 执行通知节点...")
    
    # TODO: 调用企微/钉钉/飞书Webhook
    # 这里先模拟执行
    time.sleep(1)
    
    channel = node_data.get("channel", "wecom")
    message = node_data.get("message", "工作流执行完成")
    
    result = {
        "channel": channel,
        "message": message,
        "status": "sent"
    }
    
    # 保存通知记录到数据库
    notification_record = Notification(
        id=str(__import__("uuid").uuid4()),
        workflow_execution_id=node_data.get("execution_id"),
        type="execution_success",
        channel=channel,
        message=message,
        status="sent",
        sent_at=datetime.now()
    )
    db.add(notification_record)
    db.commit()
    
    print(f"  ✅ 通知发送完成: {channel}")
    return result


# ============ 辅助函数 ============

def record_cost(execution_id: str, service: str, cost: float, db: Session):
    """记录成本"""
    cost_record = CostRecord(
        id=str(__import__("uuid").uuid4()),
        workflow_execution_id=execution_id,
        service=service,
        cost=cost
    )
    db.add(cost_record)
    db.commit()
