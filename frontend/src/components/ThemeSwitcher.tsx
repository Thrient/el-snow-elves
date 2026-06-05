import type { FC } from 'react';
import { Segmented } from 'antd';
import { useSettingsStore } from '@/store/settings-store';

const ThemeSwitcher: FC = () => {
  const theme = useSettingsStore(s => s.theme);
  const setTheme = useSettingsStore(s => s.setTheme);

  return (
    <Segmented
      size="small"
      value={theme}
      onChange={(v) => setTheme(v as typeof theme)}
      options={[
        { value: 'auto', label: '自动' },
        { value: 'light', label: '亮色' },
        { value: 'dark', label: '暗色' },
      ]}
    />
  );
};

export default ThemeSwitcher;
