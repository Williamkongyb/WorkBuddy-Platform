import React from "react";
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
