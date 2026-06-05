import { useState, useRef, useEffect, type FC } from 'react';
import { useSettingsStore } from '@/store/settings-store';

const THEMES = [
  { key: 'auto', label: '自动' },
  { key: 'light', label: '亮色' },
  { key: 'dark', label: '暗色' },
  { key: 'sakura', label: '樱花' },
  { key: 'ink', label: '墨韵' },
  { key: 'bamboo', label: '竹林' },
  { key: 'comic', label: '漫画' },
  { key: 'sunset', label: '日落' },
  { key: 'illust', label: '插画' },
] as const;

const THEME_COLORS: Record<string, { color1: string; color2?: string }> = {
  auto: { color1: '#1677ff', color2: '#16171d' },
  light: { color1: '#1677ff' },
  dark: { color1: '#4096ff' },
  sakura: { color1: '#e87a5a' },
  ink: { color1: '#475569' },
  bamboo: { color1: '#059669' },
  comic: { color1: '#f5222d' },
  sunset: { color1: '#e65100' },
  illust: { color1: '#c2410c' },
};

const ThemeSwitcher: FC = () => {
  const theme = useSettingsStore(s => s.theme);
  const setTheme = useSettingsStore(s => s.setTheme);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const current = THEME_COLORS[theme] ?? THEME_COLORS.auto;

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="w-6 h-6 rounded-full shadow-sm hover:shadow-md hover:scale-110 transition-all duration-200 shrink-0 border-none cursor-pointer"
        style={{
          background: current.color2
            ? `linear-gradient(90deg, ${current.color1} 50%, ${current.color2} 50%)`
            : current.color1,
        }}
        title="切换主题"
      />
      {open && (
        <div className="absolute top-9 right-0 bg-white rounded-lg shadow-popover p-2 flex flex-col gap-0.5 z-50 min-w-[120px] border border-border">
          {THEMES.map(({ key, label }) => {
            const c = THEME_COLORS[key];
            return (
              <button
                key={key}
                onClick={() => { setTheme(key as typeof theme); setOpen(false); }}
                className={`flex items-center gap-2 px-2 py-1.5 rounded-md text-xs
                  transition-colors hover:bg-container text-left border-none bg-transparent cursor-pointer
                  ${theme === key ? 'bg-primary-bg font-semibold text-heading' : 'text-body'}`}
              >
                <span
                  className="w-4 h-4 rounded-full shrink-0"
                  style={{
                    background: c.color2
                      ? `linear-gradient(90deg, ${c.color1} 50%, ${c.color2} 50%)`
                      : c.color1,
                  }}
                />
                {label}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ThemeSwitcher;
