import { useState, useEffect, useMemo, type FC } from "react";
import { Button, Input, Modal, Select, Form, Tag } from "antd";
import cronstrue from "cronstrue";
import "cronstrue/locales/zh_CN";
import type { Plan, PlanBase, PlanTemplate } from "@/types/plan";
import { PLAN_TEMPLATES } from "@/types/plan";
import { useTaskStore } from "@/store/task-store";
import { callApi } from "@/utils/pywebview";
import type { FullTask } from "@/types/task";
import SettingsField from "@/components/settings-field/SettingsField";
import { useGroupLabelWidths } from "@/hooks/useRowLabelWidths";

const CRON_PRESETS = [
  { label: "每分钟", value: "* * * * *" },
  { label: "每30分钟", value: "*/30 * * * *" },
  { label: "每小时整点", value: "0 * * * *" },
  { label: "每2小时1点", value: "1 */2 * * *" },
  { label: "每天19点", value: "0 19 * * *" },
  { label: "每天19点25分", value: "25 19 * * *" },
  { label: "工作日1点2分", value: "2 1 * * 1-5" },
  { label: "每周六19点45分", value: "45 19 * * 6" },
  { label: "每周一三五12点", value: "0 12 * * 1,3,5" },
  { label: "每月1号2点3分", value: "3 2 1 * *" },
  { label: "每月1号15号9点", value: "0 9 1,15 * *" },
];

interface Props {
  open: boolean;
  plan: Plan | PlanBase | null;
  onClose: () => void;
  onSave: (plan: PlanBase) => void;
}

