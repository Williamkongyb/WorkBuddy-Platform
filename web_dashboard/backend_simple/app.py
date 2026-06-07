from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# 初始化数据库
def init_db():
    conn = sqlite3.connect('workflows.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS workflows
                 (id TEXT PRIMARY KEY, name TEXT, nodes TEXT, edges TEXT, 
                  status TEXT, created_at TEXT, updated_at TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return jsonify({"message": "WorkBuddy Web Dashboard API", "status": "running"})

@app.route('/api/workflow', methods=['GET'])
def list_workflows():
    """列出所有工作流"""
    conn = sqlite3.connect('workflows.db')
    c = conn.cursor()
    c.execute('SELECT id, name, status, created_at, updated_at FROM workflows')
    rows = c.fetchall()
    conn.close()
    
    workflows = []
    for row in rows:
        workflows.append({
            "id": row[0],
            "name": row[1],
            "status": row[2],
            "created_at": row[3],
            "updated_at": row[4]
        })
    return jsonify(workflows)

@app.route('/api/workflow', methods=['POST'])
def create_workflow():
    """创建工作流"""
    data = request.json
    workflow_id = data.get('id', f'wf_{datetime.now().strftime("%Y%m%d%H%M%S")}')
    name = data.get('name', '新工作流')
    nodes = json.dumps(data.get('nodes', []))
    edges = json.dumps(data.get('edges', []))
    
    conn = sqlite3.connect('workflows.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO workflows VALUES (?, ?, ?, ?, ?, ?, ?)',
              (workflow_id, name, nodes, edges, 'draft', 
               datetime.now().isoformat(), datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    return jsonify({"id": workflow_id, "name": name, "status": "draft"})

@app.route('/api/workflow/<workflow_id>', methods=['GET'])
def get_workflow(workflow_id):
    """获取工作流详情"""
    conn = sqlite3.connect('workflows.db')
    c = conn.cursor()
    c.execute('SELECT * FROM workflows WHERE id = ?', (workflow_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return jsonify({
            "id": row[0],
            "name": row[1],
            "nodes": json.loads(row[2]),
            "edges": json.loads(row[3]),
            "status": row[4],
            "created_at": row[5],
            "updated_at": row[6]
        })
    return jsonify({"error": "Not found"}), 404

@app.route('/api/workflow/<workflow_id>/execute', methods=['POST'])
def execute_workflow(workflow_id):
    """执行工作流（模拟）"""
    return jsonify({
        "status": "success",
        "message": "工作流执行已启动",
        "execution_id": f"exec_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    })

@app.route('/api/templates', methods=['GET'])
def get_templates():
    """获取预置模板"""
    templates = [
        {
            "id": "tpl_001",
            "name": "短视频全自动带货",
            "description": "热点抓取→文案生成→视频制作→自动发布→数据监控",
            "nodes": [
                {"id": "node_1", "type": "trigger", "position": {"x": 100, "y": 100}, "data": {"label": "定时触发"}},
                {"id": "node_2", "type": "action", "position": {"x": 300, "y": 100}, "data": {"label": "抓取热点"}},
                {"id": "node_3", "type": "action", "position": {"x": 500, "y": 100}, "data": {"label": "生成文案"}},
                {"id": "node_4", "type": "action", "position": {"x": 700, "y": 100}, "data": {"label": "制作视频"}},
                {"id": "node_5", "type": "action", "position": {"x": 900, "y": 100}, "data": {"label": "自动发布"}},
                {"id": "node_6", "type": "action", "position": {"x": 1100, "y": 100}, "data": {"label": "数据监控"}}
            ],
            "edges": [
                {"id": "edge_1", "source": "node_1", "target": "node_2"},
                {"id": "edge_2", "source": "node_2", "target": "node_3"},
                {"id": "edge_3", "source": "node_3", "target": "node_4"},
                {"id": "edge_4", "source": "node_4", "target": "node_5"},
                {"id": "edge_5", "source": "node_5", "target": "node_6"}
            ]
        }
    ]
    return jsonify(templates)

if __name__ == '__main__':
    print("WorkBuddy后端启动中...")
    print("访问地址: http://localhost:8000")
    app.run(host='0.0.0.0', port=8000, debug=True)
