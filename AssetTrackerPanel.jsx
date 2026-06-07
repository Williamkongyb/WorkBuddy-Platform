import React, { useState, useEffect, useCallback, memo } from 'react';

// =============================================
// 配置：修改此处 IP 为你台式机的局域网地址
// =============================================
const API_BASE = 'http://192.168.1.208:8000';

const PLATFORM_MAP = {
  douyin:      { label: '抖音',       color: '#ff0050', icon: '🎵' },
  xiaohongshu: { label: '小红书',     color: '#ff2442', icon: '📕' },
  bilibili:    { label: '哔哩哔哩',   color: '#00a1d6', icon: '🎬' },
  shipinhao:   { label: '视频号',     color: '#07c160', icon: '💚' },
  unknown:     { label: '未知平台',   color: '#999',    icon: '📹' },
};

// =============================================
// 类型定义（仅文档用，JSX 无类型约束）
// =============================================
/*
Asset {
  id: string, filename: string, url: string,
  platform: string, size_mb: number, created: string, modified: string
}
Task {
  id: string, script_name: string, status: 'queued'|'rendering'|'completed',
  progress: number, platform?: string, created: string
}
*/


// =============================================
// API 调用层：封装 fetch，统一 CORS 错误处理
// =============================================
async function apiFetch(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  try {
    const response = await fetch(url, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...options.headers },
      // 跨设备请求不需要 credentials
      credentials: 'omit',
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    // 如果是视频流，返回 blob URL
    if (endpoint.startsWith('/api/assets/') && !options.headers?.['Range']) {
      const blob = await response.blob();
      return URL.createObjectURL(blob);
    }

    return await response.json();
  } catch (error) {
    // CORS 错误特殊提示
    if (error.message.includes('Failed to fetch') || error.name === 'TypeError') {
      console.error(
        `[CORS/Network Error] 无法连接到 ${url}\n` +
        '请确认：\n' +
        '1. 台式机已启动 asset_server.py\n' +
        '2. 防火墙已放行端口 8000\n' +
        '3. API_BASE 地址正确\n' +
        `当前 API_BASE: ${API_BASE}`
      );
    }
    throw error;
  }
}


// =============================================
// 自定义 Hook：封装数据获取逻辑
// =============================================
function useApiData(endpoint, intervalMs = 0) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setError(null);
      const result = await apiFetch(endpoint);
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [endpoint]);

  useEffect(() => {
    fetchData();
    if (intervalMs > 0) {
      const timer = setInterval(fetchData, intervalMs);
      return () => clearInterval(timer);
    }
  }, [fetchData, intervalMs]);

  return { data, loading, error, refetch: fetchData };
}


// =============================================
// VideoCard — React.memo 优化性能
// =============================================
const VideoCard = memo(function VideoCard({ asset, onPlay }) {
  const platform = PLATFORM_MAP[asset.platform] || PLATFORM_MAP.unknown;

  return (
    <div
      className="video-card"
      onClick={() => onPlay(asset)}
      style={styles.card}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-4px)';
        e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.15)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)';
      }}
    >
      {/* 缩略图占位区 */}
      <div style={styles.thumbnail}>
        <span style={styles.playIcon}>▶</span>
        <div style={{ ...styles.platformBadge, backgroundColor: platform.color }}>
          {platform.icon} {platform.label}
        </div>
      </div>

      {/* 文件信息 */}
      <div style={styles.cardBody}>
        <div style={styles.filename} title={asset.filename}>
          {asset.filename}
        </div>
        <div style={styles.meta}>
          <span>{asset.size_mb} MB</span>
          <span>{new Date(asset.created).toLocaleDateString('zh-CN')}</span>
        </div>
      </div>
    </div>
  );
});


// =============================================
// VideoPlayer — 模态播放器
// =============================================
function VideoPlayer({ asset, onClose }) {
  const videoUrl = `${API_BASE}${asset.url}`;

  // 点击遮罩关闭
  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) onClose();
  };

  // ESC 键关闭
  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [onClose]);

  return (
    <div style={styles.modalBackdrop} onClick={handleBackdropClick}>
      <div style={styles.modalContent}>
        <div style={styles.modalHeader}>
          <h3 style={styles.modalTitle}>{asset.filename}</h3>
          <button onClick={onClose} style={styles.modalClose}>✕</button>
        </div>
        <video
          src={videoUrl}
          controls
          autoPlay
          style={styles.video}
          controlsList="nodownload"
          crossOrigin="anonymous"
          onError={(e) => console.error('视频加载失败:', e)}
        >
          您的浏览器不支持视频播放。
        </video>
        <div style={styles.modalInfo}>
          <span>大小: {asset.size_mb} MB</span>
          <span>平台: {(PLATFORM_MAP[asset.platform] || PLATFORM_MAP.unknown).label}</span>
          <span>创建: {new Date(asset.created).toLocaleString('zh-CN')}</span>
        </div>
      </div>
    </div>
  );
}


