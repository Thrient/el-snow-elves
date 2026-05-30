import { type FC } from "react";
import { Switch, Tag } from "antd";
import { ClockCircleOutlined, DeleteOutlined } from "@ant-design/icons";
import { Cron } from "croner";
import cronstrue from "cronstrue";
import "cronstrue/locales/zh_CN";
import type { PlanEntry } from "@/store/user-store";
import { useUserStore } from "@/store/user-store";
import { useCharacterStore } from "@/store/character";
import { PLAN_TEMPLATES } from "@/types/plan";

interface Props {
  plan: PlanEntry;
  idx: number;
  accent: string;
  now: number;
  onEdit: (plan: PlanEntry) => void;
}

const PlanCard: FC<Props> = ({ plan, idx, accent, now, onEdit }) => {
  const userStore = useUserStore();
  const characterStore = useCharacterStore();
  const tmpl = PLAN_TEMPLATES.find((t) => t.id === plan.templateId);
  const cronHuman = (() => { try { return cronstrue.toString(plan.cron, { locale: "zh_CN" }); } catch { return plan.cron; } })();
  let nextRun: Date | null = null;
  let secondsLeft = -1;
  if (plan.enabled) { try { nextRun = new Cron(plan.cron).nextRun(); } catch { /* */ }
    if (nextRun) secondsLeft = Math.max(0, Math.floor((nextRun.getTime() - now) / 1000)); }

  const handleToggle = () => {
    userStore.togglePlan(plan._uid);
    characterStore.setPlans(characterStore.selectedHwnd!, useUserStore.getState().plans);
  };

  const handleDelete = () => {
    userStore.removePlan(plan._uid);
    characterStore.setPlans(characterStore.selectedHwnd!, useUserStore.getState().plans);
  };

  return (
    <div
      className="queue-item queue-item-enter group"
      onClick={() => onEdit(plan)}
      style={{
        animationDelay: `${idx * 50}ms`,
        borderLeft: `3px solid ${plan.enabled ? accent : "#e5e7eb"}`,
        boxShadow: plan.enabled ? "0 2px 8px rgba(0,0,0,.03)" : "0 1px 2px rgba(0,0,0,.01)",
        borderColor: plan.enabled ? "#d0d4dd" : "#eef0f2",
      }}
    >
      <div className="flex items-center gap-2.5 px-3.5 py-2.5">
        <span onClick={(e) => e.stopPropagation()}>
          <Switch size="small" checked={plan.enabled} onChange={handleToggle} />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5 mb-0.5">
            <span className="text-[12px] font-semibold text-[#1a1a2e] truncate">{plan.name}</span>
            {tmpl && (
              <Tag style={{ fontSize: 8, lineHeight: 1, border: "none", borderRadius: 4, padding: "1px 6px", margin: 0, color: "#6366f1", background: "#eef2ff" }}>
                {tmpl.name}
              </Tag>
            )}
          </div>
          <div className="flex items-center gap-1 text-[10px] text-[#9ca3af]">
            <ClockCircleOutlined className="text-[9px]" />
            <span className="font-mono">{plan.cron}</span>
            <span className="text-[#d1d5db]">·</span>
            <span className="truncate">{cronHuman}</span>
          </div>
        </div>
        <span onClick={(e) => { e.stopPropagation(); handleDelete(); }}
          className="flex items-center justify-center w-6 h-6 cursor-pointer opacity-0 group-hover:opacity-100 transition-all shrink-0 select-none rounded-md c-[#d1d5db]"
          onMouseEnter={(e) => { e.currentTarget.style.color = "#ef4444"; e.currentTarget.style.background = "#fef2f2"; }}
          onMouseLeave={(e) => { e.currentTarget.style.color = "#d1d5db"; e.currentTarget.style.background = "transparent"; }}>
          <DeleteOutlined className="text-xs" />
        </span>
      </div>
      {plan.enabled && nextRun && (
        <div className="px-3.5 pb-2.5">
          {secondsLeft <= 60 ? (
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-solid border-[#fde68a]"
              style={{ background: "linear-gradient(135deg, #fffbeb, #fef3c7)" }}>
              <div className="w-[18px] h-[18px] rounded-full bg-[#f59e0b] flex items-center justify-center text-[9px] font-bold c-white animate-[win-pulse_1s_infinite]">!</div>
              <span className="text-[10px] font-semibold text-[#92400e]">即将执行</span>
              <span className="text-xs font-bold text-[#d97706] ml-auto font-mono">{secondsLeft}s</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 px-3 py-1.5 text-[10px] text-[#9ca3af] bg-[#f9fafb] rounded-lg">
              <span>下次</span>
              <span className="font-semibold text-[#374151] ml-auto">
                {nextRun.toLocaleDateString("zh-CN", { month: "short", day: "numeric" })} {nextRun.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PlanCard;
