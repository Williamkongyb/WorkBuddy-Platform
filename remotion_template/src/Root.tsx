import { Composition } from "remotion";
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
