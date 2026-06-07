import { bundle } from "@remotion/bundler";
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
