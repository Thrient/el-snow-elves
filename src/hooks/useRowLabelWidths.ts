import { useMemo } from "react"
import type { Cell } from "@/types/task"
import { measureTextWidth } from "@/utils/measure-text"

const LABEL_FONT = '600 0.875rem "Microsoft YaHei", "PingFang SC", sans-serif'

/**
 * Group cells by their grid-column-start position and compute the max label
 * width per start column. Cells that begin at the same column (regardless of
 * span or row structure) share the same label width — like form columns.
 *
 * Returns a 2D array matching `layout`: `result[row][col]` is the label width
 * in pixels, or `undefined` for cells without a label.
 */
export function useGroupLabelWidths(layout: Cell[][]): (number | undefined)[][] {
  return useMemo(() => {
    // 1. Collect max label width per grid-column-start
    const colMaxes = new Map<number, number>()

    for (const row of layout) {
      let col = 1
      for (const cell of row) {
        const start = col
        col += cell.span ?? 1
        if (cell.store && cell.text) {
          const w = measureTextWidth(cell.text + "：", LABEL_FONT)
          const prev = colMaxes.get(start) ?? 0
          if (w > prev) colMaxes.set(start, w)
        }
      }
    }

    // 2. Build result matching the layout shape
    return layout.map((row) => {
      let col = 1
      return row.map((cell) => {
        const start = col
        col += cell.span ?? 1
        if (cell.store && cell.text) {
          return Math.ceil(colMaxes.get(start) ?? 64)
        }
        return undefined
      })
    })
  }, [layout])
}
