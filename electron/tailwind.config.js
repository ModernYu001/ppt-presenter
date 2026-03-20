export default {
  content: ['./index.html', './src/renderer/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#07111f',
        panel: '#0f172a',
        panel2: '#111827',
        line: '#243245',
        accent: '#3b82f6',
        accent2: '#8b5cf6'
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(59,130,246,0.08), 0 20px 50px rgba(2,6,23,0.45)',
      }
    },
  },
  plugins: [],
};
