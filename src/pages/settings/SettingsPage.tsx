import type { FC } from "react";
import { Empty } from "antd";
import { SettingOutlined } from "@ant-design/icons";
import { useSettingsStore } from "@/store/settings-store";
import SettingsField from "@/components/settings-field/SettingsField";
import { useGroupLabelWidths } from "@/hooks/useRowLabelWidths";

const SettingsPage: FC = () => {
  const values = useSettingsStore((s) => s.values);
  const layout = useSettingsStore((s) => s.layout);
  const updateValue = useSettingsStore((s) => s.updateValue);
  const labelWidths = useGroupLabelWidths(layout);

  return (
    <div className="flex flex-col h-full bg-white rounded-lg mx-4 mb-4 p-4 shadow-sm">
      <div className="flex items-center gap-2 h-40px shrink-0">
        <SettingOutlined className="text-lg" />
        <span className="text-lg font-bold text-[#1a1a2e]">全局设置</span>
      </div>

      <div className="flex-1 overflow-y-auto">
        {layout.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <Empty description="暂无设置" />
          </div>
        ) : (
          <div
            className="grid gap-x-4 gap-y-3"
            style={{ gridTemplateColumns: `repeat(24, 1fr)` }}
          >
            {layout.map((row, rowIndex) => {
              const isHeader = row.length === 1 && !row[0].store;

              let col = 1;
              return row.map((cell, ci) => {
                const start = col;
                col += isHeader ? 24 : (cell.span ?? 1);

                return (
                  <div
                    key={cell.store ?? cell.text ?? rowIndex}
                    className={`flex items-center min-h-0 ${isHeader ? "border-b border-[#e5e7eb] pb-1 mt-2" : ""}`}
                    style={{
                      gridRow: rowIndex + 1,
                      gridColumn: `${start} / span ${isHeader ? 24 : (cell.span ?? 1)}`,
                    }}
                  >
                    {isHeader ? (
                      <span className="text-sm font-bold text-[#1a1a2e]">{cell.text}</span>
                    ) : (
                      <SettingsField
                        cell={cell}
                        value={cell.store ? values[cell.store] : undefined}
                        onChange={cell.store
                          ? (v) => updateValue(cell.store as string, v)
                          : () => {}
                        }
                        labelWidth={labelWidths[rowIndex]?.[ci]}
                      />
                    )}
                  </div>
                );
              });
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default SettingsPage;
