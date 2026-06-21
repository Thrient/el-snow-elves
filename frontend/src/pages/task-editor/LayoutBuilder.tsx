import {
  useState, useCallback, useMemo,
  type FC, type DragEvent as ReactDragEvent,
} from "react";
import type { Cell, CellModel, VarType } from "@/types/task";
import { DEFAULT_CELL_SPAN } from "@/types/task-editor/field-config";
import ComponentPickerModal from "./ComponentPickerModal";
import UnboundPanel from "./components/UnboundPanel";
import CreateVarModal from "./components/CreateVarModal";
import GridCanvas from "./components/GridCanvas";

/* ── helpers ── */

export function cloneLayout(l: Cell[][]): Cell[][] {
  return l.map((r) => r.map((c) => ({ ...c })));
}

export function usedStores(layout: Cell[][]): Set<string> {
  const s = new Set<string>();
  for (const r of layout) for (const c of r) if (c.store) s.add(c.store);
  return s;
}

/* ── props ── */

export interface LayoutBuilderProps {
  initialLayout?: Cell[][];
  initialValues?: Record<string, unknown>;
  initialValueTypes?: Record<string, VarType>;
  onConfirm?: (layout: Cell[][], values: Record<string, unknown>, valueTypes: Record<string, VarType>) => void;
  onCancel?: () => void;
}

/* ── main ── */