// =============================================
// TaskList — 任务状态追踪区
// =============================================
function TaskList({ tasks, loading }) {
  const statusConfig = {
    completed:  { label: '已完成', color: '#52c41a', bg: '#f6ffed', icon: '✅' },
    rendering:  { label: '渲染中', color: '#1890ff', bg: '#e6f7ff', icon: '🔄' },
    queued:     { label: '排队中', color: '#faad14', bg: '#fffbe6', icon: '⏳' },
    failed:     { label: '失败',   color: '#ff4d4f', bg: '#fff2e8', icon: '❌' },
  };

  if (loading) {
    return <div style={styles.empty}>加载中...</div>;
  }

  if (!tasks || tasks.length === 0) {
    return <div style={styles.empty}>暂无任务</div>;
  }

  return (
    <div style={styles.taskList}>
      {tasks.map((task) => {
        const config = statusConfig[task.status] || statusConfig.queued;
        const platform = task.platform ? (PLATFORM_MAP[task.platform] || PLATFORM_MAP.unknown) : null;

        return (
          <div key={task.id} style={{ ...styles.taskItem, borderLeftColor: config.color }}>
            <div style={styles.taskHeader}>
              <span style={styles.taskId}>#{task.id}</span>
              {platform && (
                <span style={{ ...styles.taskPlatform, color: platform.color }}>
                  {platform.icon}
                </span>
              )}
              <span style={{ ...styles.taskStatus, color: config.color, backgroundColor: config.bg }}>
                {config.icon} {config.label}
              </span>
            </div>

            <div style={styles.taskScript} title={task.script_name}>
              {task.script_name}
            </div>

            {/* 进度条 */}
            {task.status === 'rendering' && (
              <div style={styles.progressBar}>
                <div style={{ ...styles.progressFill, width: `${task.progress}%` }} />
                <span style={styles.progressText}>{task.progress}%</span>
              </div>
            )}

            <div style={styles.taskTime}>
              {new Date(task.created).toLocaleString('zh-CN')}
            </div>
          </div>
        );
      })}
    </div>
  );
}


// =============================================
// 错误提示组件
// =============================================
function ErrorBanner({ message, onRetry }) {
  return (
    <div style={styles.errorBanner}>
      <div style={styles.errorIcon}>⚠️</div>
      <div style={styles.errorContent}>
        <div style={styles.errorTitle}>连接失败</div>
        <div style={styles.errorMsg}>{message}</div>
        <div style={styles.errorHint}>
          请确认台式机已启动: <code>python asset_server.py</code><br />
          目标地址: <code>{API_BASE}</code>
        </div>
      </div>
      {onRetry && (
        <button onClick={onRetry} style={styles.retryBtn}>重试</button>
      )}
    </div>
  );
}


