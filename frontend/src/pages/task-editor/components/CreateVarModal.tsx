import { useState, useCallback, type FC } from "react";
import { Input, Modal, message } from "antd";
import type { VarType } from "@/types/task";
import { VAR_TYPE_OPTS } from "@/types/variable/system-vars";

export interface CreateVarModalProps {
  open: boolean;
  existingKeys: Set<string>;
  onOk: (name: string, value: string, type: VarType) => void;
  onCancel: () => void;
}

const CreateVarModal: FC<CreateVarModalProps> = ({ open, existingKeys, onOk, onCancel }) => {
  const [newVarName, setNewVarName] = useState("");
  const [newVarValue, setNewVarValue] = useState("");
  const [newVarType, setNewVarType] = useState<VarType>("text");

  const handleCreateVar = useCallback(() => {
    if (!newVarName.trim()) {
      message.warning("变量名不能为空");
      return;
    }
    if (existingKeys.has(newVarName.trim())) {
      message.warning("变量名已存在");
      return;
    }
    const key = newVarName.trim();
    onOk(key, newVarValue, newVarType);
    setNewVarName("");
    setNewVarValue("");
    setNewVarType("text");
    message.success(`变量 {${key}} 已创建`);
  }, [newVarName, newVarValue, newVarType, existingKeys, onOk]);

  const handleCancel = () => {
    setNewVarName("");
    setNewVarValue("");
    setNewVarType("text");
    onCancel();
  };

  return (
    <Modal
      title={null}
      open={open}
      onOk={handleCreateVar}
      onCancel={handleCancel}
      okText="创建变量"
      cancelText="取消"
      width={460}
      destroyOnClose
      okButtonProps={{ className: "!rounded-xl !shadow-md !shadow-indigo-200" }}
      cancelButtonProps={{ className: "!rounded-xl" }}
    >
      <div className="flex flex-col gap-5">
        {/* header */}
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-indigo-100 to-indigo-200 flex items-center justify-center shrink-0 shadow-sm">
            <span className="text-indigo-500 text-lg font-bold">+</span>
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-800">创建变量</h3>
            <p className="text-[11px] text-slate-400">创建一个新的任务变量，后续可拖入布局</p>
          </div>
        </div>

        {/* name input */}
        <div>
          <span className="text-[11px] font-semibold text-slate-600 block mb-2">
            变量名 <span className="text-rose-400">*</span>
          </span>
          <Input
            size="middle"
            placeholder="输入变量名，例如 my_var"
            value={newVarName}
            onChange={(e) => setNewVarName(e.target.value)}
            onPressEnter={handleCreateVar}
            autoFocus
            prefix={<code className="text-[11px] text-slate-400">{`{`}</code>}
            suffix={<code className="text-[11px] text-slate-400">{`}`}</code>}
            className="!rounded-xl"
          />
        </div>

        {/* type selector */}
        <div>
          <span className="text-[11px] font-semibold text-slate-600 block mb-2">变量类型</span>
          <div className="grid grid-cols-2 gap-2">
            {VAR_TYPE_OPTS.map((o) => {
              const active = newVarType === o.value;
              const colors: Record<string, string> = {
                text: "#6366f1", number: "#10b981", bool: "#f59e0b", list: "#ec4899",
              };
              const color = colors[o.value] ?? "#6366f1";
              return (
                <button
                  key={o.value}
                  type="button"
                  onClick={() => setNewVarType(o.value)}
                  className={`text-left p-3 rounded-xl border-2 transition-all duration-150 ${
                    active
                      ? "border-current shadow-sm"
                      : "border-slate-100 hover:border-slate-200 hover:bg-slate-50"
                  }`}
                  style={active ? { borderColor: color, backgroundColor: `${color}08` } : undefined}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className="w-5 h-5 rounded-md flex items-center justify-center text-[10px] font-bold text-white shrink-0"
                      style={{ backgroundColor: color }}
                    >
                      {o.value === "text" ? "Aa" : o.value === "number" ? "12" : o.value === "switch" ? "⇄" : "[ ]"}
                    </span>
                    <span className="text-xs font-semibold text-slate-700">{o.label}</span>
                    {active && (
                      <span className="w-4 h-4 rounded-full flex items-center justify-center ml-auto shrink-0" style={{ backgroundColor: color }}>
                        <span className="text-[8px] text-white font-bold">✓</span>
                      </span>
                    )}
                  </div>
                  <span className="text-[10px] text-slate-400 leading-relaxed">{o.desc}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* value input */}
        <div>
          <span className="text-[11px] font-semibold text-slate-600 block mb-2">
            默认值 <span className="text-[10px] text-slate-400 font-normal">— 可选，留空则为空</span>
          </span>
          <Input
            size="middle"
            placeholder="例如 hello、123、true、[1,2,3]"
            value={newVarValue}
            onChange={(e) => setNewVarValue(e.target.value)}
            onPressEnter={handleCreateVar}
            className="!rounded-xl"
          />
        </div>

        {/* preview */}
        {newVarName.trim() && (
          <div className="rounded-2xl border border-slate-100 bg-gradient-to-br from-slate-50 to-white px-5 py-4 shadow-sm">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-2">预览</span>
            <div className="flex items-center gap-2 flex-wrap">
              <code className="text-xs font-mono font-semibold bg-indigo-50 text-indigo-600 px-2.5 py-1.5 rounded-xl shadow-sm">
                {`{${newVarName.trim()}}`}
              </code>
              {newVarValue && (
                <>
                  <span className="text-[10px] text-slate-300">=</span>
                  <span className="text-xs text-slate-600 font-mono font-medium">{newVarValue}</span>
                </>
              )}
            </div>
            <div className="mt-3 text-[10px] text-slate-400 flex items-center gap-1.5">
              <span className="inline-block w-1 h-1 rounded-full bg-slate-300" />
              类型：{VAR_TYPE_OPTS.find((o) => o.value === newVarType)?.label ?? newVarType}
              <span className="text-[10px] text-slate-300 ml-1">— {VAR_TYPE_OPTS.find((o) => o.value === newVarType)?.desc ?? ""}</span>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
};

export default CreateVarModal;
