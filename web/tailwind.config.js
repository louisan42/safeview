/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        sv: {
          paper: '#f7f4ee',
          'paper-2': '#efebe3',
          ink: '#292524',
          muted: '#78716c',
          accent: '#2563eb',
          'accent-strong': '#1d4ed8',
          'accent-soft': '#dbeafe',
          'on-accent': '#ffffff',
          'crime-high': '#e11d48',
          warn: '#dc2626',
          'warn-soft': '#fee2e2',
          better: '#2563eb',
          'better-soft': '#dbeafe',
        },
        accent: '#2563eb',
      },
      fontFamily: {
        sans: ['Nunito', 'sans-serif'],
        display: ['Nunito', 'sans-serif'],
        mono: ['Nunito', 'sans-serif'],
      },
      boxShadow: {
        paper: '0 10px 28px rgba(41, 37, 36, 0.08)',
      },
    },
  },
  plugins: [],
}
