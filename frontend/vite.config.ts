import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';
import { readFileSync, writeFileSync, readdirSync } from 'fs';
import UnoCSS from 'unocss/vite';
import type { Plugin } from 'vite';


const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

function inlineCSSPlugin(): Plugin {
  return {
    name: 'inline-css',
    enforce: 'post',
    closeBundle() {
      const distDir = resolve(__dirname, 'dist');
      const assetsDir = resolve(distDir, 'assets');
      const indexPath = resolve(distDir, 'index.html');

      // Collect all CSS from assets
      let css = '';
      for (const f of readdirSync(assetsDir)) {
        if (f.endsWith('.css')) {
          css += readFileSync(resolve(assetsDir, f), 'utf-8');
        }
      }

      if (!css) return;

      // Modify index.html
      let html = readFileSync(indexPath, 'utf-8');
      html = html.replace(/<link rel="stylesheet"[^>]*>/g, '');
      html = html.replace('</head>', `<style>${css}</style></head>`);
      writeFileSync(indexPath, html, 'utf-8');
    },
  };
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    UnoCSS(),
    react(),
    inlineCSSPlugin(),
  ],
  build: {
    cssCodeSplit: false,
  },
  resolve: {
    alias: [
      {find: /^@\//, replacement: resolve(__dirname, 'src') + '/'},
      {find: '@', replacement: resolve(__dirname, 'src')}
    ]
  }
})
