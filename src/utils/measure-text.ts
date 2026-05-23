let canvas: HTMLCanvasElement | null = null

function getCtx(): CanvasRenderingContext2D {
  if (!canvas) {
    canvas = document.createElement("canvas")
  }
  return canvas.getContext("2d")!
}

/** Measure pixel width of text with the given CSS font shorthand. */
export function measureTextWidth(text: string, font: string): number {
  const ctx = getCtx()
  ctx.font = font
  return ctx.measureText(text).width
}
