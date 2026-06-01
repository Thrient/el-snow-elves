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
              className="window-card win-card-enter relative"
              onClick={() => characterStore.setSelectedHwnd(c.hwnd)}
              title={`HWND: ${c.hwnd}`}
              style={{
                animationDelay: `${i * 50}ms`,
                borderTop: `2px solid ${accent}`,
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
              <span className="absolute top-2 right-2 w-2 h-2 rounded-full" style={{
                background: c.running ? "#52c41a" : "#d1d5db",
                boxShadow: c.running ? "0 0 6px rgba(82,196,26,.4)" : undefined,
              }} />
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
            display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
          }}
        >
          <div style={{
            width: 28, height: 28, borderRadius: 8,
            background: "#eef2ff", border: "1px dashed #b0c8f0",
            display: "flex", alignItems: "center", justifyContent: "center",
            flexShrink: 0,
          }}>
            <PlusOutlined style={{ fontSize: 14, color: "#1677ff" }} />
          </div>
          <span className="text-[11px] font-medium text-[#1677ff]">绑定窗口</span>
        </div>
      </div>
    </div>
  );
};

export default WindowSelector;
