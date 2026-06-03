import { AutoComplete, Input } from "antd";
import { useCallback } from "react";
import type { FC } from "react";
import * as React from "react";

interface Props {
  value: string
  onChange: (value: string) => void
  varOptions?: { value: string; label: string }[]
}

const excluded = new Set(["Process", "Unidentified", "Dead"]);

const KeyInput: FC<Props> = ({ value, onChange, varOptions = [] }) => {
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      // 用户输入 { 或退格时放行，允许输入/修改变量表达式
      if (e.key === "{" || e.key === "}" || e.key === "Backspace" || e.key === "Delete" || e.key === "ArrowLeft" || e.key === "ArrowRight" || e.key === "Home" || e.key === "End") {
        return;
      }
      if ((e.target as HTMLInputElement).value?.startsWith("{")) return;

      e.preventDefault();
      const key = e.key;
      if (excluded.has(key)) return;

      if (e.code.startsWith("Numpad") && /^[0-9]$/.test(key)) {
        onChange(`Num${key}`);
        return;
      }

      onChange(key.length === 1 ? key.toUpperCase() : key);
    },
    [onChange],
  );

  return (
    <AutoComplete
      size="small"
      className="w-full"
      value={value}
      onChange={(v) => onChange(v ?? "")}
      options={varOptions}
      filterOption={(input, option) =>
        option?.label?.toLowerCase().includes(input.toLowerCase()) ?? false
      }
    >
      <Input
        placeholder="—"
        className="!font-mono !text-sm"
        onKeyDown={handleKeyDown}
      />
    </AutoComplete>
  );
};

export default KeyInput;
