import { type FC } from "react";
import { DesktopOutlined, PlusOutlined } from "@ant-design/icons";
import { useCharacterStore } from "@/store/character";

const DOT_COLORS = ["#1677ff", "#52c41a", "#fa8c16", "#722ed1", "#13c2c2"];

interface Props {
  onBind: () => void;
}

const WindowSelector: FC<Props> = ({ onBind }) => {
  const characterStore = useCharacterStore();

  return (
    <div className="shrink-0 mb-4">
      <div
        className="window-row flex items-center gap-2.5 overflow-x-auto pb-1.5"
        style={{ marginRight: -20, paddingRight: 20, scrollSnapType: "x mandatory" }}
        onWheel={(e) => {
          if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
            e.currentTarget.scrollLeft += e.deltaY;
            e.preventDefault();
          }
        }}
      >
        {characterStore.characters.map((c, i) => {
          const selected = c.hwnd === characterStore.selectedHwnd;
          const accent = DOT_COLORS[i % DOT_COLORS.length];
          return (
            <div
              key={c.hwnd}
              className="window-card win-card-enter"
              onClick={() => characterStore.setSelectedHwnd(c.hwnd)}
              title={`HWND: ${c.hwnd}`}
              style={{
                animationDelay: `${i * 50}ms`,
                borderTop: `3px solid ${accent}`,
                padding: "10px 14px 12px",
                minWidth: 130,
                display: "flex", flexDirection: "column", alignItems: "center", gap: 8,
                ...(selected ? {
                  borderColor: accent,
                  boxShadow: `0 0 0 1px ${accent}40, 0 4px 16px ${accent}18`,
                  backgroundColor: `${accent}06`,
                } : {}),
              }}
            >
              {c.character ? (
                <img src={c.character} alt=""
                  style={{
                    width: 120, height: 34, objectFit: "contain",
                    borderRadius: 6, background: "#f5f6f8",
                    border: "1px solid #e8eaed",
                  }} />
              ) : (
                <div style={{
                  width: 48, height: 34, borderRadius: 8,
                  background: `linear-gradient(135deg, ${accent}18, ${accent}0d)`,
                  border: `1px dashed ${accent}40`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                }}>
                  <DesktopOutlined style={{ fontSize: 18, color: accent }} />
                </div>
              )}
              <div className="flex items-center gap-1.5">
                <span style={{
                  width: 6, height: 6, borderRadius: "50%",
                  background: c.running ? "#52c41a" : "#d1d5db",
                  boxShadow: c.running ? "0 0 6px rgba(82,196,26,.4)" : undefined,
                  flexShrink: 0,
                }} />
                <span className="text-[11px] font-medium" style={{ color: c.running ? "#374151" : "#8b8fa3" }}>
                  {c.running ? "运行中" : "已停止"}
                </span>
              </div>
            </div>
          );
        })}
        {/* Add window card */}
        <div
          className="window-card"
          onClick={onBind}
          style={{
            borderStyle: "dashed",
            borderColor: "#d0d4dd",
            background: "#fafbfc",
            padding: "10px 20px 12px",
            minWidth: 100,
            display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 6,
          }}
        >
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: "#eef2ff", border: "1px dashed #b0c8f0",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <PlusOutlined style={{ fontSize: 16, color: "#1677ff" }} />
          </div>
          <span className="text-[11px] font-medium text-[#1677ff]">绑定窗口</span>
        </div>
      </div>
    </div>
  );
};

export default WindowSelector;