const LayoutBuilder: FC<LayoutBuilderProps> = ({ initialLayout = [], initialValues = {}, initialValueTypes = {}, onConfirm, onCancel }) => {
  const [layout, setLayout] = useState<Cell[][]>(() => cloneLayout(initialLayout));
  const [values, setValues] = useState<Record<string, unknown>>({ ...initialValues });
  const [valueTypes, setValueTypes] = useState<Record<string, VarType>>({ ...initialValueTypes });

  // selection
  const [sel, setSel] = useState<{ ri: number; ci: number } | null>(null);

  // picker state
  const [pickerOpen, setPickerOpen] = useState(false);
  const [pendingVar, setPendingVar] = useState<{ name: string; value: unknown; type: VarType; ri: number; ci: number } | null>(null);

  // drag state
  const [dragFromLeft, setDragFromLeft] = useState<{ key: string } | null>(null);

  // create variable modal
  const [createVarOpen, setCreateVarOpen] = useState(false);

  /* ── computed ── */

  const unboundVars = useMemo(() => {
    const used = usedStores(layout);
    return Object.entries(values)
      .filter(([k]) => !used.has(k))
      .map(([k, v]) => ({ key: k, value: v, type: valueTypes[k] ?? "text" as const }));
  }, [values, layout, valueTypes]);

  const existingKeys = useMemo(() => new Set(Object.keys(values)), [values]);

  /* ── layout ops ── */

  const addCell = useCallback((ri: number, ci: number, store: string, model: CellModel) => {
    setLayout((prev) => {
      const next = cloneLayout(prev);
      const cell: Cell = { span: DEFAULT_CELL_SPAN, model, store };
      if (!next[ri]) {
        next.push([cell]);
      } else {
        next[ri].splice(ci, 0, cell);
      }
      return next;
    });
  }, []);

  const updateCell = useCallback((ri: number, ci: number, patch: Partial<Cell>) => {
    setLayout((prev) => {
      const next = cloneLayout(prev);
      if (next[ri]) next[ri][ci] = { ...next[ri][ci], ...patch };
      return next;
    });
  }, []);

  const removeCell = useCallback((ri: number, ci: number) => {
    setLayout((prev) => {
      const next = cloneLayout(prev);
      next[ri] = next[ri].filter((_, j) => j !== ci);
      return next.filter((r) => r.length > 0);
    });
    setSel(null);
  }, []);

  const moveCell = useCallback((fromRi: number, fromCi: number, toRi: number, toCi: number) => {
    setLayout((prev) => {
      const next = cloneLayout(prev);
      const cell = next[fromRi]?.[fromCi];
      if (!cell) return prev;
      next[fromRi].splice(fromCi, 1);
      if (next[fromRi].length === 0) next.splice(fromRi, 1);
      // Adjust target indices after removal
      let adjRi = toRi;
      let adjCi = toCi;
      if (fromRi === toRi && fromCi < toCi) adjCi = toCi - 1;
      if (fromRi < toRi) adjRi = toRi - 1;
      if (!next[adjRi]) next[adjRi] = [];
      next[adjRi].splice(adjCi, 0, cell);
      return next;
    });
    setSel({ ri: toRi, ci: toCi });
  }, []);

  const moveRow = useCallback((fromRi: number, toRi: number) => {
    setLayout((prev) => {
      const next = cloneLayout(prev);
      const [row] = next.splice(fromRi, 1);
      next.splice(toRi, 0, row);
      return next;
    });
    if (sel?.ri === fromRi) setSel({ ri: toRi, ci: sel.ci });
  }, [sel]);

  const addRow = useCallback(() => {
    setLayout((prev) => [...cloneLayout(prev), []]);
  }, []);

  const deleteRow = useCallback((ri: number) => {
    setLayout((prev) => cloneLayout(prev).filter((_, i) => i !== ri));
    if (sel?.ri === ri) setSel(null);
  }, [sel]);

  /* ── picker callback ── */

  const handlePickerSelect = useCallback((model: CellModel) => {
    if (pendingVar) {
      addCell(pendingVar.ri, pendingVar.ci, pendingVar.name, model);
    }
    setPickerOpen(false);
    setPendingVar(null);
  }, [pendingVar, addCell]);

  /* ── drop handler (left → right) ── */

  const handleDrop = useCallback((ri: number, ci: number, e: ReactDragEvent) => {
    e.preventDefault();
    const key = e.dataTransfer.getData("text/plain");
    if (!key) return;
    const val = values[key];
    if (val === undefined) return;
    setPendingVar({ name: key, value: val, type: valueTypes[key] ?? "text", ri, ci });
    setPickerOpen(true);
  }, [values, valueTypes]);

  const handleDragOverRow = useCallback((ri: number, e: ReactDragEvent) => {
    e.preventDefault();
    const row = layout[ri];
    const used = row ? row.reduce((s, c: Cell) => s + (c.span ?? 1), 0) : 0;
    const remaining = 24 - used;
    if (remaining >= DEFAULT_CELL_SPAN) {
      e.dataTransfer.dropEffect = "move";
    } else {
      e.dataTransfer.dropEffect = "none";
    }
  }, [layout]);

  /* ── cell drag (within grid) ── */

  const handleCellDragStart = useCallback((ri: number, ci: number, e: ReactDragEvent) => {
    e.dataTransfer.setData("application/layout-move", JSON.stringify({ ri, ci }));
    e.dataTransfer.effectAllowed = "move";
  }, []);

  const handleRowDragStart = useCallback((ri: number, e: ReactDragEvent) => {
    e.dataTransfer.setData("application/layout-row-move", String(ri));
    e.dataTransfer.effectAllowed = "move";
  }, []);

  const handleRowDrop = useCallback((toRi: number, e: ReactDragEvent) => {
    e.preventDefault();
    const raw = e.dataTransfer.getData("application/layout-row-move");
    if (!raw) return;
    const fromRi = parseInt(raw, 10);
    if (fromRi === toRi) return;
    moveRow(fromRi, toRi);
  }, [moveRow]);

  const handleCellDrop = useCallback((toRi: number, toCi: number, e: ReactDragEvent) => {
    e.preventDefault();
    const raw = e.dataTransfer.getData("application/layout-move");
    if (!raw) return;
    const { ri: fromRi, ci: fromCi } = JSON.parse(raw);
    if (fromRi === toRi && fromCi === toCi) return;
    moveCell(fromRi, fromCi, toRi, toCi);
  }, [moveCell]);

  /* ── confirm ── */

  const deleteVar = useCallback((key: string) => {
    setValues((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
    setValueTypes((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
    // 同步清理 layout 中引用该变量的 cell
    setLayout((prev) => cloneLayout(prev).map((row) =>
      row.filter((cell) => cell.store !== key),
    ).filter((row) => row.length > 0));
  }, []);

  const handleCreateVar = useCallback((name: string, value: unknown, type: VarType) => {
    setValues((prev) => ({ ...prev, [name]: value }));
    setValueTypes((prev) => ({ ...prev, [name]: type }));
    setCreateVarOpen(false);
  }, []);

  const handleConfirm = () => {
    const final = cloneLayout(layout).filter((r) => r.length > 0);
    const used = usedStores(final);
    const finalVals: Record<string, unknown> = {};
    for (const k of used) finalVals[k] = values[k] ?? "";
    // also include unbound variables
    for (const [k, v] of Object.entries(values)) {
      if (!(k in finalVals)) finalVals[k] = v ?? "";
    }
    // Clean up valueTypes for deleted vars
    const finalTypes: Record<string, VarType> = {};
    for (const k of Object.keys(finalVals)) {
      finalTypes[k] = valueTypes[k] ?? "text";
    }
    onConfirm?.(final, finalVals, finalTypes);
  };

  /* ═══════════════════════════════════════════════
     RENDER
     ═══════════════════════════════════════════════ */

  return (
    <div className="flex gap-4 select-none min-h-480px" style={{ maxHeight: "calc(100vh - 200px)" }}>

      {/* ═══ LEFT: 待布局变量 ═══ */}
      <UnboundPanel
        unboundVars={unboundVars}
        values={values}
        dragFromLeft={dragFromLeft}
        onDragStart={(key) => setDragFromLeft({ key })}
        onDragEnd={() => setDragFromLeft(null)}
        onDeleteVar={deleteVar}
        onCreateVar={() => setCreateVarOpen(true)}
      />

      {/* ═══ RIGHT: 布局画布 ═══ */}
      <GridCanvas
        layout={layout}
        sel={sel}
        setSel={setSel}
        dragFromLeft={dragFromLeft}
        values={values}
        valueTypes={valueTypes}
        onAddRow={addRow}
        onDeleteRow={deleteRow}

        onCellDrop={handleCellDrop}
        onCellDragStart={handleCellDragStart}
        onRowDragOver={handleDragOverRow}
        onRowDragStart={handleRowDragStart}
        onRowDrop={handleRowDrop}
        onDrop={handleDrop}
        onCellUpdate={updateCell}
        onCellRemove={removeCell}
        onChangeControl={(cell, ri, ci) => {
          setPendingVar({ name: cell.store ?? "", value: values[cell.store ?? ""] ?? "", type: valueTypes[cell.store ?? ""] ?? "text", ri, ci });
          setPickerOpen(true);
        }}
        onChangeValue={(store, value) => {
          setValues((prev) => ({ ...prev, [store]: value }));
        }}
        onCancel={onCancel ?? (() => {})}
        onConfirm={handleConfirm}
      />

      {/* ═══ ComponentPickerModal ═══ */}
      <ComponentPickerModal
        open={pickerOpen}
        varName={pendingVar?.name ?? ""}
        varValue={pendingVar?.value ?? ""}
        varType={pendingVar?.type}
        onSelect={handlePickerSelect}
        onCancel={() => { setPickerOpen(false); setPendingVar(null); }}
      />

      {/* ═══ Create Variable Modal ═══ */}
      <CreateVarModal
        open={createVarOpen}
        existingKeys={existingKeys}
        onOk={handleCreateVar}
        onCancel={() => setCreateVarOpen(false)}
      />
    </div>
  );
};

export default LayoutBuilder;
