import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In local dev, /api and /images go to the Python service on port 8000.
// In production, Firebase Hosting forwards /api/** to Cloud Run instead.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/images': 'http://localhost:8000',
    },
  },
})
