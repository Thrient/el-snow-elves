# 锁定启动步骤 — 设计文档

**日期：** 2026-06-27
**范围：** `el-snow-elves` 桌面项目 — 任务编辑器

## 需求

创建任务时自动生成一个默认「启动」步骤，并设为起始步骤。启动步骤的**内容**可编辑（名称、动作、参数等），但 `start` 字段**不可更改**指向其他步骤，启动步骤**不可删除**。

## 当前行为

- `TaskRepository.create()` 创建任务时 `start: ""`，`steps: {}`
- 用户需手动在画布上双击创建步骤
- `TaskSettingsModal` 提供 Select 下拉框自由更改起始步骤
- 步骤面板和画布上可删除任意步骤（包括启动步骤）

## 目标行为

| 操作 | 当前 | 目标 |
|------|------|------|
| 创建任务 | 空 steps，空 start | 自动创建 `开始执行` 步骤，`start: "开始执行"` |
| 修改起始步骤指向 | 可随意改 | **不可改**（只读展示） |
| 删除启动步骤 | 可删除 | **不可删除**（面板按钮禁用 + 画布 Delete 键过滤） |
| 编辑启动步骤内容 | N/A（无默认步骤） | 可编辑（名称、action、params、流程跳转等） |
| 重命名启动步骤 | N/A | 可重命名（同步更新 `start` 字段） |

## 改动清单

### 1. `backend/script/task/TaskRepository.py` — `create()`

```python
# 改前
"start": "",
"steps": {},

# 改后
"start": "开始执行",
"steps": {"开始执行": {"action": "", "params": {}}},
```

### 2. `frontend/src/pages/task-editor/TaskSettingsModal.tsx`

起始步骤行：`Select` → 只读 `Tag`

```tsx
// 改前
<Select value={task.start || undefined} options={startOpts.map(...)} onChange={(v) => updateStart(v ?? "")} />

// 改后
<Tag color="green" className="text-[12px]">{task.start || "未设置"}</Tag>
```

移除不再需要的 `updateStart` 调用和 `startOpts` 计算。

### 3. `frontend/src/pages/task-editor/StepPanel.tsx`

新增 `isStart` prop，启动步骤时禁用删除按钮：

```tsx
interface Props {
  // ... 现有字段
  isStart: boolean;  // 新增
}

// 删除按钮
<Tooltip title={isStart ? "启动步骤不可删除" : "删除步骤"}>
  <Button danger icon={<DeleteOutlined />} disabled={isStart} onClick={onDelete} />
</Tooltip>
```

### 4. `frontend/src/pages/task-editor/TaskEditorPage.tsx`

画布节点删除回调中过滤启动步骤：

```tsx
onNodesDelete={(ids) => {
  ids.forEach((id) => {
    if (id === editor.currentTask?.start) return; // 新增守卫
    const isCommon = id in (editor.currentTask?.common ?? {});
    editor.removeStep(id, isCommon);
  });
}}
```

StepPanel 渲染时传入 `isStart`：

```tsx
<StepPanel
  // ... 现有 props
  isStart={drawerStep.name === editor.currentTask?.start}
/>
```

### 5. `frontend/src/store/editor-store.ts` — `removeStep()`

```ts
removeStep: (name, isCommon) => {
  const { currentTask } = get();
  if (!currentTask || name === currentTask.start) return; // 新增守卫
  // ... 现有逻辑
}
```

### 6. 重命名启动步骤时的同步

`renameStep` 已存在，需额外处理：如果旧名称等于 `start`，同步更新 `start` 为新名称：

```ts
renameStep: (oldName, newName, isCommon) => {
  // ... 现有重命名逻辑
  // 新增：如果重命名的是启动步骤，同步更新 start
  if (oldName === currentTask.start) {
    updated.start = newName;
  }
  set({ currentTask: updated, isDirty: true });
}
```

## 不变的部分

- 步骤内容编辑器（动作选择、参数编辑、流程跳转、前置/后置步骤等）完全不变
- 画布拖拽、连线逻辑不变
- 保存/另存为/版本管理不变
- 公共步骤机制不变
- `start` 字段的 JSON 存储格式不变

## 自检

- [x] 无 TBD / TODO
- [x] 各改动无矛盾
- [x] 范围聚焦单一功能，无需分解
- [x] 所有行为边界明确（删除、重命名、面板操作、画布操作）
