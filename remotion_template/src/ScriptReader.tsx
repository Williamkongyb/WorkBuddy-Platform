import React from "react";
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
