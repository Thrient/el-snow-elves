import { useState, useRef, useEffect, type FC } from "react";

interface Props {
  delay: number;
  onChange: (delay: number) => void;
  isLast?: boolean;
}

const ComboConnector: FC<Props> = ({ delay, onChange, isLast }) => {
  const [editing, setEditing] = useState(false);
  const [temp, setTemp] = useState(String(delay));
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { setTemp(String(delay)); }, [delay]);

  useEffect(() => {
    if (editing) inputRef.current?.select();
  }, [editing]);

  const commit = () => {
    const v = parseInt(temp, 10);
    if (!isNaN(v) && v >= 0) onChange(v);
    else setTemp(String(delay));
    setEditing(false);
  };

  if (editing) {
    return (
      <div className="flex flex-col items-center px-3 shrink-0">
        <input
          ref={inputRef}
          className="
            w-40px text-center text-10px leading-normal
            color-[var(--color-primary)]
            bg-[var(--color-primary-bg)]
            border-none rounded-2px outline-none p-0
          "
          value={temp}
          onChange={(e) => setTemp(e.target.value)}
          onBlur={commit}
          onKeyDown={(e) => {
            if (e.key === "Enter") commit();
            if (e.key === "Escape") {
              setTemp(String(delay));
              setEditing(false);
            }
          }}
        />
        <span className="text-16px color-[#d0d5dd] leading-none mt-1px">
          {isLast ? "—⟳" : "—→"}
        </span>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center px-3 shrink-0">
      <span
        className="
          text-10px color-[var(--color-text-muted)] leading-normal mb-1px
          cursor-text
          hover:color-[var(--color-primary)]
          rounded-2px
        "
        onClick={() => setEditing(true)}
        title="点击编辑延迟"
      >
        {delay}ms
      </span>
      <span className="text-16px color-[#d0d5dd] leading-none">
        {isLast ? "—⟳" : "—→"}
      </span>
    </div>
  );
};

export default ComboConnector;
