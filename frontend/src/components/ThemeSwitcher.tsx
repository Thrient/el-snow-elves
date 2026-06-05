import { useCallback, type FC } from 'react';
import { useSettingsStore } from '@/store/settings-store';

const cycle = { light: 'dark', dark: 'auto', auto: 'light' } as const;

const ThemeSwitcher: FC = () => {
  const theme = useSettingsStore(s => s.theme);
  const setTheme = useSettingsStore(s => s.setTheme);

  const toggle = useCallback((e: React.MouseEvent) => {
    const next = cycle[theme] ?? 'light';
    const x = e.clientX;
    const y = e.clientY;

    if (document.startViewTransition) {
      document.documentElement.style.setProperty('--click-x', `${x}px`);
      document.documentElement.style.setProperty('--click-y', `${y}px`);
      document.startViewTransition(() => setTheme(next));
    } else {
      setTheme(next);
    }
  }, [theme, setTheme]);

  return (
    <button
      onClick={toggle}
      className="w-8 h-8 rounded-full flex items-center justify-center shrink-0
        border-none cursor-pointer shadow-sm hover:shadow-md hover:scale-110
        transition-all duration-200 overflow-hidden"
      style={{
        background: theme === 'auto' ? 'linear-gradient(135deg, #1677ff 50%, #1e293b 50%)'
                   : theme === 'dark' ? '#1e293b'
                   : '#fbbf24',
      }}
      title={`当前: ${theme === 'auto' ? '自动' : theme === 'light' ? '亮色' : '暗色'}`}
    >
      {theme === 'dark' ? (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        </svg>
      ) : theme === 'light' ? (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="5"/>
          <line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
          <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
        </svg>
      ) : (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="5"/>
          <line x1="12" y1="1" x2="12" y2="3"/>
          <line x1="12" y1="21" x2="12" y2="23"/>
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
          <line x1="1" y1="12" x2="3" y2="12"/>
          <line x1="21" y1="12" x2="23" y2="12"/>
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
        </svg>
      )}
    </button>
  );
};

export default ThemeSwitcher;