// =============================================
// AssetTrackerPanel — 主组件
// =============================================
export default function AssetTrackerPanel() {
  const [activeTab, setActiveTab] = useState('assets');
  const [playingAsset, setPlayingAsset] = useState(null);

  // 每 10 秒自动刷新资源列表和任务状态
  const { data: assetsData, loading: assetsLoading, error: assetsError, refetch: refetchAssets } =
    useApiData('/api/assets', 10000);

  const { data: tasksData, loading: tasksLoading, error: tasksError, refetch: refetchTasks } =
    useApiData('/api/tasks', 10000);

  // 合并错误信息
  const activeError = assetsError || tasksError;
  const handleRetry = () => { refetchAssets(); refetchTasks(); };

  // 渲染视频网格
  const renderAssetsGrid = () => {
    if (assetsLoading) {
      return <div style={styles.empty}>正在加载媒体资产...</div>;
    }
    if (assetsError) {
      return <ErrorBanner message={assetsError} onRetry={handleRetry} />;
    }
    if (!assetsData?.assets?.length) {
      return (
        <div style={styles.empty}>
          <div style={{ fontSize: 48 }}>📭</div>
          <p>暂无视频文件</p>
          <p style={{ fontSize: 12, color: '#999' }}>
            请确认台式机的 {API_BASE} 可访问，且 final_videos 目录中有 .mp4 文件
          </p>
        </div>
      );
    }

    return (
      <div style={styles.grid}>
        {assetsData.assets.map((asset) => (
          <VideoCard key={asset.id} asset={asset} onPlay={setPlayingAsset} />
        ))}
      </div>
    );
  };

  return (
    <div style={styles.panel}>
      {/* ---- 头部 ---- */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <span style={styles.logo}>🎬</span>
          <h2 style={styles.title}>AssetTrackerPanel</h2>
          <span style={styles.subtitle}>媒体资产管理控制台</span>
        </div>
        <div style={styles.headerRight}>
          <span style={styles.serverAddr}>{API_BASE}</span>
          <button onClick={handleRetry} style={styles.refreshBtn}>🔄 刷新</button>
        </div>
      </div>

      {/* ---- 标签栏 ---- */}
      <div style={styles.tabBar}>
        <button
          style={{ ...styles.tab, ...(activeTab === 'assets' ? styles.tabActive : {}) }}
          onClick={() => setActiveTab('assets')}
        >
          🎞️ 媒体资产 ({assetsData?.total ?? '...'})
        </button>
        <button
          style={{ ...styles.tab, ...(activeTab === 'tasks' ? styles.tabActive : {}) }}
          onClick={() => setActiveTab('tasks')}
        >
          📋 任务状态 ({tasksData?.total ?? '...'})
        </button>
      </div>

      {/* ---- 全局错误提示 ---- */}
      {activeError && activeTab === 'assets' && assetsError && (
        <ErrorBanner message={assetsError} onRetry={handleRetry} />
      )}

      {/* ---- 内容区 ---- */}
      <div style={styles.content}>
        {activeTab === 'assets' ? renderAssetsGrid() : (
          tasksError ? (
            <ErrorBanner message={tasksError} onRetry={handleRetry} />
          ) : (
            <TaskList tasks={tasksData?.tasks} loading={tasksLoading} />
          )
        )}
      </div>

      {/* ---- 状态栏 ---- */}
      <div style={styles.statusBar}>
        <span>🟢 服务 {assetsError || tasksError ? '离线' : '在线'}</span>
        <span>自动刷新: 10秒</span>
        <span>{new Date().toLocaleTimeString('zh-CN')}</span>
      </div>

      {/* ---- 播放器弹窗 ---- */}
      {playingAsset && (
        <VideoPlayer asset={playingAsset} onClose={() => setPlayingAsset(null)} />
      )}
    </div>
  );
}


// =============================================
// 内联样式（生产中建议使用 CSS Modules 或 Tailwind）
// =============================================
const styles = {
  panel: {
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif",
    background: '#f0f2f5',
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
  },

  // Header
  header: {
    background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
    color: 'white',
    padding: '14px 24px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerLeft: { display: 'flex', alignItems: 'center', gap: '10px' },
  logo: { fontSize: '24px' },
  title: { fontSize: '18px', fontWeight: 600, margin: 0 },
  subtitle: { fontSize: '13px', color: 'rgba(255,255,255,0.65)' },
  headerRight: { display: 'flex', alignItems: 'center', gap: '12px', fontSize: '13px' },
  serverAddr: {
    background: 'rgba(255,255,255,0.12)',
    padding: '4px 10px',
    borderRadius: '4px',
    fontFamily: 'monospace',
    fontSize: '12px',
  },
  refreshBtn: {
    background: 'rgba(255,255,255,0.15)',
    border: 'none',
    color: 'white',
    padding: '6px 14px',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '13px',
  },

  // Tab Bar
  tabBar: {
    display: 'flex',
    background: '#fff',
    borderBottom: '1px solid #e8e8e8',
    padding: '0 24px',
  },
  tab: {
    padding: '14px 20px',
    border: 'none',
    background: 'none',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 500,
    color: '#666',
    borderBottom: '2px solid transparent',
    transition: 'all 0.2s',
  },
  tabActive: {
    color: '#667eea',
    borderBottomColor: '#667eea',
  },

  // Content
  content: {
    flex: 1,
    padding: '20px 24px',
    overflowY: 'auto',
  },
  empty: {
    textAlign: 'center',
    padding: '60px 20px',
    color: '#999',
    fontSize: '14px',
  },

  // Grid
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
    gap: '16px',
  },

  // Card
  card: {
    background: '#fff',
    borderRadius: '10px',
    overflow: 'hidden',
    boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
    cursor: 'pointer',
    transition: 'transform 0.2s, box-shadow 0.2s',
  },
  thumbnail: {
    height: '135px',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  playIcon: {
    fontSize: '40px',
    color: 'rgba(255,255,255,0.8)',
    transition: 'transform 0.2s',
  },
  platformBadge: {
    position: 'absolute',
    top: '8px',
    right: '8px',
    color: 'white',
    padding: '2px 8px',
    borderRadius: '4px',
    fontSize: '11px',
    fontWeight: 600,
  },
  cardBody: { padding: '12px' },
  filename: {
    fontSize: '13px',
    fontWeight: 600,
    color: '#333',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  meta: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '11px',
    color: '#999',
    marginTop: '6px',
  },

  // Modal
  modalBackdrop: {
    position: 'fixed',
    top: 0, left: 0, right: 0, bottom: 0,
    background: 'rgba(0,0,0,0.7)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  modalContent: {
    background: '#fff',
    borderRadius: '12px',
    width: '90%',
    maxWidth: '900px',
    maxHeight: '90vh',
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
  },
  modalHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '14px 20px',
    borderBottom: '1px solid #e8e8e8',
  },
  modalTitle: { fontSize: '15px', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  modalClose: {
    background: 'none',
    border: 'none',
    fontSize: '20px',
    cursor: 'pointer',
    color: '#999',
    padding: '4px 8px',
  },
  video: {
    width: '100%',
    maxHeight: '500px',
    background: '#000',
  },
  modalInfo: {
    display: 'flex',
    gap: '20px',
    padding: '12px 20px',
    fontSize: '12px',
    color: '#666',
    borderTop: '1px solid #e8e8e8',
  },

  // Task List
  taskList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
    maxWidth: '800px',
  },
  taskItem: {
    background: '#fff',
    borderRadius: '8px',
    padding: '14px 16px',
    borderLeft: '4px solid #ccc',
    boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
  },
  taskHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '6px',
  },
  taskId: {
    fontFamily: 'monospace',
    fontSize: '12px',
    color: '#999',
  },
  taskPlatform: { fontSize: '14px' },
  taskStatus: {
    marginLeft: 'auto',
    padding: '2px 10px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: 600,
  },
  taskScript: {
    fontSize: '13px',
    color: '#333',
    marginBottom: '6px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  progressBar: {
    height: '6px',
    background: '#f0f0f0',
    borderRadius: '3px',
    overflow: 'hidden',
    marginBottom: '6px',
    position: 'relative',
  },
  progressFill: {
    height: '100%',
    background: 'linear-gradient(90deg, #667eea, #764ba2)',
    borderRadius: '3px',
    transition: 'width 0.5s ease',
  },
  progressText: {
    position: 'absolute',
    right: '4px',
    top: '-18px',
    fontSize: '11px',
    color: '#667eea',
    fontWeight: 600,
  },
  taskTime: {
    fontSize: '11px',
    color: '#bbb',
  },

  // Error Banner
  errorBanner: {
    display: 'flex',
    alignItems: 'center',
    gap: '14px',
    background: '#fff2e8',
    border: '1px solid #ffbb96',
    borderRadius: '8px',
    padding: '14px 20px',
    margin: '12px 0',
  },
  errorIcon: { fontSize: '28px' },
  errorContent: { flex: 1 },
  errorTitle: { fontWeight: 600, color: '#ff4d4f', marginBottom: '4px' },
  errorMsg: { fontSize: '13px', color: '#666' },
  errorHint: { fontSize: '12px', color: '#999', marginTop: '6px' },
  retryBtn: {
    background: '#ff4d4f',
    color: 'white',
    border: 'none',
    padding: '8px 16px',
    borderRadius: '6px',
    cursor: 'pointer',
    fontWeight: 500,
  },

  // Status Bar
  statusBar: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '8px 24px',
    background: '#fafafa',
    borderTop: '1px solid #e8e8e8',
    fontSize: '12px',
    color: '#999',
  },
};
