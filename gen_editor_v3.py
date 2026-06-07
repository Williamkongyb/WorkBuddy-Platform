#!/usr/bin/env python3
# 生成 workflow_editor_v3.html - 完整可拖拽工作流编辑器
import os

html = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>工作流编排器 v3.1 — DAG可视化编辑器</title>
<style>
:root{--bg:#1a1a2e;--surface:#16213e;--accent:#667eea;--success:#52c41a;--warn:#faad14;--danger:#ff4d4f;--info:#1890ff;--grid:#1e2935;--nodebg:#1e293b;--border:#2a3a5c;--text:#e0e0e0;--text2:#8899aa;}
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;background:var(--bg);color:var(--text);overflow:hidden;height:100vh;user-select:none;}
.header{height:48px;background:var(--surface);border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;padding:0 16px;z-index:100;position:relative;}
.header-left{display:flex;align-items:center;gap:10px;}
.header-title{font-size:15px;font-weight:600;}
.header-badge{background:rgba(102,126,234,0.2);padding:2px 8px;border-radius:8px;font-size:11px;color:var(--accent);}
.header-actions{display:flex;gap:6px;}
.btn{padding:6px 14px;border:1px solid var(--border);border-radius:6px;background:var(--surface);color:var(--text);cursor:pointer;font-size:12px;font-weight:500;transition:all 0.2s;font-family:inherit;}
.btn:hover{border-color:var(--accent);}
.btn-accent{background:var(--accent);border-color:var(--accent);color:#fff;}
.btn-success{background:var(--success);border-color:var(--success);color:#fff;}
.btn-danger{background:var(--danger);border-color:var(--danger);color:#fff;}
.main{display:flex;height:calc(100vh - 48px - 28px);}
.sidebar{width:260px;background:var(--surface);border-right:1px solid var(--border);overflow-y:auto;padding:8px;flex-shrink:0;}
.sidebar h3{font-size:11px;text-transform:uppercase;color:var(--text2);letter-spacing:1px;padding:8px 4px 4px;border-bottom:1px solid var(--border);margin-top:4px;}
.node-tpl{background:var(--nodebg);border:1px solid var(--border);border-radius:8px;padding:10px;margin-bottom:6px;cursor:grab;display:flex;align-items:center;gap:10px;transition:all 0.2s;user-select:none;}
.node-tpl:hover{border-color:var(--accent);box-shadow:0 0 12px rgba(102,126,234,0.15);}
.node-tpl:active{cursor:grabbing;}
.node-tpl.dragging{opacity:0.4;}
.nt-icon{font-size:20px;flex-shrink:0;}
.nt-info{flex:1;min-width:0;}
.nt-name{font-size:12px;font-weight:600;}
.nt-desc{font-size:10px;color:var(--text2);}
.nt-tag{font-size:9px;padding:1px 5px;border-radius:3px;display:inline-block;margin-top:2px;}
.tag-t{background:rgba(82,196,26,0.15);color:var(--success);}
.tag-a{background:rgba(102,126,234,0.15);color:var(--accent);}
.tag-c{background:rgba(250,173,20,0.15);color:var(--warn);}
.tag-i{background:rgba(24,144,255,0.15);color:var(--info);}
.tag-o{background:rgba(255,77,79,0.15);color:var(--danger);}
.canvas-wrap{flex:1;position:relative;overflow:hidden;background:var(--bg);cursor:grab;}
.canvas-wrap.grabbing{cursor:grabbing;}
.canvas-wrap.connecting{cursor:crosshair;}
.canvas-layer{position:absolute;top:0;left:0;transform-origin:0 0;}
.grid-dot{position:absolute;width:2px;height:2px;background:var(--grid);border-radius:50%;}
.lines-svg{position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:2;}
.lines-svg line{pointer-events:stroke;cursor:pointer;}
.lines-svg line:hover{stroke:var(--danger)!important;}
.temp-line{pointer-events:none;stroke:var(--accent);stroke-width:2;stroke-dasharray:6 3;}
.wf-node{position:absolute;min-width:150px;max-width:220px;background:var(--nodebg);border:2px solid var(--border);border-radius:10px;cursor:move;z-index:10;transition:box-shadow 0.2s;}
.wf-node:hover{z-index:20;}
.wf-node.selected{border-color:var(--accent);box-shadow:0 0 0 3px rgba(102,126,234,0.2);}
.wf-node.executing{border-color:var(--info);box-shadow:0 0 12px rgba(24,144,255,0.3);}
.wf-node.success{border-color:var(--success);}
.wf-node.error{border-color:var(--danger);box-shadow:0 0 12px rgba(255,77,79,0.3);}
.wf-node-header{padding:8px 10px 4px;display:flex;align-items:center;gap:6px;border-bottom:1px solid var(--border);}
.wf-node-icon{font-size:16px;}
.wf-node-title{font-size:12px;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.wf-node-body{padding:6px 10px;font-size:10px;color:var(--text2);}
.wf-node-status{margin:0 10px 6px;padding:3px 6px;border-radius:4px;font-size:9px;text-align:center;font-weight:500;}
.status-ready{background:rgba(136,153,170,0.1);color:var(--text2);}
.status-running{background:rgba(24,144,255,0.1);color:var(--info);}
.status-done{background:rgba(82,196,26,0.1);color:var(--success);}
.status-fail{background:rgba(255,77,79,0.1);color:var(--danger);}
.connector{position:absolute;width:14px;height:14px;background:var(--accent);border:2px solid var(--nodebg);border-radius:50%;cursor:crosshair;z-index:30;transition:transform 0.15s,box-shadow 0.15s;}
.connector:hover{transform:scale(1.4);box-shadow:0 0 8px rgba(102,126,234,0.6);}
.connector.in{top:-7px;left:50%;margin-left:-7px;}
.connector.out{bottom:-7px;left:50%;margin-left:-7px;}
.ghost{position:fixed;pointer-events:none;z-index:9999;opacity:0.85;transform:scale(0.9);}
.minimap{position:absolute;bottom:10px;right:10px;width:160px;height:100px;background:var(--surface);border:1px solid var(--border);border-radius:8px;overflow:hidden;z-index:50;opacity:0.75;transition:opacity 0.2s;}
.minimap:hover{opacity:1;}
.minimap canvas{display:block;}
.minimap-vp{position:absolute;border:2px solid var(--accent);background:rgba(102,126,234,0.08);pointer-events:none;}
.zoom-ctrl{position:absolute;bottom:10px;left:50%;transform:translateX(-50%);display:flex;gap:4px;z-index:50;}
.zb{width:30px;height:30px;background:var(--surface);border:1px solid var(--border);border-radius:6px;color:var(--text);cursor:pointer;font-size:14px;display:flex;align-items:center;justify-content:center;}
.zb:hover{border-color:var(--accent);}
.exec-log{position:absolute;bottom:10px;left:10px;width:400px;max-height:200px;background:#0d1117;border:1px solid var(--border);border-radius:8px;padding:8px;overflow-y:auto;z-index:50;font-family:'Consolas',monospace;font-size:10px;color:#7ee787;display:none;}
.status-bar{height:28px;background:var(--surface);border-top:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;padding:0 14px;font-size:11px;color:var(--text2);flex-shrink:0;}
.toast{position:fixed;top:56px;right:20px;padding:8px 16px;border-radius:8px;font-size:13px;color:#fff;z-index:999;animation:slideIn 0.3s ease;box-shadow:0 4px 16px rgba(0,0,0,0.3);}
.toast.ok{background:var(--success);}
.toast.err{background:var(--danger);}
@keyframes slideIn{from{opacity:0;transform:translateX(20px);}to{opacity:1;transform:translateX(0);}}
</style>
</head>
<body>
<div class="header">
  <div class="header-left">
    <span style="font-size:20px">🔧</span>
    <span class="header-title">工作流编排器</span>
    <span class="header-badge">v3.1 DAG</span>
  </div>
  <div class="header-actions">
    <button class="btn btn-sm" onclick="app.newWf()">📄 新建</button>
    <button class="btn btn-sm" onclick="app.saveWf()">💾 保存</button>
    <button class="btn btn-sm" onclick="app.loadWf()">📂 加载</button>
    <button class="btn btn-sm" onclick="app.exportJSON()">📤 导出</button>
    <button class="btn btn-sm" onclick="app.importJSON()">📥 导入</button>
    <button class="btn btn-success btn-sm" onclick="app.execute()">▶ 执行</button>
    <button class="btn btn-sm" onclick="app.toggleLog()">📋 日志</button>
    <button class="btn btn-danger btn-sm" onclick="app.delSel()" id="btnDel" disabled>🗑 删除</button>
  </div>
</div>
<div class="main" id="mainBox">
  <div class="sidebar" id="sidebar">
    <h3>⏰ 触发器</h3>
    <div class="node-tpl" data-t="timer" data-label="定时触发" data-icon="⏰" data-desc="Cron定时启动"><span class="nt-icon">⏰</span><div class="nt-info"><div class="nt-name">定时触发</div><div class="nt-desc">Cron定时</div><span class="nt-tag tag-t">触发</span></div></div>
    <div class="node-tpl" data-t="manual" data-label="手动触发" data-icon="👆" data-desc="手动启动"><span class="nt-icon">👆</span><div class="nt-info"><div class="nt-name">手动触发</div><div class="nt-desc">手动启动</div><span class="nt-tag tag-t">触发</span></div></div>
    <div class="node-tpl" data-t="webhook" data-label="Webhook触发" data-icon="🌐" data-desc="HTTP回调"><span class="nt-icon">🌐</span><div class="nt-info"><div class="nt-name">Webhook触发</div><div class="nt-desc">HTTP回调</div><span class="nt-tag tag-t">触发</span></div></div>
    <div class="node-tpl" data-t="hotspot" data-label="热点监控" data-icon="🔥" data-desc="热点话题抓取"><span class="nt-icon">🔥</span><div class="nt-info"><div class="nt-name">热点监控</div><div class="nt-desc">热点抓取</div><span class="nt-tag tag-t">触发</span></div></div>
    <h3>⚡ 动作</h3>
    <div class="node-tpl" data-t="gen_script" data-label="智能文案生成" data-icon="📝" data-desc="4平台文案"><span class="nt-icon">📝</span><div class="nt-info"><div class="nt-name">智能文案生成</div><div class="nt-desc">4平台差异化</div><span class="nt-tag tag-a">动作</span></div></div>
    <div class="node-tpl" data-t="make_video" data-label="视频制作" data-icon="🎬" data-desc="双引擎渲染"><span class="nt-icon">🎬</span><div class="nt-info"><div class="nt-name">视频自动制作</div><div class="nt-desc">剪映/Seedance</div><span class="nt-tag tag-a">动作</span></div></div>
    <div class="node-tpl" data-t="publish" data-label="多平台发布" data-icon="🚀" data-desc="RPA自动发布"><span class="nt-icon">🚀</span><div class="nt-info"><div class="nt-name">多平台发布</div><div class="nt-desc">RPA自动发布</div><span class="nt-tag tag-a">动作</span></div></div>
    <div class="node-tpl" data-t="monitor" data-label="数据监控" data-icon="📊" data-desc="播放量/点赞"><span class="nt-icon">📊</span><div class="nt-info"><div class="nt-name">数据监控采集</div><div class="nt-desc">全维度指标</div><span class="nt-tag tag-a">动作</span></div></div>
    <h3>🔀 条件</h3>
    <div class="node-tpl" data-t="compliance" data-label="合规审查" data-icon="🔍" data-desc="违禁词扫描"><span class="nt-icon">🔍</span><div class="nt-info"><div class="nt-name">合规审查</div><div class="nt-desc">5平台规则</div><span class="nt-tag tag-c">条件</span></div></div>
    <div class="node-tpl" data-t="push_idx" data-label="推流指数" data-icon="🎯" data-desc="阈值判断"><span class="nt-icon">🎯</span><div class="nt-info"><div class="nt-name">推流指数评估</div><div class="nt-desc">阈值判断</div><span class="nt-tag tag-c">条件</span></div></div>
    <div class="node-tpl" data-t="anomaly" data-label="异常预警" data-icon="⚠️" data-desc="限流检测"><span class="nt-icon">⚠️</span><div class="nt-info"><div class="nt-name">异常预警</div><div class="nt-desc">限流检测</div><span class="nt-tag tag-c">条件</span></div></div>
    <h3>🔗 集成</h3>
    <div class="node-tpl" data-t="ai_analysis" data-label="AI归因分析" data-icon="🧠" data-desc="LLM策略建议"><span class="nt-icon">🧠</span><div class="nt-info"><div class="nt-name">AI归因分析</div><div class="nt-desc">LLM建议</div><span class="nt-tag tag-i">集成</span></div></div>
    <div class="node-tpl" data-t="notify" data-label="消息通知" data-icon="💬" data-desc="企微/钉钉推送"><span class="nt-icon">💬</span><div class="nt-info"><div class="nt-name">消息通知</div><div class="nt-desc">企微/钉钉</div><span class="nt-tag tag-i">集成</span></div></div>
    <h3>📤 输出</h3>
    <div class="node-tpl" data-t="report" data-label="生成报告" data-icon="📄" data-desc="MD/Word报告"><span class="nt-icon">📄</span><div class="nt-info"><div class="nt-name">生成复盘报告</div><div class="nt-desc">MD/Word</div><span class="nt-tag tag-o">输出</span></div></div>
  </div>
  <div class="canvas-wrap" id="canvasWrap">
    <div class="canvas-layer" id="canvasLayer">
      <svg class="lines-svg" id="linesSvg">
        <defs>
          <marker id="ah" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#667eea"/></marker>
          <marker id="ahr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#52c41a"/></marker>
        </defs>
        <g id="linesGroup"></g>
        <g id="tempLineG"></g>
      </svg>
      <div id="nodesBox"></div>
    </div>
    <div class="minimap" id="minimap"><canvas id="miniCanvas" width="160" height="100"></canvas><div class="minimap-vp" id="miniVp"></div></div>
    <div class="zoom-ctrl">
      <button class="zb" onclick="app.zoomIn()">＋</button>
      <button class="zb" onclick="app.zoomReset()" style="font-size:10px">100%</button>
      <button class="zb" onclick="app.zoomOut()">－</button>
    </div>
    <div class="exec-log" id="execLog"></div>
  </div>
</div>
<div class="status-bar">
  <span id="statusLeft">节点: <strong id="nodeCnt">0</strong> | 连线: <strong id="edgeCnt">0</strong></span>
  <span id="statusHint">✋ 中键/空格+拖=平移 | 滚轮=缩放 | 侧边栏拖入=添加 | 点击端口=连线</span>
</div>
<div class="toast" id="toast" style="display:none"></div>

<script>
// ===== 工作流编排器 v3.1 — 完整DAG引擎 =====
const STORE_KEY='wf_editor_v31';

class WFEditor{
  constructor(){
    this.nodes=[]; this.edges=[]; this.sel=null;
    this.nid=1; this.eid=1;
    this.zoom=1; this.px=0; this.py=0;
    this.executing=false; this.logs=[]; this.showLog=false;
    // drag state
    this.mode=null; // pan|node|connect|sidebarDrag
    this.dragTarget=null;
    this.dsx=0; this.dsy=0; this.dox=0; this.doy=0;
    this.connectFrom=null;
    this.ghost=null; // sidebar drag ghost
    // DOM
    this.wrap=document.getElementById('canvasWrap');
    this.layer=document.getElementById('canvasLayer');
    this.nodesBox=document.getElementById('nodesBox');
    this.linesSvg=document.getElementById('linesSvg');
    this.linesG=document.getElementById('linesGroup');
    this.tempG=document.getElementById('tempLineG');
    // Init
    this.renderGrid();
    this.bindEvents();
    this.renderAll();
    this.upStatus();
  }

  // ===== Grid =====
  renderGrid(){
    const frag=document.createDocumentFragment();
    for(let x=0;x<5000;x+=40) for(let y=0;y<5000;y+=40){
      const d=document.createElement('div'); d.className='grid-dot';
      d.style.left=x+'px'; d.style.top=y+'px'; frag.appendChild(d);
    }
    this.layer.appendChild(frag);
  }

  // ===== Event Binding =====
  bindEvents(){
    const w=this.wrap;
    // Canvas mousedown: pan or deselect
    w.addEventListener('mousedown',e=>{
      if(e.target===w||e.target===this.layer||e.target.tagName==='svg'||e.target.classList.contains('grid-dot')){
        if(e.button===1||(e.button===0&&e.ctrlKey)){this.startPan(e);e.preventDefault();return;}
        if(e.button===0&&!e.ctrlKey){this.sel=null;this.connectFrom=null;this.renderAll();this.upStatus();document.getElementById('btnDel').disabled=true;}
      }
    });
    // Wheel zoom
    w.addEventListener('wheel',e=>{e.preventDefault();const f=e.deltaY>0?0.95:1.05;this.zoomTo(f,e.clientX,e.clientY);},{passive:false});
    // Dblclick on line = delete edge
    this.linesSvg.addEventListener('dblclick',e=>{if(e.target.tagName==='line'){const eid=e.target.dataset.eid;if(eid){this.edges=this.edges.filter(ed=>ed.id!==eid);this.renderAll();this.toast('连线已删除');}}});
    
    // ===== 侧边栏拖拽（自定义实现，不依赖HTML5 Drag API）=====
    document.querySelectorAll('.node-tpl').forEach(tpl=>{
      tpl.addEventListener('mousedown',e=>{
        if(e.button!==0) return;
        e.preventDefault();
        const data={t:tpl.dataset.t,label:tpl.dataset.label,icon:tpl.dataset.icon,desc:tpl.dataset.desc};
        // 创建幽灵元素
        const ghost=document.createElement('div');
        ghost.className='ghost';
        ghost.style.cssText=`background:var(--nodebg);border:2px solid var(--accent);border-radius:10px;padding:10px 16px;font-size:13px;color:var(--text);box-shadow:0 8px 24px rgba(102,126,234,0.4);`;
        ghost.innerHTML=`<span style="font-size:18px">${data.icon}</span> ${data.label}`;
        document.body.appendChild(ghost);
        this.ghost=ghost;
        this.mode='sidebarDrag';
        this._sdData=data;
        this._sdOx=e.clientX; this._sdOy=e.clientY;
        tpl.classList.add('dragging');
        this._sdTpl=tpl;
        const onMove=ev=>{ghost.style.left=(ev.clientX-40)+'px';ghost.style.top=(ev.clientY-20)+'px';};
        const onUp=ev=>{
          document.removeEventListener('mousemove',onMove);
          document.removeEventListener('mouseup',onUp);
          ghost.remove();this.ghost=null;this.mode=null;
          tpl.classList.remove('dragging');
          // 判断是否落在画布上
          const rect=w.getBoundingClientRect();
          if(ev.clientX>=rect.left&&ev.clientX<=rect.right&&ev.clientY>=rect.top&&ev.clientY<=rect.bottom){
            const x=(ev.clientX-rect.left-this.px)/this.zoom-75;
            const y=(ev.clientY-rect.top-this.py)/this.zoom-18;
            this.addNode(this._sdData.t,this._sdData.label,this._sdData.icon,this._sdData.desc,Math.max(0,x),Math.max(0,y));
          }
        };
        document.addEventListener('mousemove',onMove);
        document.addEventListener('mouseup',onUp);
      });
    });

    // Keyboard
    document.addEventListener('keydown',e=>{
      if(e.target.tagName==='INPUT') return;
      if(e.key==='Delete'||e.key==='Backspace'){e.preventDefault();this.delSel();}
      if(e.ctrlKey&&e.key==='s'){e.preventDefault();this.saveWf();}
      if(e.key==='Escape'){this.connectFrom=null;this.renderAll();}
    });
  }

  // ===== Pan =====
  startPan(e){this.mode='pan';this.dsx=e.clientX-this.px;this.dsy=e.clientY-this.py;this.wrap.classList.add('grabbing');const m=e=>{this.px=e.clientX-this.dsx;this.py=e.clientY-this.dsy;this.renderTransform();this.upMini();};const u=()=>{this.mode=null;this.wrap.classList.remove('grabbing');document.removeEventListener('mousemove',m);document.removeEventListener('mouseup',u);};document.addEventListener('mousemove',m);document.addEventListener('mouseup',u);}

  // ===== Zoom =====
  zoomTo(f,cx,cy){const nz=Math.max(0.2,Math.min(3,this.zoom*f));if(cx!==undefined){const r=this.wrap.getBoundingClientRect();const mx=cx-r.left;const my=cy-r.top;this.px=mx-(mx-this.px)*(nz/this.zoom);this.py=my-(my-this.py)*(nz/this.zoom);}this.zoom=nz;this.renderTransform();this.upMini();document.getElementById('statusHint').textContent=Math.round(this.zoom*100)+'%';setTimeout(()=>document.getElementById('statusHint').textContent='✋ 中键/空格+拖=平移 | 滚轮=缩放 | 侧边栏拖入=添加 | 点击端口=连线',2000);}
  zoomIn(){this.zoomTo(1.15);}
  zoomOut(){this.zoomTo(0.87);}
  zoomReset(){this.zoom=1;this.px=0;this.py=0;this.renderTransform();this.upMini();}
  renderTransform(){this.layer.style.transform=`translate(${this.px}px,${this.py}px) scale(${this.zoom})`;}

  // ===== Nodes =====
  addNode(type,label,icon,desc,x,y){const id='n'+(this.nid++);this.nodes.push({id,type,label,icon,desc,x,y,status:'ready'});this.renderAll();this.toast('已添加: '+label);}
  getNode(id){return this.nodes.find(n=>n.id===id);}

  // ===== Node Drag on Canvas =====
  startNodeDrag(id,cx,cy){this.mode='node';this.dragTarget=id;const n=this.getNode(id);if(!n)return;this.dox=n.x;this.doy=n.y;this.dsx=cx;this.dsy=cy;this.wrap.classList.add('dragging-node');const m=e=>{if(this.mode!=='node')return;const dx=(e.clientX-this.dsx)/this.zoom;const dy=(e.clientY-this.dsy)/this.zoom;const nd=this.getNode(this.dragTarget);if(nd){nd.x=Math.max(0,this.dox+dx);nd.y=Math.max(0,this.doy+dy);this.renderNodes();this.renderLines();}};const u=()=>{this.mode=null;this.dragTarget=null;this.wrap.classList.remove('dragging-node');document.removeEventListener('mousemove',m);document.removeEventListener('mouseup',u);};document.addEventListener('mousemove',m);document.addEventListener('mouseup',u);}

  selectNode(id){if(this.connectFrom&&this.connectFrom.id!==id){this.createEdge(this.connectFrom.id,this.connectFrom.port,id);this.connectFrom=null;}else{this.sel=id;this.renderAll();document.getElementById('btnDel').disabled=false;this.upStatus();}}

  delSel(){if(!this.sel)return;this.nodes=this.nodes.filter(n=>n.id!==this.sel);this.edges=this.edges.filter(e=>e.from!==this.sel&&e.to!==this.sel);this.sel=null;document.getElementById('btnDel').disabled=true;this.renderAll();this.upStatus();this.toast('节点已删除');}

  // ===== Connections =====
  startConnect(nid,port){this.connectFrom={id:nid,port};this.wrap.classList.add('connecting');const m=e=>{if(!this.connectFrom)return;const n=this.getNode(this.connectFrom.id);if(!n)return;const cr=this.wrap.getBoundingClientRect();const nx=(e.clientX-cr.left-this.px)/this.zoom;const ny=(e.clientY-cr.top-this.py)/this.zoom;const fx=n.x+75;const fy=port==='out'?n.y+60:n.y;this.tempG.innerHTML=`<line x1="${fx}" y1="${fy}" x2="${nx}" y2="${ny}" class="temp-line"/>`;};const u=()=>{document.removeEventListener('mousemove',m);document.removeEventListener('mouseup',u);setTimeout(()=>{if(this.connectFrom){this.connectFrom=null;this.wrap.classList.remove('connecting');this.tempG.innerHTML='';this.renderAll();}},120);};document.addEventListener('mousemove',m);document.addEventListener('mouseup',u);this.renderAll();}

  createEdge(fromId,port,toId){if(fromId===toId)return;let f,t;if(port==='out'){f=fromId;t=toId;}else{f=toId;t=fromId;}if(this.edges.find(e=>e.from===f&&e.to===t))return;const id='e'+(this.eid++);this.edges.push({id,from:f,to:t});this.wrap.classList.remove('connecting');this.tempG.innerHTML='';this.renderAll();this.upStatus();this.toast('连线已创建');}

  // ===== Render =====
  renderAll(){this.renderNodes();this.renderLines();this.upMini();this.upStatus();}
  renderNodes(){this.nodesBox.innerHTML='';this.nodes.forEach(n=>{const el=document.createElement('div');el.className='wf-node';if(n.id===this.sel)el.classList.add('selected');if(n.status==='running')el.classList.add('executing');if(n.status==='done')el.classList.add('success');if(n.status==='fail')el.classList.add('error');el.style.left=n.x+'px';el.style.top=n.y+'px';el.dataset.nid=n.id;const sc={'ready':'status-ready','running':'status-running','done':'status-done','fail':'status-fail'};const st={'ready':'等待中','running':'▶ 执行中','done':'✓ 完成','fail':'✗ 失败'};el.innerHTML=`<div class="wf-node-header"><span class="wf-node-icon">${n.icon}</span><span class="wf-node-title">${n.label}</span></div><div class="wf-node-body">${n.desc||''}</div>${n.status!=='ready'?`<div class="wf-node-status ${sc[n.status]}">${st[n.status]}</div>`:''}<div class="connector in" data-nid="${n.id}" data-port="in"></div><div class="connector out" data-nid="${n.id}" data-port="out"></div>`;
    el.addEventListener('click',e=>{e.stopPropagation();this.selectNode(n.id);});
    el.addEventListener('mousedown',e=>{if(e.target.classList.contains('connector'))return;if(e.button===0&&!e.ctrlKey){this.startNodeDrag(n.id,e.clientX,e.clientY);e.stopPropagation();}});
    // Connector events
    el.querySelectorAll('.connector').forEach(c=>{
      c.addEventListener('click',e=>{e.stopPropagation();const nid=c.dataset.nid;const port=c.dataset.port;if(!this.connectFrom){this.startConnect(nid,port);}else{this.selectNode(nid);}});
    });
    this.nodesBox.appendChild(el);
  });}

  renderLines(){this.linesG.innerHTML='';this.edges.forEach(e=>{const n1=this.getNode(e.from);const n2=this.getNode(e.to);if(!n1||!n2)return;const x1=n1.x+75;const y1=n1.y+60;const x2=n2.x+75;const y2=n2.y;const cpx1=x1+(x2-x1)*0.5;const cpx2=x2-(x2-x1)*0.5;const cls=n1.status==='running'&&n2.status==='running'?'temp-line':'';
      const marker=n1.status==='running'&&n2.status==='running'?'url(#ahr)':'url(#ah)';
      this.linesG.innerHTML+=`<path d="M${x1},${y1} C${cpx1},${y1} ${cpx2},${y2} ${x2},${y2}" stroke="${n1.status==='running'&&n2.status==='running'?'#52c41a':'#667eea'}" stroke-width="2" fill="none" marker-end="${marker}" class="${cls}" data-eid="${e.id}" style="pointer-events:stroke;cursor:pointer"/>`;});}

  // ===== Minimap =====
  upMini(){const c=document.getElementById('miniCanvas');if(!c)return;const ctx=c.getContext('2d');ctx.clearRect(0,0,160,100);const sx=160/5000,sy=100/5000;this.nodes.forEach(n=>{ctx.fillStyle='#667eea';ctx.fillRect(n.x*sx,n.y*sy,40*sx,20*sy);});const vp=document.getElementById('miniVp');if(vp){vp.style.left=((-this.px)/this.zoom*sx)+'px';vp.style.top=((-this.py)/this.zoom*sy)+'px';vp.style.width=(this.wrap.clientWidth/this.zoom*sx)+'px';vp.style.height=(this.wrap.clientHeight/this.zoom*sy)+'px';}}

  // ===== Status =====
  upStatus(){document.getElementById('nodeCnt').textContent=this.nodes.length;document.getElementById('edgeCnt').textContent=this.edges.length;}

  // ===== Execute (simulation) =====
  async execute(){if(this.executing)return;if(this.nodes.length===0){this.toast('请先添加节点','err');return;}this.executing=true;document.getElementById('btn-execute').disabled=true;this.logs=[];this.showLog=true;document.getElementById('execLog').style.display='block';const logEl=document.getElementById('execLog');logEl.innerHTML='';const ordered=[...this.nodes];for(const n of ordered){n.status='running';this.renderAll();this.addLog(n.label+' 开始执行...');await new Promise(r=>setTimeout(r,600+Math.random()*400));const ok=Math.random()>0.15;n.status=ok?'done':'fail';this.addLog(n.label+(ok?' ✓ 完成':' ✗ 失败'),!ok);this.renderAll();await new Promise(r=>setTimeout(r,200));}this.executing=false;document.getElementById('btn-execute').disabled=false;this.addLog('🎉 工作流执行完成');this.toast('执行完成');}
  addLog(msg,isErr){const el=document.getElementById('execLog');const d=new Date();const t=d.getHours().toString().padStart(2,'0')+':'+d.getMinutes().toString().padStart(2,'0')+':'+d.getSeconds().toString().padStart(2,'0');const div=document.createElement('div');div.className='log-entry';div.innerHTML=`<span class="log-time">${t}</span><span${isErr?' class="log-error"':''}>${msg}</span>`;el.appendChild(div);el.scrollTop=el.scrollHeight;}
  toggleLog(){this.showLog=!this.showLog;document.getElementById('execLog').style.display=this.showLog?'block':'none';}

  // ===== Save/Load =====
  newWf(){if(this.nodes.length>0&&!confirm('确定新建？当前工作流将丢失'))return;this.nodes=[];this.edges=[];this.sel=null;this.nid=1;this.eid=1;this.renderAll();this.toast('已新建工作流');}
  saveWf(){const data=JSON.stringify({nodes:this.nodes,edges:this.edges,nextNid:this.nid,nextEid:this.eid});localStorage.setItem(STORE_KEY,data);this.toast('已保存到浏览器');}
  loadWf(){const data=localStorage.getItem(STORE_KEY);if(!data){this.toast('没有保存的记录','err');return;}try{const j=JSON.parse(data);this.nodes=j.nodes||[];this.edges=j.edges||[];this.nid=j.nextNid||(this.nodes.length+1);this.eid=j.nextEid||(this.edges.length+1);this.sel=null;this.renderAll();this.toast('已加载保存的工作流');}catch(e){this.toast('加载失败: '+e.message,'err');}}
  exportJSON(){const data=JSON.stringify({nodes:this.nodes,edges:this.edges},{indent:2});const blob=new Blob([data],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='workflow_'+new Date().toISOString().slice(0,10)+'.json';a.click();this.toast('已导出JSON文件');}
  importJSON(){const input=document.createElement('input');input.type='file';input.accept='.json';input.onchange=e=>{const file=e.target.files[0];if(!file)return;const reader=new FileReader();reader.onload=ev=>{try{const j=JSON.parse(ev.target.result);this.nodes=j.nodes||[];this.edges=j.edges||[];this.nid=j.nextNid||(this.nodes.length+1);this.eid=j.nextEid||(this.edges.length+1);this.sel=null;this.renderAll();this.toast('已导入: '+file.name);}catch(er){this.toast('导入失败: '+er.message,'err');}};reader.readAsText(file);};input.click();}

  // ===== Toast =====
  toast(msg,isErr){const el=document.getElementById('toast');el.textContent=msg;el.className='toast '+(isErr?'err':'ok');el.style.display='block';setTimeout(()=>el.style.display='none',2500);}
}

// Init
const app=new WFEditor();
</script>
</body>
</html>"""

with open(r"D:\WB_Workflow\workflow_editor_v3.html", "w", encoding="utf-8") as f:
    f.write(html)

import os
size = os.path.getsize(r"D:\WB_Workflow\workflow_editor_v3.html")
print(f"Done! File size: {size} bytes")
