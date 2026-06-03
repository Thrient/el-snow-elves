import { useState, useEffect, type FC } from "react";
import { Button, Popconfirm, Switch, Table, Tag } from "antd";
import type { ColumnsType } from "antd/es/table";
import {
  PlusOutlined, EditOutlined, DeleteOutlined,
  ClockCircleOutlined, ScheduleOutlined,
} from "@ant-design/icons";
import cronstrue from "cronstrue";
import "cronstrue/locales/zh_CN";
import type { Plan, PlanBase } from "@/types/plan";
import { PLAN_TEMPLATES } from "@/types/plan";
import { useUserStore } from "@/store/user-store";
import { useTaskStore } from "@/store/task-store";
import PlanModal from "./PlanModal";

let _planUid = Date.now();
const newPlanId = () => `plan_${++_planUid}`;

const PlansPage: FC = () => {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingPlan, setEditingPlan] = useState<Plan | null>(null);

  useEffect(() => {
    window.pywebview?.api.emit("API:PLAN:LOAD").then((data: unknown) => {
      if (Array.isArray(data)) setPlans(data);
    });
  }, []);

  const writePlans = async (next: Plan[]) => {
    setPlans(next);
    try {
      await window.pywebview?.api.emit("API:PLAN:SAVE", next);
    } catch { /* */ }
  };

  const handleSave = async (saved: PlanBase) => {
    if (editingPlan) {
      await writePlans(plans.map((p) => (p.id === editingPlan.id ? { ...saved, id: editingPlan.id, createdAt: editingPlan.createdAt, updatedAt: Date.now() } : p)));
    } else {
      const plan: Plan = { ...saved, id: newPlanId(), createdAt: Date.now(), updatedAt: Date.now() };
      await writePlans([...plans, plan]);
    }
    setModalOpen(false);
    setEditingPlan(null);
  };

  const handleDelete = async (id: string) => {
    await writePlans(plans.filter((p) => p.id !== id));
  };

  const handleToggle = async (id: string) => {
    await writePlans(plans.map((p) => (p.id === id ? { ...p, enabled: !p.enabled } : p)));
  };

  const addPlan = useUserStore((s) => s.addPlan);

  const handleAddToQueue = (plan: Plan) => {
    addPlan({
      name: plan.name,
      templateId: plan.templateId,
      cron: plan.cron,
      enabled: plan.enabled,
      action: plan.action,
    });
  };

  const openCreate = () => {
    setEditingPlan(null);
    setModalOpen(true);
  };

  const openEdit = (plan: Plan) => {
    setEditingPlan(plan);
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setEditingPlan(null);
  };

  const cronHuman = (expr: string): string => {
    try {
      return cronstrue.toString(expr, { locale: "zh_CN" });
    } catch {
      return expr;
    }
  };

  const columns: ColumnsType<Plan> = [
    {
      title: "计划名",
      dataIndex: "name",
      key: "name",
      width: 180,
      render: (name: string, record) => (
        <div className="flex items-center gap-2">
          <span className="font-medium text-[#1a1a2e]">{name}</span>
          {(() => {
            const t = PLAN_TEMPLATES.find((t) => t.id === record.templateId);
            return t ? <Tag className="!m-0 text-[10px]" color="blue">{t.name}</Tag> : null;
          })()}
        </div>
      ),
    },
    {
      title: "Cron",
      dataIndex: "cron",
      key: "cron",
      width: 200,
      render: (cron: string) => (
        <div className="text-xs">
          <div className="flex items-center gap-1">
            <ClockCircleOutlined className="text-[#8b8fa3]" />
            <span className="font-mono">{cron}</span>
          </div>
          <div className="text-[#8b8fa3] mt-0.5">{cronHuman(cron)}</div>
        </div>
      ),
    },
    {
      title: "参数",
      key: "params",
      render: (_, record) => {
        const params = record.action.params;
        if (record.action.type === "refill_queue") {
          const source = params.source === "config"
            ? `配置文件: ${params.configName || "—"}`
            : "默认队列";
          return <span className="text-xs text-[#6b7280]">{source}</span>;
        }
        if (record.action.type === "push_task") {
          const taskList = useTaskStore.getState().taskList;
          const task = taskList.find((t) => t.id === params.taskId);
          const label = task ? `${task.name} v${task.version}` : (params.taskId as string);
          return <span className="text-xs text-[#6b7280]">推送: {label}</span>;
        }
        return <span className="text-xs text-[#ccc]">—</span>;
      },
    },
    {
      title: "启用",
      key: "enabled",
      width: 60,
      render: (_, record) => (
        <Switch size="small" checked={record.enabled} onChange={() => handleToggle(record.id)} />
      ),
    },
    {
      title: "操作",
      key: "action",
      width: 130,
      render: (_, record) => (
        <div className="flex items-center gap-1">
          <Button type="text" size="small" className="!text-[#1677ff]" icon={<PlusOutlined />} onClick={() => handleAddToQueue(record)} />
          <Button type="text" size="small" icon={<EditOutlined />} onClick={() => openEdit(record)} />
          <Popconfirm
            title="确定删除此计划？"
            onConfirm={() => handleDelete(record.id)}
            okText="删除"
            cancelText="取消"
          >
            <Button type="text" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </div>
      ),
    },
  ];

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-header__left">
          <span className="page-header__accent" />
          <h2 className="page-header__title">
            <ScheduleOutlined className="mr-2 text-[#1677ff]" />
            计划任务
          </h2>
          <span className="page-header__badge">
            {plans.length}
          </span>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          创建计划
        </Button>
      </div>

      <div className="page-content thin-scrollbar">
        <Table
          columns={columns}
          dataSource={plans}
          rowKey="id"
          size="middle"
          pagination={false}
        />
      </div>

      <PlanModal
        open={modalOpen}
        plan={editingPlan}
        onClose={closeModal}
        onSave={handleSave}
      />
    </div>
  );
};

export default PlansPage;
