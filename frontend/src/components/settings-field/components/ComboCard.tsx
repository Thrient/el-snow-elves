import { useState, useRef, useEffect, type FC, type CSSProperties } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Select } from "antd";

export interface ComboStep {
  id: string;
  s: string;
  m: "click" | "down" | "up";
  p: number;
  d: number;
}

interface Props {
  step: ComboStep;
  skillOptions: { label: string; value: string }[];
  onDelete: (id: string) => void;
  onModeCycle: (id: string) => void;
  onChangeSkill: (id: string, s: string) => void;
  onChangePress: (id: string, p: number) => void;
}

const ComboCard: FC<Props> = ({
  step, skillOptions,
  onDelete, onModeCycle, onChangeSkill, onChangePress,
}) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: step.id });

  const style: CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const [editingPress, setEditingPress] = useState(false);
  const [pressTemp, setPressTemp] = useState(String(step.p));
  const pressRef = useRef<HTMLInputElement>(null);
  useEffect(() => { setPressTemp(String(step.p)); }, [step.p]);
  useEffect(() => { if (editingPress) pressRef.current?.select(); }, [editingPress]);

  const commitPress = () => {
    const v = parseInt(pressTemp, 10);
    if (!isNaN(v) && v >= 0) onChangePress(step.id, v);
    else setPressTemp(String(step.p));
    setEditingPress(false);
  };

  return (
    <div
      ref={setNodeRef} style={style} {...attributes} {...listeners}
      className="
        group relative flex flex-col items-center justify-center gap-4px
        w-104px h-72px shrink-0
        bg-[var(--color-bg-container)] border-1 border-[var(--color-border)]
        rounded-[var(--radius-md)]
        cursor-grab select-none
        hover:border-[var(--color-primary-border)] hover:shadow-[var(--shadow-md)]
        transition-all duration-150
      "
    >
      <button
        className="
          absolute top-2px right-2px z-10
          w-20px h-20px flex items-center justify-center
          text-12px leading-none p-0 rounded-full
          color-[var(--color-text-muted)] bg-transparent border-none cursor-pointer
          opacity-0 group-hover:opacity-70
          hover:opacity-100 hover:color-[var(--color-text-secondary)] hover:bg-[var(--color-bg-hover)]
          transition-all duration-150
        "
        onClick={(e) => { e.stopPropagation(); onDelete(step.id); }}
      >×</button>

      {/* Row 1: skill name */}
      <Select
        className="!w-full max-w-88px
          [&_.ant-select-selector]:!text-center [&_.ant-select-selector]:!px-0
          [&_.ant-select-selection-item]:!text-15px [&_.ant-select-selection-item]:!font-600"
        size="small" variant="borderless"
        value={step.s} options={skillOptions} showSearch
        popupMatchSelectWidth={false}
        onClick={(e) => e.stopPropagation()}
        onChange={(v) => onChangeSkill(step.id, v)}
        filterOption={(input, option) => (option?.label ?? "").toLowerCase().includes(input.toLowerCase())}
      />

      {/* Row 2: mode tag + press duration side by side */}
      <div className="flex items-center gap-4px">
        <span
          className="text-12px px-6px py-2px rounded-4px leading-normal
            color-[var(--color-primary)] bg-[var(--color-primary-bg)]
            cursor-pointer hover:bg-[rgba(22,119,255,0.18)]"
          onClick={(e) => { e.stopPropagation(); onModeCycle(step.id); }}
        >
          {step.m === "click" ? "点击" : step.m === "down" ? "按下" : "抬起"}
        </span>
        {step.m === "click" && (
          editingPress ? (
            <input
              ref={pressRef}
              className="w-40px text-center text-11px color-[var(--color-primary)]
                bg-[var(--color-primary-bg)] border-none rounded-2px outline-none p-0"
              value={pressTemp}
              onChange={(e) => setPressTemp(e.target.value)}
              onBlur={commitPress}
              onKeyDown={(e) => {
                if (e.key === "Enter") commitPress();
                if (e.key === "Escape") { setPressTemp(String(step.p)); setEditingPress(false); }
              }}
              onClick={(e) => e.stopPropagation()}
            />
          ) : (
            <span
              className="text-11px color-[var(--color-text-muted)] cursor-text
                hover:color-[var(--color-primary)]"
              onClick={(e) => { e.stopPropagation(); setEditingPress(true); }}
            >{step.p}ms</span>
          )
        )}
      </div>
    </div>
  );
};

export default ComboCard;
