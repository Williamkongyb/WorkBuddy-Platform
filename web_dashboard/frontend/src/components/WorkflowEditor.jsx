import React, { useState, useCallback, useRef } from 'react';
import ReactFlow, {
  addEdge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { Modal, Form, Input, Select, Button, message, Card, Tag } from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  SaveOutlined,
} from '@ant-design/icons';

// 节点类型定义（与后端对应）
const NODE_TYPES = {
  scriptGenerate: {
    label: '智能文案生成',
    icon: '📝',
    color: '#52c41a',
    description: '生成4平台差异化文案+合规自检',
  },
  videoGenerate: {
    label: '视频自动生成',
    icon: '🎬',
    color: '#1890ff',
    description: '剪映数字人/Seedance API',
  },
  videoPublish: {
    label: '多平台发布',
    icon: '📤',
    color: '#faad14',
    description: '抖音/小红书/B站自动发布',
  },
  dataMonitor: {
    label: '数据监控',
    icon: '📊',
    color: '#722ed1',
    description: '推流指数+评论洞察',
  },
  aiEmployee: {
    label: 'AI超级员工',
    icon: '🤖',
    color: '#13c2c2',
    description: '深度复盘+异常预警',
  },
  condition: {
    label: '条件判断',
    icon: '🔀',
    color: '#eb2f96',
    description: '根据条件决定执行路径',
  },
  notification: {
    label: '通知',
    icon: '🔔',
    color: '#fa8c16',
    description: '企微/钉钉/飞书推送',
  },
};

