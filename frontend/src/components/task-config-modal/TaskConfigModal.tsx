import { useState } from "react"
import type { FC } from "react"
import { Modal } from "antd"
import type { Task } from "@/types/task.ts"
import SettingsField from "@/components/settings-field/SettingsField"
import { useGroupLabelWidths } from "@/hooks/useRowLabelWidths"

interface Props {
  open: boolean
  task: Task | null
  onClose: () => void
  onSave: (values: Record<string, unknown>) => void
}

const TaskConfigModal: FC<Props> = ({ open, task, onClose, onSave }) => {
  const [formValues, setFormValues] = useState<Record<string, unknown>>(
    () => task?.values ?? {}
  )

  const layout = task?.layout ?? []
  const labelWidths = useGroupLabelWidths(layout)

  const handleOk = () => {
    onSave(formValues)
    onClose()
  }

  if (!task) return null

  return (
    <Modal title={`配置 - ${task.name}`} open={open} onCancel={onClose} onOk={handleOk} centered>
      <div
        className="grid gap-x-4 gap-y-3 mt-4 grid-cols-[repeat(24,1fr)]"
      >
        {layout.map((row, rowIndex) => {
          let col = 1
          return row.map((cell, ci) => {
            const start = col
            col += cell.span ?? 1
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
                  value={cell.store ? formValues[cell.store] : undefined}
                  onChange={cell.store
                    ? (v) => setFormValues((prev) => ({ ...prev, [cell.store as string]: v }))
                    : () => {}
                  }
                  labelWidth={labelWidths[rowIndex]?.[ci]}
                />
              </div>
            )
          })
        })}
      </div>
    </Modal>
  )
}

export type { Props as TaskConfigModalProps }
export default TaskConfigModal
