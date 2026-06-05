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
    // ── Page shell ──
    ['page-container', 'flex flex-col bg-white rounded-lg mx-4 mb-4 shadow-sm'],
    ['page-header',   'flex items-center justify-between px-6 h-12 bg-container shrink-0 mb-4'],
    ['page-content',  'flex-1 overflow-y-auto p-5'],

    // ── Decorative ──
    ['section-dot',    'w-1 h-4 rounded-full shrink-0 bg-primary'],
    ['header-accent',  'w-1 h-5 rounded-full shrink-0 bg-primary'],

    // ── Cards ──
    ['card-interactive', 'rounded-card bg-white shadow-sm hover:-translate-y-0.5 hover:shadow-card-hover transition-all duration-200 cursor-pointer'],

    // ── Border radius semantic tokens ──
    ['rounded-card',  'rounded-12px'],
    ['rounded-btn',   'rounded-8px'],
    ['rounded-tag',   'rounded-6px'],

    // ── Scrollbar ──
    ['thin-scrollbar', 'scrollbar-thin scrollbar-thumb-rounded scrollbar-track-transparent'],
  ],

  theme: {
    colors: {
      primary:     'var(--color-primary)',
      'primary-bg':'var(--color-primary-bg)',
      success:     '#52c41a',
      warning:     '#fa8c16',
      danger:      '#ff4d4f',
      purple:      '#722ed1',
      cyan:        '#13c2c2',

      heading:     'var(--color-text-heading)',
      body:        'var(--color-text-body)',
      secondary:   'var(--color-text-secondary)',
      muted:       'var(--color-text-muted)',

      border:      'var(--color-border)',
      container:   'var(--color-bg-container)',
    },

    boxShadow: {
      'card':        '0 1px 2px rgba(0,0,0,0.04)',
      'card-hover':  '0 8px 24px rgba(0,0,0,0.08)',
      'popover':     '0 20px 60px rgba(0,0,0,0.12)',
    },

    borderRadius: {
      '6px':  '6px',
      '8px':  '8px',
      '12px': '12px',
      '16px': '16px',
    },
  },

  presets: [
    presetWind3(),
    presetAttributify(),
    presetIcons(),
    presetTypography(),
    presetWebFonts({ fonts: {} }),
  ],

  transformers: [
    transformerDirectives(),
    transformerVariantGroup(),
  ],
})
