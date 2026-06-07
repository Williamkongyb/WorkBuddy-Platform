# WorkBuddy Remotion 模板 v1.0

## 使用方式

### 1. 安装依赖
```bash
cd remotion_template
npm install
```

### 2. 预览（Remotion Studio）
```bash
npm start
```

### 3. 单个视频渲染
```bash
npm run build
```

### 4. 批量渲染（从 WorkBuddy 流水线调用）
```bash
tsx src/batch_render.ts ../batch_config.json
```

## 与 multi_engine_scheduler.py 集成

```python
# 在 :8300 API 中调用
scheduler.dispatch("remotion", RenderRequest(
    product="智能手表",
    script_text="这是由 WorkBuddy AI 自动生成的视频文案...",
    extra_params={
        "template": "ProductCard",
        "batch_config": "remotion_template/batch_config.json"
    }
))
```

## 模板

- **ProductCard** — 商品卡片展示模板（1080x1920 竖版）
- **ScriptReader** — 文案逐行阅读模板
