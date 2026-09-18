import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    // Prioritise .tsx before .ts so JSX-containing utility files resolve correctly
    extensions: ['.tsx', '.ts', '.jsx', '.js', '.json'],
  },
})
