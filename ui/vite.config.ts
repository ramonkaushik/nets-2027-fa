import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
  // VITE_API_URL is set at build time on Vercel to point to the Railway API
  define: {
    __API_BASE__: JSON.stringify(process.env.VITE_API_URL ?? ''),
  },
})
