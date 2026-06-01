import { type FC } from "react";
import { Button, Slider } from "antd";
import {
  ClearOutlined, LockOutlined, UnlockOutlined,
  PauseCircleOutlined, PlayCircleOutlined, StopOutlined,
} from "@ant-design/icons";
import { useCharacterStore } from "@/store/character";

const ControlPanel: FC = () => {
  const characterStore = useCharacterStore();
  const selected = characterStore.characters.find((c) => c.hwnd === characterStore.selectedHwnd);
  if (!selected) return null;

  const taskCount = selected.executeList.length;
  const isLocked = selected.locked !== false;

  const handleToggleLock = () => {
    const hwnd = characterStore.selectedHwnd!;
    const action = isLocked ? "API:SCRIPT:UNLOCK" : "API:SCRIPT:LOCK";
    window.pywebview?.api.emit(action, hwnd).then(() => { characterStore.update({ hwnd, locked: !isLocked }); });
  };

  return (
    <div className="shrink-0 mb-4 bg-white rounded-xl border border-solid border-[#eef0f2] overflow-hidden">
      {/* Status bar */}
      <div className="flex items-center gap-3 px-4 py-3" style={{ boxShadow: "inset 0 -1px 0 #f3f4f6" }}>
        <div className="flex items-center gap-2">
          <div style={{
            width: 7, height: 7, borderRadius: "50%",
            background: selected.currentTask ? "#52c41a" : "#d1d5db",
            boxShadow: selected.currentTask ? "0 0 6px rgba(82,196,26,.4)" : undefined,
          }} />
          <span className="text-[11px] text-[#8b8fa3] uppercase tracking-wider">当前任务</span>
        </div>
        <span className="text-[13px] font-medium text-[#1a1a2e] truncate">
          {selected.currentTask ?? "—"}
        </span>
        <div className="flex-1" />
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full"
          style={{
            background: isLocked ? "#fff7ed" : "#f0fdf4",
            border: `1px solid ${isLocked ? "#fed7aa" : "#bbf7d0"}`,
          }}>
          {isLocked ? <LockOutlined style={{ fontSize: 10, color: "#c2410c" }} /> : <UnlockOutlined style={{ fontSize: 10, color: "#15803d" }} />}
          <span className="text-[11px] font-medium" style={{ color: isLocked ? "#c2410c" : "#15803d" }}>
            {isLocked ? "已锁定" : "已解锁"}
          </span>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-3 px-5 py-4">
        <Button
          type={selected.running ? "default" : "primary"}
          icon={selected.running ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
          style={{ borderRadius: 8, fontWeight: 500, ...(selected.running ? {} : { boxShadow: "0 2px 8px rgba(22,119,255,.2)" }) }}
          onClick={() => {
            const hwnd = characterStore.selectedHwnd!;
            const wasRunning = selected.running;
            window.pywebview?.api.emit(wasRunning ? "API:SCRIPT:PAUSE" : "API:SCRIPT:RESUME", hwnd).then(() => {
              const ch = useCharacterStore.getState().characters.find((c) => c.hwnd === hwnd);
              if (ch) characterStore.update({ hwnd, running: !ch.running });
            });
          }}
        >
          {selected.running ? "暂停" : "开始执行"}
        </Button>

        <Button
          icon={<StopOutlined />}
          disabled={!selected.currentTask && taskCount === 0}
          onClick={async () => {
            const hwnd = characterStore.selectedHwnd!;
            await window.pywebview?.api.emit("API:SCRIPT:STOP", hwnd);
            characterStore.update({ hwnd, currentTask: null });
          }}
          style={{ borderRadius: 8, fontWeight: 500, borderColor: "#fecaca", color: "#dc2626" }}
        >
          结束任务
        </Button>

        <Button
          icon={isLocked ? <LockOutlined /> : <UnlockOutlined />}
          onClick={handleToggleLock}
          style={{
            borderRadius: 8, fontWeight: 500,
            borderColor: isLocked ? "#fed7aa" : "#bbf7d0",
            color: isLocked ? "#c2410c" : "#15803d",
            background: isLocked ? "#fff7ed" : "#f0fdf4",
          }}
        >
          {isLocked ? "解锁" : "锁定"}
        </Button>

        <Button icon={<ClearOutlined />} disabled={taskCount === 0}
          onClick={() => characterStore.clearExecute(selected.hwnd)}
          style={{ borderRadius: 8, fontWeight: 500 }}>
          {taskCount > 0 ? `清空队列 (${taskCount})` : "清空队列"}
        </Button>

        <div className="flex-1" />

        {/* Opacity slider */}
        <div className="flex items-center gap-3">
          <span className="text-[10px] text-[#9ca3af] font-medium uppercase tracking-wider">透明度</span>
          <Slider style={{ width: 96, margin: 0 }} min={0} max={255}
            value={selected.opacity ?? 255}
            onChange={(v) => { characterStore.update({ hwnd: selected.hwnd, opacity: v }); window.pywebview?.api.emit("API:SCRIPT:SET_OPACITY", selected.hwnd, v); }}
            styles={{ track: { background: "#1677ff" }, rail: { background: "#e5e7eb" } }} />
          <span className="text-[12px] font-semibold text-[#374151] font-mono w-7 text-right">
            {selected.opacity ?? 255}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ControlPanel;
