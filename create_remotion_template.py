"""Remotion 项目模板 - WorkBuddy 短视频智能中台 v4.0
引擎 B：代码化视频——利用 React 技术栈实现高度定制化的动态图文排版与批量导出

启动方式：
  cd remotion_template
  npm install
  npm start            # Remotion Studio 预览
  npm run build        # 渲染导出 MP4

在 multi_engine_scheduler.py 中的集成方式：
  engine_type="remotion" → RemotionRenderer → 调用本模板的 render.ts
"""

# Remotion 项目结构模板
import os
import json
import shutil

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "remotion_template")

# ==================== 项目文件内容 ====================

PACKAGE_JSON = json.dumps({
    "name": "workbuddy-remotion",
    "version": "1.0.0",
    "description": "WorkBuddy Remotion 代码化视频模板",
    "scripts": {
        "start": "remotion studio",
        "build": "remotion render src/index.tsx out/video.mp4",
        "build:batch": "tsx src/batch_render.ts"
    },
    "dependencies": {
        "react": "^18.2.0",
        "react-dom": "^18.2.0",
        "remotion": "^4.0.0",
        "@remotion/cli": "^4.0.0"
    },
    "devDependencies": {
        "tsx": "^4.0.0",
        "typescript": "^5.0.0",
        "@types/react": "^18.2.0",
        "@react-types/react": "17.0.0"
    }
}, indent=2)

TS_CONFIG = json.dumps({
    "compilerOptions": {
        "target": "ES2020",
        "module": "commonjs",
        "jsx": "react-jsx",
        "strict": True,
        "esModuleInterop": True,
        "skipLibCheck": True,
        "forceConsistentCasingInFileNames": True,
        "outDir": "./dist",
        "rootDir": "./src"
    },
    "include": ["src"]
}, indent=2)


