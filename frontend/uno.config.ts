import {
  defineConfig,
  presetAttributify,
  presetIcons,
  presetTypography,
  presetWebFonts,
  presetWind3,
  transformerDirectives,
  transformerVariantGroup
} from 'unocss'

export default defineConfig({
  shortcuts: [
    // Page container
    ['page-container', 'flex flex-col h-full bg-white rounded-lg mx-4 mb-4 p-4 shadow-sm border border-[var(--color-border)]'],
    // Section header with colored dot
    ['section-dot', 'w-1 h-4 rounded-full shrink-0'],
    // Interactive card
    ['card-interactive', 'rounded-xl border border-[var(--color-border)] bg-white hover:border-[#dde0e6] hover:shadow-sm transition-all cursor-pointer'],
  ],
  theme: {
    colors: {
      primary: '#1677ff',
      'primary-bg': 'rgba(22, 119, 255, 0.08)',
      success: '#52c41a',
      warning: '#fa8c16',
      danger: '#ff4d4f',
      purple: '#722ed1',
      cyan: '#13c2c2',
      heading: '#1a1a2e',
      muted: '#8b8fa3',
      border: '#eef0f2',
      container: '#fafbfc',
    },
  },
  presets: [
    presetWind3(),
    presetAttributify(),
    presetIcons(),
    presetTypography(),
    presetWebFonts({
      fonts: {
      },
    }),
  ],
  transformers: [
    transformerDirectives(),
    transformerVariantGroup(),
  ],
})
