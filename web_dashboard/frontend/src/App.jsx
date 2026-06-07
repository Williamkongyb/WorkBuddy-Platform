import React, { useState } from 'react';
import { Layout, Menu, ConfigProvider, theme, message } from 'antd';
import {
  DashboardOutlined,
  FunctionOutlined,
  VideoCameraOutlined,
  CloudUploadOutlined,
  RobotOutlined,
  SettingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import zhCN from 'antd/locale/zh_CN';
import WorkflowEditor from './components/WorkflowEditor';
import 'antd/dist/reset.css';
import './App.css';

const { Header, Sider, Content } = Layout;

function App() {
  const [collapsed, setCollapsed] = useState(false);
  const [selectedMenu, setSelectedMenu] = useState('workflow');
  const [messageApi, contextHolder] = message.useMessage();

  // 渲染主内容区
  const renderContent = () => {
    switch (selectedMenu) {
      case 'workflow':
        return <WorkflowEditor />;
      case 'dashboard':
        return (
          <div style={{ padding: 24, textAlign: 'center', marginTop: 100 }}>
            <h2>📊 数据驾驶舱</h2>
            <p>功能开发中...</p>
          </div>
        );
      case 'video':
        return (
          <div style={{ padding: 24, textAlign: 'center', marginTop: 100 }}>
            <h2>🎬 视频生成管理</h2>
            <p>功能开发中...</p>
          </div>
        );
      case 'publish':
        return (
          <div style={{ padding: 24, textAlign: 'center', marginTop: 100 }}>
            <h2>📤 多平台发布</h2>
            <p>功能开发中...</p>
          </div>
        );
      case 'ai':
        return (
          <div style={{ padding: 24, textAlign: 'center', marginTop: 100 }}>
            <h2>🤖 AI超级员工</h2>
            <p>功能开发中...</p>
          </div>
        );
      case 'settings':
        return (
          <div style={{ padding: 24, textAlign: 'center', marginTop: 100 }}>
            <h2>⚙️ 系统设置</h2>
            <p>功能开发中...</p>
          </div>
        );
      default:
        return <WorkflowEditor />;
    }
  };

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: '#1890ff',
          borderRadius: 6,
        },
      }}
    >
      {contextHolder}
      <Layout style={{ height: '100vh' }}>
        {/* 顶部导航 */}
        <Header
          style={{
            background: '#fff',
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
            zIndex: 10,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div
              style={{
                width: 32,
                height: 32,
                background: 'linear-gradient(135deg, #1890ff, #36cfc9)',
                borderRadius: 6,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                fontWeight: 'bold',
                fontSize: 16,
              }}
            >
              W
            </div>
            <h1
              style={{
                margin: 0,
                fontSize: 18,
                background: 'linear-gradient(90deg, #1890ff, #36cfc9)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              WorkBuddy 智能中台 v4.0
            </h1>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <span
              style={{
                background: '#f6ffed',
                color: '#52c41a',
                padding: '4px 12px',
                borderRadius: 12,
                fontSize: 13,
                border: '1px solid #b7eb8f',
              }}
            >
              ● 系统运行中
            </span>
          </div>
        </Header>

        <Layout>
          {/* 左侧菜单 */}
          <Sider
            width={220}
            collapsedWidth={64}
            collapsed={collapsed}
            style={{
              background: '#fff',
              borderRight: '1px solid #f0f0f0',
            }}
          >
            <Menu
              mode="inline"
              selectedKeys={[selectedMenu]}
              onClick={({ key }) => setSelectedMenu(key)}
              style={{ height: '100%', borderRight: 0 }}
              items={[
                {
                  key: 'workflow',
                  icon: <FunctionOutlined />,
                  label: '工作流编排',
                },
                {
                  key: 'dashboard',
                  icon: <DashboardOutlined />,
                  label: '数据驾驶舱',
                },
                {
                  key: 'video',
                  icon: <VideoCameraOutlined />,
                  label: '视频生成',
                },
                {
                  key: 'publish',
                  icon: <CloudUploadOutlined />,
                  label: '多平台发布',
                },
                {
                  key: 'ai',
                  icon: <RobotOutlined />,
                  label: 'AI超级员工',
                },
                {
                  key: 'settings',
                  icon: <SettingOutlined />,
                  label: '系统设置',
                },
              ]}
            />
            <div
              style={{
                position: 'absolute',
                bottom: 16,
                left: 0,
                right: 0,
                textAlign: 'center',
              }}
            >
              <button
                onClick={() => setCollapsed(!collapsed)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: '#999',
                  fontSize: 16,
                }}
              >
                {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              </button>
            </div>
          </Sider>

          {/* 主内容区 */}
          <Content
            style={{
              overflow: 'auto',
              background: '#f5f5f5',
            }}
          >
            {renderContent()}
          </Content>
        </Layout>
      </Layout>
    </ConfigProvider>
  );
}

export default App;
