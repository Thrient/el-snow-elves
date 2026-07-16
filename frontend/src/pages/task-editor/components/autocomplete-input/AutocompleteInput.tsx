import { useState, useCallback, useEffect, type FC } from "react";
import { AutoComplete } from "antd";

export type AutocompleteType =
  | "action"
  | "template"
  | "step"
  | "variable"
  | "subflow";

interface Props {
  value?: string;
  onChange?: (value: string) => void;
  type: AutocompleteType;
  context?: {
    taskName?: string;
    version?: string;
    taskId?: string;
    variables?: string[];
    author?: string;
  };
  placeholder?: string;
  disabled?: boolean;
  allowClear?: boolean;
}

const cache = new Map<string, { value: string; label: string }[]>();

const AutocompleteInput: FC<Props> = ({
  value = "",
  onChange,
  type,
  context = {},
  placeholder,
  disabled,
  allowClear,
}) => {
  const [options, setOptions] = useState<{ value: string; label: string }[]>(
    () => cache.get(type) ?? []
  );

  const fetchSuggestions = useCallback(async () => {
    if (cache.has(type)) {
      setOptions(cache.get(type)!);
      return;
    }

    try {
      let result: { value: string; label: string }[];

      switch (type) {
        case "action":
          result = (await window.pywebview?.api.emit("API:AUTOCOMPLETE:ACTIONS")) ?? [];
          break;
        case "template": {
          const names: string[] = (await window.pywebview?.api.emit(
            "API:AUTOCOMPLETE:TEMPLATES",
            context.taskName ?? null,
            context.version ?? null,
            context.author ?? "匿名作者",
          )) ?? [];
          result = names.map((name) => ({ value: name, label: name }));
          break;
        }
        case "step":
          if (context.taskId) {
            const names: string[] = (await window.pywebview?.api.emit(
              "API:AUTOCOMPLETE:STEPS",
              context.taskId
            )) ?? [];
            result = names.map((name) => ({ value: name, label: name }));
          } else {
            result = [];
          }
          break;
        case "variable": {
          const items: { value: string; label: string }[] = [
            { value: "{result}", label: "{result}" },
          ];
          if (context.variables) {
            for (const key of context.variables) {
              items.push({
                value: `{${key}}`,
                label: `{${key}}`,
              });
            }
          }
          try {
            const settings = await window.pywebview?.api.emit("API:SETTINGS:LOAD");
            if (settings?.values) {
              for (const key of Object.keys(settings.values)) {
                items.push({
                  value: `{CONFIG.${key}}`,
                  label: `{CONFIG.${key}}`,
                });
              }
            }
          } catch {
            // settings not available
          }
          result = items;
          break;
        }
        case "subflow":
          if (context.taskId) {
            const names: string[] = (await window.pywebview?.api.emit(
              "API:AUTOCOMPLETE:STEPS",
              context.taskId
            )) ?? [];
            result = names.map((name) => ({ value: name, label: name }));
          } else {
            result = [];
          }
          break;
        default:
          result = [];
      }

      cache.set(type, result);
      setOptions(result);
    } catch {
      setOptions([]);
    }
  }, [type, context.taskName, context.version, context.taskId, context.author]);

  useEffect(() => {
    cache.delete(type);
  }, [type, context.taskName, context.version, context.taskId, context.author]);

  return (
    <AutoComplete
      value={value}
      onChange={(v) => onChange?.(v)}
      options={options}
      onFocus={fetchSuggestions}
      placeholder={placeholder}
      disabled={disabled}
      allowClear={allowClear}
      className="w-full"
      filterOption={(inputValue, option) =>
        option?.label?.toLowerCase().includes(inputValue.toLowerCase()) ?? false
      }
    />
  );
};

export default AutocompleteInput;