// 自定义节点组件
const CustomNode = ({ data }) => {
  const nodeType = NODE_TYPES[data.nodeType];
  const color = nodeType?.color || '#999';
  const icon = nodeType?.icon || '📦';
  const label = nodeType?.label || data.label || '未知节点';

  return (
    <div
      style={{
        padding: '12px 16px',
        borderRadius: '8px',
        border: `2px solid ${color}`,
        background: '#fff',
        minWidth: '150px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
        <span style={{ fontSize: '18px' }}>{icon}</span>
        <span style={{ fontWeight: 600, fontSize: '14px' }}>{label}</span>
      </div>
      {data.status && (
        <Tag
          color={
            data.status === 'success' ? 'success' :
            data.status === 'running' ? 'processing' :
            data.status === 'failed' ? 'error' : 'default'
          }
          style={{ marginTop: '4px' }}
        >
          {data.status === 'success' ? '已完成' :
           data.status === 'running' ? '执行中' :
           data.status === 'failed' ? '失败' : '等待中'}
        </Tag>
      )}
    </div>
  );
};

const nodeTypes = {
  custom: CustomNode,
};

const defaultEdgeOptions = {
  markerEnd: { type: MarkerType.ArrowClosed, color: '#1890ff' },
  style: { stroke: '#1890ff', strokeWidth: 2 },
  animated: true,
};

const WorkflowEditor = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [currentNodeType, setCurrentNodeType] = useState(null);
  const [form] = Form.useForm();
  const reactFlowWrapper = useRef(null);
  const [reactFlowInstance, setReactFlowInstance] = useState(null);

  // 添加节点
  const onAddNode = useCallback(
    (nodeType) => {
      const nodeTypeInfo = NODE_TYPES[nodeType];
      const newNode = {
        id: `${nodeType}_${Date.now()}`,
        type: 'custom',
        position: {
          x: Math.random() * 400,
          y: Math.random() * 400,
        },
        data: {
          label: nodeTypeInfo.label,
          nodeType: nodeType,
          status: null,
          ...(nodeType === 'scriptGenerate' && {
            productName: '',
            platforms: ['抖音', '小红书'],
          }),
          ...(nodeType === 'videoGenerate' && {
            method: 'jianying', // jianying/seedance/template
          }),
          ...(nodeType === 'videoPublish' && {
            platforms: ['抖音', '小红书'],
          }),
          ...(nodeType === 'notification' && {
            channel: 'wecom',
            message: '',
          }),
        },
      };
      setNodes((nds) => [...nds, newNode]);
      setIsModalVisible(false);
    },
    [setNodes]
  );

  // 连接节点
  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge({ ...params, ...defaultEdgeOptions }, eds)),
    [setEdges]
  );

  // 删除选中节点/边
  const onDelete = useCallback(() => {
    setNodes((nds) => nds.filter((n) => !n.selected));
    setEdges((eds) => eds.filter((e) => !e.selected));
  }, [setNodes, setEdges]);

  // 保存工作流
  const onSave = useCallback(() => {
    const workflowData = {
      nodes: nodes.map((n) => ({
        id: n.id,
        type: n.type,
        position: n.position,
        data: n.data,
      })),
      edges: edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle,
        targetHandle: e.targetHandle,
      })),
    };
    console.log('保存工作流:', JSON.stringify(workflowData, null, 2));
    message.success('工作流保存成功！（查看Console）');
  }, [nodes, edges]);

  // 执行工作流
  const onExecute = useCallback(() => {
    if (nodes.length === 0) {
      message.warning('请先添加节点');
      return;
    }
    message.info('开始执行工作流...（模拟）');
    // TODO: 调用后端API执行工作流
  }, [nodes]);

  // 拖拽放置
  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event) => {
      event.preventDefault();
      const type = event.dataTransfer.getData('application/reactflow');
      if (!type) return;

      const position = reactFlowInstance?.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const nodeTypeInfo = NODE_TYPES[type];
      const newNode = {
        id: `${type}_${Date.now()}`,
        type: 'custom',
        position,
        data: {
          label: nodeTypeInfo.label,
          nodeType: type,
          status: null,
        },
      };
      setNodes((nds) => [...nds, newNode]);
    },
    [reactFlowInstance, setNodes]
  );

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* 顶部工具栏 */}
      <div
        style={{
          padding: '12px 24px',
          background: '#fff',
          borderBottom: '1px solid #f0f0f0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        }}
      >
        <h2 style={{ margin: 0, fontSize: '18px' }}>🔄 工作流编排器</h2>
        <div style={{ display: 'flex', gap: '8px' }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setIsModalVisible(true)}
          >
            添加节点
          </Button>
          <Button
            icon={<DeleteOutlined />}
            onClick={onDelete}
            danger
          >
            删除选中
          </Button>
          <Button
            icon={<SaveOutlined />}
            onClick={onSave}
          >
            保存
          </Button>
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={onExecute}
            style={{ background: '#52c41a', borderColor: '#52c41a' }}
          >
            执行工作流
          </Button>
        </div>
      </div>

      <div style={{ flex: 1, display: 'flex' }}>
        {/* 左侧节点面板 */}
        <div
          style={{
            width: '220px',
            background: '#fafafa',
            borderRight: '1px solid #f0f0f0',
            padding: '16px',
            overflowY: 'auto',
          }}
        >
          <h4 style={{ marginBottom: '12px', color: '#666' }}>节点类型</h4>
          {Object.entries(NODE_TYPES).map(([type, info]) => (
            <Card
              key={type}
              size="small"
              draggable
              onDragStart={(event) => {
                event.dataTransfer.setData('application/reactflow', type);
                event.dataTransfer.effectAllowed = 'move';
              }}
              style={{
                marginBottom: '8px',
                cursor: 'grab',
                borderLeft: `3px solid ${info.color}`,
              }}
              bodyStyle={{ padding: '8px 12px' }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '16px' }}>{info.icon}</span>
                <div>
                  <div style={{ fontWeight: 500, fontSize: '13px' }}>{info.label}</div>
                  <div style={{ fontSize: '11px', color: '#999' }}>{info.description}</div>
                </div>
              </div>
            </Card>
          ))}
        </div>

        {/* React Flow画布 */}
        <div className="reactflow-wrapper" ref={reactFlowWrapper} style={{ flex: 1 }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onInit={setReactFlowInstance}
            onDragOver={onDragOver}
            onDrop={onDrop}
            nodeTypes={nodeTypes}
            defaultEdgeOptions={defaultEdgeOptions}
            deleteKeyCode={['Backspace', 'Delete']}
            snapToGrid
            snapGrid={[15, 15]}
          >
            <Background variant="dots" gap={15} size={1} color="#ddd" />
            <Controls />
            <MiniMap
              nodeColor={(node) => {
                const nodeType = node.data?.nodeType;
                return NODE_TYPES[nodeType]?.color || '#999';
              }}
              style={{ background: '#fafafa' }}
            />
          </ReactFlow>
        </div>
      </div>

      {/* 添加节点模态框 */}
      <Modal
        title="添加节点"
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={null}
      >
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', padding: '12px 0' }}>
          {Object.entries(NODE_TYPES).map(([type, info]) => (
            <Card
              key={type}
              hoverable
              onClick={() => onAddNode(type)}
              style={{ borderLeft: `3px solid ${info.color}` }}
              bodyStyle={{ padding: '12px' }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                <span style={{ fontSize: '20px' }}>{info.icon}</span>
                <span style={{ fontWeight: 600 }}>{info.label}</span>
              </div>
              <div style={{ fontSize: '12px', color: '#999' }}>{info.description}</div>
            </Card>
          ))}
        </div>
      </Modal>
    </div>
  );
};

export default WorkflowEditor;
