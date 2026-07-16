import { useState, useCallback, type FC } from "react";
import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  horizontalListSortingStrategy,
  arrayMove,
} from "@dnd-kit/sortable";
import { useSettingsStore } from "@/store/settings-store";
import ComboCard from "./ComboCard";
import type { ComboStep } from "./ComboCard";
import ComboConnector from "./ComboConnector";

// ── helpers ──

type ComboMode = "click" | "down" | "up";

function isSkillKey(key: string): boolean {
  if (key.startsWith("cfg_") || key.startsWith("连招_")) return false;
  return true;
}

const CONFIG_PREFIX = "{CONFIG.";

function configRef(name: string): string {
  return `${CONFIG_PREFIX}${name}}`;
}

type RawStep = { s?: string; m?: string; p?: unknown; d?: unknown };

function toSteps(raw: unknown): ComboStep[] {
  const arr: RawStep[] = Array.isArray(raw)
    ? raw
    : typeof raw === "string"
      ? (() => {
          try { const p = JSON.parse(raw); return Array.isArray(p) ? p : []; }
          catch { return []; }
        })()
      : [];
  return arr.map((item: RawStep) => ({
    id: crypto.randomUUID(),
    s: String(item.s ?? ""),
    m: (item.m as ComboMode) || "click",
    p: Number(item.p ?? 100),
    d: Number(item.d ?? 800),
  }));
}

function serializeSteps(steps: ComboStep[]): { s: string; m: string; p: number; d: number }[] {
  return steps.map(({ s, m, p, d }) => ({ s, m, p, d }));
}

// ── Component ──

interface Props {
  value?: ComboStep[] | string;
  onChange: (value: unknown) => void;
}

const ComboEditor: FC<Props> = ({ value, onChange }) => {
  const settingsValues = useSettingsStore((s) => s.values);
  const skills = Object.keys(settingsValues).filter(isSkillKey).sort();
  const defaultRef = skills[0] ? configRef(skills[0]) : "";

  const [steps, setSteps] = useState<ComboStep[]>(() => toSteps(value));
  const skillOptions = skills.map((n) => ({ label: n, value: configRef(n) }));

  const emit = useCallback(
    (s: ComboStep[]) => { setSteps(s); onChange(serializeSteps(s)); },
    [onChange],
  );

  const addStep = useCallback(() => {
    emit([...steps, { id: crypto.randomUUID(), s: defaultRef, m: "click", p: 100, d: 800 }]);
  }, [defaultRef, steps, emit]);

  const deleteStep = useCallback(
    (id: string) => emit(steps.filter((s) => s.id !== id)),
    [steps, emit],
  );

  const updateStep = useCallback(
    (id: string, patch: Partial<ComboStep>) =>
      emit(steps.map((s) => (s.id === id ? { ...s, ...patch } : s))),
    [steps, emit],
  );

  const cycleMode = useCallback(
    (id: string) => {
      const step = steps.find((s) => s.id === id);
      if (!step) return;
      const CYCLE: ComboMode[] = ["click", "down", "up"];
      updateStep(id, { m: CYCLE[(CYCLE.indexOf(step.m) + 1) % CYCLE.length] });
    },
    [steps, updateStep],
  );

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
  );

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event;
      if (!over || active.id === over.id) return;
      const oldIdx = steps.findIndex((s) => s.id === active.id);
      const newIdx = steps.findIndex((s) => s.id === over.id);
      if (oldIdx === -1 || newIdx === -1) return;
      emit(arrayMove(steps, oldIdx, newIdx));
    },
    [steps, emit],
  );

  return (
    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <SortableContext items={steps.map((s) => s.id)} strategy={horizontalListSortingStrategy}>
        <div className="flex items-center flex-wrap w-full">
          {steps.flatMap((step, i) => [
            <ComboCard
              key={step.id}
              step={step}
              skillOptions={skillOptions}
              onDelete={deleteStep}
              onModeCycle={cycleMode}
              onChangeSkill={(id, s) => updateStep(id, { s })}
              onChangePress={(id, p) => updateStep(id, { p })}
            />,
            <ComboConnector
              key={`conn-${step.id}`}
              delay={step.d}
              onChange={(d) => updateStep(step.id, { d })}
              isLast={i === steps.length - 1}
            />,
          ])}
          <button
            key="add-btn"
            className="
              flex items-center justify-center
              w-104px h-72px shrink-0
              border-2 border-dashed border-[#e0e0e0] rounded-[var(--radius-md)]
              cursor-pointer text-24px color-[#bbb] bg-transparent
              hover:border-[var(--color-primary-border)] hover:text-[var(--color-primary)]
              transition-colors duration-150
            "
            onClick={addStep}
            title="添加步骤"
          >
            +
          </button>
        </div>
      </SortableContext>
    </DndContext>
  );
};

export default ComboEditor;
