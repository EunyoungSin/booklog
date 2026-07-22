import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // /mnt/c (WSL의 Windows 드라이브 마운트)에서는 inotify 파일 변경 알림이
    // 제대로 전달되지 않아 HMR이 멈추는 경우가 있어 폴링 방식으로 강제 감시한다.
    watch: {
      usePolling: true,
      interval: 300,
    },
  },
})
