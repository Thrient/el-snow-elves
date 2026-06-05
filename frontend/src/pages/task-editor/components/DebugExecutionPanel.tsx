import type { FC } from "react";
import { Button, message } from "antd";
import { BugOutlined } from "@ant-design/icons";
import { useEditorStore } from "@/store/editor-store";
import { useCharacterStore } from "@/store/character-store";

interface DebugExecutionPanelProps {
  hwnd: string;
  stepName: string;
}

const DebugExecutionPanel: FC<DebugExecutionPanelProps> = ({ hwnd, stepName }) => (
  <div className="rounded-xl border border-dashed border-[#ffa940] bg-[#fffbe6] p-3.5 space-y-2">
    <div className="flex items-center gap-2">
      <BugOutlined className="text-[#fa8c16] text-sm" />
      <span className="text-[11px] font-semibold text-[#1a1a2e]">调试运行</span>
      <span className="text-[10px] text-[#8b8fa3]">窗口 {hwnd}</span>
    </div>
    <div className="flex gap-2">
      <Button size="small" type="primary"
        className="border-[#fa8c16] bg-[#fa8c16]"
        onClick={() => {
          const task = useEditorStore.getState().currentTask;
          if (!task) return;
          const charStore = useCharacterStore.getState();
          if (!charStore.selectedHwnd) { message.warning("请先在窗口管理中选择一个窗口"); return; }
          charStore.pushExecute(charStore.selectedHwnd, {
            id: task.id, name: task.name, version: task.version,
            values: task.values, debugStart: stepName,
          });
          message.success(`已添加到窗口 ${charStore.selectedHwnd}：从「${stepName}」开始`);
        }}>
        从此步骤开始
      </Button>
      <Button size="small"
        className="border-[#fa8c16] c-[#fa8c16]"
        onClick={() => {
          const task = useEditorStore.getState().currentTask;
          if (!task) return;
          const charStore = useCharacterStore.getState();
          if (!charStore.selectedHwnd) { message.warning("请先在窗口管理中选择一个窗口"); return; }
          charStore.pushExecute(charStore.selectedHwnd, {
            id: task.id, name: task.name, version: task.version,
            values: task.values, debugStart: stepName, debugSingle: true,
          });
          message.success(`已添加到窗口 ${charStore.selectedHwnd}：单步执行「${stepName}」`);
        }}>
        单步执行
      </Button>
    </div>
    <div className="text-[10px] text-[#8b8fa3] leading-relaxed">
      从此步骤开始：覆盖任务入口，后续正常流转。<br />
      单步执行：仅执行此步骤，完成后立即结束（忽略跳转）。
    </div>
  </div>
);

export default DebugExecutionPanel;
