export function insertAtCursor(text: string): boolean {
  const el = document.activeElement;
  if (
    !el ||
    !("selectionStart" in el) ||
    !("selectionEnd" in el)
  ) {
    return false;
  }

  const input = el as HTMLInputElement | HTMLTextAreaElement;
  const start = input.selectionStart ?? 0;
  const end = input.selectionEnd ?? 0;
  const before = input.value.substring(0, start);
  const after = input.value.substring(end);
  input.value = before + text + after;
  input.selectionStart = input.selectionEnd = start + text.length;

  // Trigger React synthetic event to keep controlled components in sync
  const nativeSetter = Object.getOwnPropertyDescriptor(
    window.HTMLInputElement.prototype,
    "value"
  )?.set;
  nativeSetter?.call(input, input.value);
  input.dispatchEvent(new Event("input", { bubbles: true }));
  input.focus();
  return true;
}
