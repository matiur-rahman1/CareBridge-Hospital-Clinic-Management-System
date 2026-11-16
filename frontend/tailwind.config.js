/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#17253D',
        muted: '#718096',
        brand: { 50: '#EAF8F7', 100: '#D2F0ED', 500: '#1D9C98', 600: '#168783', 700: '#126C69' },
        canvas: '#F5F8FA',
      },
      boxShadow: { soft: '0 10px 30px rgba(22, 42, 68, 0.06)' },
      fontFamily: { sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'] },
    },
  },
  plugins: [],
};