def create_template(base_dir: str = None):
    """创建 Remotion 项目模板文件结构"""
    if base_dir is None:
        base_dir = TEMPLATE_DIR

    src_dir = os.path.join(base_dir, "src")
    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(os.path.join(base_dir, "out"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "public"), exist_ok=True)

    # ---- package.json ----
    with open(os.path.join(base_dir, "package.json"), "w", encoding="utf-8") as f:
        f.write(PACKAGE_JSON)

    # ---- tsconfig.json ----
    with open(os.path.join(base_dir, "tsconfig.json"), "w", encoding="utf-8") as f:
        f.write(TS_CONFIG)

    # ---- src/index.tsx (Remotion 入口) ----
    with open(os.path.join(src_dir, "index.tsx"), "w", encoding="utf-8") as f:
        f.write('''import { registerRoot } from "remotion";
import { RemotionRoot } from "./Root";

registerRoot(RemotionRoot);
''')

    # ---- src/Root.tsx (组合根) ----
    with open(os.path.join(src_dir, "Root.tsx"), "w", encoding="utf-8") as f:
        f.write('''import { Composition } from "remotion";
import { ProductCard } from "./ProductCard";
import { ScriptReader } from "./ScriptReader";

export const RemotionRoot = () => {
  return (
    <>
      <Composition
        id="ProductCard"
        component={ProductCard}
        durationInFrames={300}  // 10s @30fps
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          productName: "智能手表",
          price: "¥299",
          features: ["心率监测", "睡眠分析", "7天续航"],
          bgColor: "#667eea",
        }}
      />
      <Composition
        id="ScriptReader"
        component={ScriptReader}
        durationInFrames={450}  // 15s
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          scriptText: "这是由 WorkBuddy AI 自动生成的视频文案...",
          voiceUrl: "",
        }}
      />
    </>
  );
};
''')

    # ---- src/ProductCard.tsx (商品卡片模板) ----
    with open(os.path.join(src_dir, "ProductCard.tsx"), "w", encoding="utf-8") as f:
        f.write('''import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring, Sequence } from "remotion";

interface ProductCardProps {
  productName: string;
  price: string;
  features: string[];
  bgColor: string;
}

export const ProductCard: React.FC<ProductCardProps> = ({ productName, price, features, bgColor }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 入场动画
  const scale = spring({ frame, fps, config: { damping: 12 } });
  const opacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: "clamp" });

  return (
    <div style={{
      flex: 1,
      background: `linear-gradient(135deg, ${bgColor}, ${bgColor}dd)`,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      color: "white",
      fontFamily: "-apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif",
      textAlign: "center",
    }}>
      {/* 标题 */}
      <Sequence from={0} durationInFrames={90}>
        <div style={{ transform: `scale(${scale})`, opacity }}>
          <h1 style={{ fontSize: 72, fontWeight: 700, marginBottom: 8 }}>{productName}</h1>
          <div style={{ fontSize: 48, fontWeight: 300 }}>{price}</div>
        </div>
      </Sequence>

      {/* 卖点列表 */}
      <Sequence from={60} durationInFrames={180}>
        <div style={{ display: "flex", flexDirection: "column", gap: 24, marginTop: 40 }}>
          {features.map((f, i) => {
            const delay = (i * 30 + 60);
            const itemOpacity = interpolate(frame, [delay, delay + 20], [0, 1], { extrapolateRight: "clamp" });
            const itemX = interpolate(frame, [delay, delay + 20], [60, 0], { extrapolateRight: "clamp" });
            return (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 16, opacity: itemOpacity, transform: `translateX(${itemX}px)` }}>
                <div style={{ width: 12, height: 12, borderRadius: "50%", background: "white" }} />
                <span style={{ fontSize: 36 }}>{f}</span>
              </div>
            );
          })}
        </div>
      </Sequence>

      {/* CTA */}
      <Sequence from={240}>
        <div style={{
          opacity: interpolate(frame, [240, 260], [0, 1], { extrapolateRight: "clamp" }),
          transform: `scale(${spring({ frame: frame - 240, fps, config: { damping: 10 } })})`,
          marginTop: 60,
        }}>
          <div style={{
            background: "white",
            color: bgColor,
            padding: "20px 60px",
            borderRadius: 48,
            fontSize: 40,
            fontWeight: 700,
          }}>
            立即购买 →
          </div>
        </div>
      </Sequence>
    </div>
  );
};
''')

    # ---- src/ScriptReader.tsx (文案阅读模板) ----
    with open(os.path.join(src_dir, "ScriptReader.tsx"), "w", encoding="utf-8") as f:
        f.write('''import React from "react";
import { useCurrentFrame, interpolate, Sequence } from "remotion";

interface ScriptReaderProps {
  scriptText: string;
  voiceUrl: string;
}

export const ScriptReader: React.FC<ScriptReaderProps> = ({ scriptText, voiceUrl }) => {
  const frame = useCurrentFrame();

  // 文字逐行显示（每行 20 字，每2秒一行）
  const words = scriptText.split("");
  const charsPerLine = 18;
  const lines: string[] = [];
  for (let i = 0; i < words.length; i += charsPerLine) {
    lines.push(words.slice(i, i + charsPerLine).join(""));
  }

  return (
    <div style={{
      flex: 1,
      background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      color: "white",
      fontFamily: "-apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif",
      padding: 60,
    }}>
      <div style={{ fontSize: 20, opacity: 0.6, marginBottom: 40, letterSpacing: 4 }}>
        🤖 AI 自动生成文案
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 12, maxWidth: 800 }}>
        {lines.map((line, i) => {
          const lineStart = i * 60; // 每2秒
          const opacity = interpolate(frame, [lineStart, lineStart + 15], [0, 1], { extrapolateRight: "clamp" });
          return (
            <div key={i} style={{ opacity, fontSize: 32, lineHeight: 1.6, textAlign: "center" }}>
              {line}
            </div>
          );
        })}
      </div>

      {/* 底部水印 */}
      <Sequence from={100}>
        <div style={{
          position: "absolute",
          bottom: 40,
          fontSize: 16,
          opacity: 0.3,
        }}>
          Powered by WorkBuddy v4.0 · Remotion Engine
        </div>
      </Sequence>
    </div>
  );
};
''')

    # ---- src/batch_render.ts (批量渲染) ----
    with open(os.path.join(src_dir, "batch_render.ts"), "w", encoding="utf-8") as f:
        f.write('''import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import path from "path";
import fs from "fs";

interface BatchConfig {
  compositionId: string;
  outputName: string;
  props: Record<string, any>;
  durationInFrames?: number;
}

// 读取 WorkBuddy 传入的批量配置
const configPath = process.argv[2] || path.join(__dirname, "../batch_config.json");
const configs: BatchConfig[] = JSON.parse(fs.readFileSync(configPath, "utf-8"));

async function renderBatch() {
  const bundleLocation = await bundle({ entryPoint: path.join(__dirname, "./index.tsx") });

  for (const cfg of configs) {
    console.log(`🎬 Rendering: ${cfg.outputName}...`);
    const composition = await selectComposition({
      serveUrl: bundleLocation,
      id: cfg.compositionId,
      inputProps: cfg.props,
    });

    await renderMedia({
      composition,
      serveUrl: bundleLocation,
      codec: "h264",
      outputLocation: path.join(__dirname, "../out", cfg.outputName),
      inputProps: cfg.props,
      durationInFrames: cfg.durationInFrames || composition.durationInFrames,
    });
    console.log(`✅ Done: ${cfg.outputName}`);
  }
}

renderBatch().catch(console.error);
''')

    # ---- README.md ----
    with open(os.path.join(base_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write('''# WorkBuddy Remotion 模板 v1.0

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
''')

    print(f"[OK] Remotion project template created: {os.path.abspath(base_dir)}")
    print(f"     Next: cd {base_dir} && npm install && npm start")


if __name__ == "__main__":
    create_template()
