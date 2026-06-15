import type { FC } from "react";
import { Button, InputNumber, Select } from "antd";
import { PlusOutlined, DeleteOutlined } from "@ant-design/icons";
import { useSettingsStore } from "@/store/settings-store";

type ComboMode = "click" | "down" | "up";

interface ComboStep {
  s: string;
  m: ComboMode;
  p: number;
  d: number;
}

const MODE_OPTS: { label: string; value: ComboMode }[] = [
  { label: "点击", value: "click" },
  { label: "按下", value: "down" },
  { label: "抬起", value: "up" },
];

function isSkillKey(key: string): boolean {
  // cfg: 前缀 = 全局配置，连招: 前缀 = 连招数据，都不是技能
  if (key.startsWith("cfg_") || key.startsWith("连招_")) return false;
  return true;
}

interface Props {
  value?: ComboStep[];
  onChange: (value: ComboStep[]) => void;
}

function toSteps(raw: unknown): ComboStep[] {
  if (Array.isArray(raw)) {
    return raw.map((item: Record<string, unknown>) => ({
      s: String(item.s ?? ""),
      m: (item.m as ComboMode) || "click",
      p: Number(item.p ?? 100),
      d: Number(item.d ?? 800),
    }));
  }
  if (typeof raw === "string") {
    try { const parsed = JSON.parse(raw); if (Array.isArray(parsed)) return toSteps(parsed); } catch { /* */ }
  }
  return [];
}

const CONFIG_PREFIX = "{CONFIG.";

function configRef(name: string): string {
  return `${CONFIG_PREFIX}${name}}`;
}

const ComboEditor: FC<Props> = ({ value, onChange }) => {
  const settingsValues = useSettingsStore((s) => s.values);
  const skills = Object.keys(settingsValues).filter(isSkillKey).sort();
  const defaultRef = skills[0] ? configRef(skills[0]) : "";

  const steps = toSteps(value);
  const emit = (s: ComboStep[]) => onChange(s);
  const updateStep = (idx: number, patch: Partial<ComboStep>) => {
    const next = steps.map((step, i) => (i === idx ? { ...step, ...patch } : step));
    emit(next);
  };
  const removeStep = (idx: number) => emit(steps.filter((_, i) => i !== idx));
  const addStep = () => emit([...steps, { s: defaultRef, m: "click", p: 100, d: 800 }]);

  return (
    <div className="flex flex-col gap-1 w-full">
      {steps.map((step, i) => {
        const isHoldMode = step.m === "down" || step.m === "up";
        return (
          <div
            key={i}
            className="
              group flex items-center gap-3 px-3 py-1
              rounded-[var(--radius-md)]
              border border-[var(--color-border)]
              bg-[var(--color-bg-container)]
              hover:border-[var(--color-primary-border)]
              hover:shadow-[var(--shadow-sm)]
              transition-all duration-200
            "
          >
            {/* 序号 */}
            <span className="
              w-5.5 h-5.5 flex items-center justify-center
              rounded-full text-2xs font-bold flex-shrink-0
              bg-[var(--color-primary-bg)] text-[var(--color-primary)]
            ">
              {i + 1}
            </span>

            {/* 技能 — 弹性占位 */}
            <Select
              className="flex-1 min-w-0"
              size="small"
              variant="borderless"
              value={step.s || undefined}
              options={skills.map((n) => ({ label: n, value: configRef(n) }))}
              showSearch
              onChange={(v) => updateStep(i, { s: v })}
            />

            {/* 模式 */}
            <Select
              className="!w-24 flex-shrink-0"
              size="small"
              variant="borderless"
              value={step.m}
              options={MODE_OPTS}
              onChange={(v) => updateStep(i, { m: v })}
              popupMatchSelectWidth={false}
            />

            {/* 按下时长 */}
            {isHoldMode ? (
              <span className="w-24 text-center text-xs text-[var(--color-text-muted)] flex-shrink-0">—</span>
            ) : (
              <InputNumber
                className="!w-24 flex-shrink-0"
                size="small"
                variant="borderless"
                min={0}
                max={10000}
                step={10}
                precision={0}
                value={step.p}
                onChange={(v) => updateStep(i, { p: v ?? 100 })}
                suffix={<span className="text-2xs text-[var(--color-text-muted)]">ms</span>}
              />
            )}

            {/* 间隔 */}
            <InputNumber
              className="!w-24 flex-shrink-0"
              size="small"
              variant="borderless"
              min={0}
              max={60000}
              step={10}
              precision={0}
              value={step.d}
              onChange={(v) => updateStep(i, { d: v ?? 800 })}
              suffix={<span className="text-2xs text-[var(--color-text-muted)]">ms</span>}
            />

            {/* 删除 */}
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
              className="!w-6 !h-6 !p-0 opacity-0 group-hover:opacity-100 transition-opacity duration-150 flex-shrink-0"
              onClick={() => removeStep(i)}
            />
          </div>
        );
      })}

      <div className="flex items-center justify-between mt-1 px-1">
        <Button
          type="dashed"
          size="small"
          icon={<PlusOutlined />}
          onClick={addStep}
          className="
            !border-dashed !border-[var(--color-border)]
            hover:!border-[var(--color-primary-border)] hover:!text-[var(--color-primary)]
            transition-colors duration-200
          "
        >
          添加
        </Button>
        <span className="text-2xs text-[var(--color-text-muted)]">
          共 {steps.length} 步
        </span>
      </div>
    </div>
  );
};

export default ComboEditor;