const PlanModal: FC<Props> = ({ open, plan, onClose, onSave }) => {
  const [form] = Form.useForm();
  const [template, setTemplate] = useState<PlanTemplate | null>(null);
  const [cronError, setCronError] = useState<string | null>(null);
  const [configFiles, setConfigFiles] = useState<string[]>([]);
  const taskList = useTaskStore((s) => s.taskList);
  const watchedSource = Form.useWatch("source", form);
  const watchedTaskId = Form.useWatch("taskId", form);
  const [taskLayout, setTaskLayout] = useState<FullTask["layout"] | null>(null);
  const [taskValues, setTaskValues] = useState<Record<string, unknown>>({});
  const taskLabelWidths = useGroupLabelWidths(taskLayout ?? []);
  useEffect(() => {
    if (!watchedTaskId) {
      setTaskLayout(null);
      setTaskValues({});
      return;
    }
    callApi<FullTask>("API:TASK:LOAD:FULL", watchedTaskId).then((full) => {
      if (full) {
        setTaskLayout(full.layout ?? null);
        // 编辑模式优先使用已保存的值
        const savedValues = plan?.action?.params?.values as Record<string, unknown> | undefined;
        setTaskValues(savedValues ?? full.values ?? {});
      } else {
        setTaskLayout(null);
        setTaskValues({});
      }
    });
  }, [watchedTaskId, plan]);

  useEffect(() => {
    if (!open) return;
    callApi<string[]>("API:SCRIPT:LOAD:CONFIG:LIST").then((v) => setConfigFiles(v ?? []));
  }, [open]);

  const isEdit = plan !== null;

  useEffect(() => {
    if (!open) return;
    if (plan) {
      const tmpl = PLAN_TEMPLATES.find((t) => t.id === plan.templateId) ?? PLAN_TEMPLATES[0];
      setTemplate(tmpl);
      form.setFieldsValue({
        name: plan.name,
        cron: plan.cron,
        ...plan.action.params,
      });
    } else {
      setTemplate(null);
      form.resetFields();
    }
    setCronError(null);
  }, [open, plan, form]);

  const validateCron = (expr: string): boolean => {
    try {
      cronstrue.toString(expr, { locale: "zh_CN" });
      setCronError(null);
      return true;
    } catch {
      setCronError("无效的 cron 表达式");
      return false;
    }
  };

  const watchedCron: string = Form.useWatch("cron", form) ?? "";

  const cronHuman = useMemo(() => {
    const expr = watchedCron || template?.defaultCron || "";
    if (!expr) return "";
    try {
      return cronstrue.toString(expr, { locale: "zh_CN" });
    } catch {
      return "";
    }
  }, [watchedCron, template]);

  const selectTemplate = (tmpl: PlanTemplate) => {
    setTemplate(tmpl);
    form.setFieldsValue({ cron: tmpl.defaultCron });
    setCronError(null);
  };

  const handleFinish = (values: Record<string, unknown>) => {
    const { name, cron, ...rest } = values;
    if (!validateCron(cron as string)) return;
    if (!template) return;

    const params = { ...rest };
    if (template.id === "push_task") {
      params.values = taskValues;
    }

    const result: PlanBase = {
      name: name as string,
      templateId: template.id,
      cron: cron as string,
      enabled: plan?.enabled ?? true,
      action: {
        type: template.actionType,
        params,
      },
    };
    onSave(result);
  };

  const handleClose = () => {
    setTemplate(null);
    onClose();
  };

  const taskOptions = taskList.map((t) => ({
    value: t.id,
    label: `${t.name} v${t.version}`,
  }));

  return (
    <Modal
      title={isEdit ? "编辑计划" : "创建计划"}
      open={open}
      onCancel={handleClose}
      onOk={template ? () => form.submit() : undefined}
      okText={template ? "保存" : undefined}
      okButtonProps={template ? undefined : { style: { display: "none" } }}
      cancelText="取消"
      width={taskLayout ? 640 : 480}
    >
      {/* Step 1: Select template */}
      {!template && !isEdit && (
        <div className="flex flex-col gap-2">
          <div className="text-sm text-[#8b8fa3] mb-1">请选择计划模板</div>
          {PLAN_TEMPLATES.map((tmpl) => (
            <div
              key={tmpl.id}
              onClick={() => selectTemplate(tmpl)}
              className="p-4 rounded-lg border border-[#e8e8ed] cursor-pointer hover:border-[#1677ff] hover:bg-[#f0f5ff] transition-colors"
            >
              <div className="flex items-center gap-2 mb-1">
                <Tag color="blue">{tmpl.name}</Tag>
                <span className="font-mono text-xs text-[#8b8fa3]">{tmpl.defaultCron}</span>
              </div>
              <div className="text-xs text-[#8b8fa3]">{tmpl.description}</div>
            </div>
          ))}
        </div>
      )}

      {/* Step 2: Fill form */}
      {(template || isEdit) && (
        <Form form={form} layout="vertical" onFinish={handleFinish}>
          {!isEdit && template && (
            <div className="flex items-center gap-2 mb-4 p-3 bg-[#f0f5ff] rounded-lg">
              <Tag color="blue">{template.name}</Tag>
              <span className="text-xs text-[#8b8fa3]">{template.description}</span>
              <Button type="link" size="small" className="ml-auto" onClick={() => setTemplate(null)}>
                更换模板
              </Button>
            </div>
          )}

          <Form.Item
            label="计划名称"
            name="name"
            rules={[{ required: true, message: "请输入计划名称" }]}
          >
            <Input placeholder="如：五点刷新日常" />
          </Form.Item>

          <Form.Item label="Cron 表达式">
            <div className="flex items-center gap-1 mb-2 flex-wrap">
              {CRON_PRESETS.map((p) => (
                <Tag
                  key={p.value}
                  className="cursor-pointer text-[11px]"
                  color={form.getFieldValue("cron") === p.value ? "blue" : "default"}
                  onClick={() => {
                    form.setFieldValue("cron", p.value);
                    validateCron(p.value);
                  }}
                >
                  {p.label}
                </Tag>
              ))}
            </div>
            <Form.Item
              name="cron"
              noStyle
              rules={[{ required: true, message: "请输入 cron 表达式" }]}
            >
              <Input
                placeholder="0 17 * * *"
                onChange={(e) => validateCron(e.target.value)}
                className={cronError ? "border-[#ff4d4f]" : ""}
              />
            </Form.Item>
            {cronError && <div className="text-[#ff4d4f] text-xs mt-1">{cronError}</div>}
            {!cronError && cronHuman && <div className="text-[#8b8fa3] text-xs mt-1">「{cronHuman}」</div>}
          </Form.Item>

          {template?.id === "restart" && (
            <>
              <Form.Item label="填充来源" name="source" initialValue="current_queue">
                <Select
                  options={[
                    { value: "current_queue", label: "默认队列（绑定窗口时传入的队列）" },
                    { value: "config", label: "配置文件（从任务配置中读取）" },
                  ]}
                />
              </Form.Item>
              {watchedSource === "config" && (
                <Form.Item
                  label="配置文件名"
                  name="configName"
                  rules={[{ required: true, message: "请选择配置文件" }]}
                >
                  <Select
                    placeholder="选择配置文件"
                    options={configFiles.map((f) => ({ value: f, label: f }))}
                    showSearch
                    filterOption={(input, option) =>
                      (option?.label as string)?.toLowerCase().includes(input.toLowerCase())
                    }
                  />
                </Form.Item>
              )}
            </>
          )}

          {template?.id === "push_task" && (
            <>
              <Form.Item
                label="要推送的任务"
                name="taskId"
                rules={[{ required: true, message: "请选择任务" }]}
              >
                <Select
                  placeholder="选择任务"
                  options={taskOptions}
                  showSearch
                  filterOption={(input, option) =>
                    (option?.label as string)?.toLowerCase().includes(input.toLowerCase())
                  }
                />
              </Form.Item>
              {taskLayout && (
                <div className="mb-4 p-3 bg-[#fafbfc] rounded-lg border border-[#f0f0f5]">
                  <div className="text-xs text-[#8b8fa3] mb-2">任务参数</div>
                  <div
                    className="grid gap-x-4 gap-y-3"
                    style={{ gridTemplateColumns: `repeat(24, 1fr)` }}
                  >
                    {taskLayout.map((row, rowIndex) => {
                      let col = 1;
                      return row.map((cell, ci) => {
                        const start = col;
                        col += cell.span ?? 1;
                        return (
                          <div
                            key={cell.store ?? cell.text ?? rowIndex}
                            style={{
                              gridRow: rowIndex + 1,
                              gridColumn: `${start} / span ${cell.span ?? 1}`,
                            }}
                          >
                            <SettingsField
                              cell={cell}
                              value={cell.store ? taskValues[cell.store] : undefined}
                              onChange={cell.store
                                ? (v) => setTaskValues((prev) => ({ ...prev, [cell.store as string]: v }))
                                : () => {}
                              }
                              labelWidth={taskLabelWidths[rowIndex]?.[ci]}
                            />
                          </div>
                        );
                      });
                    })}
                  </div>
                </div>
              )}
            </>
          )}
        </Form>
      )}
    </Modal>
  );
};

export default PlanModal;
