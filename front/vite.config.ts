import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// In development, /api is forwarded to the FastAPI backend, which serves its routes without that prefix.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: path => path.replace(/^\/api/, ''),
      },
    },
  },
});
