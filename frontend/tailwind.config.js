/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: '#131313',
          dim: '#131313',
          bright: '#393939',
          container: {
            DEFAULT: '#201F1F',
            low: '#1C1B1B',
            high: '#2A2A2A',
            highest: '#353534',
            lowest: '#0E0E0E',
          },
          variant: '#353534',
        },
        primary: {
          DEFAULT: '#A3C9FF',
          container: '#00D09C',
        },
        onSurface: {
          DEFAULT: '#E5E2E1',
          variant: '#C0C7D4',
        },
        outline: {
          DEFAULT: '#8A919E',
          variant: '#404752',
        },
        positive: '#00D09C',
        negative: '#E50914',
        engagement: '#00D09C',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      animation: {
        'spin-slow': 'spin 1s linear infinite',
      },
    },
  },
  plugins: [],
}
