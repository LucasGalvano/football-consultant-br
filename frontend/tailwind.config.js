/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brasil-green': '#1e3a1f',
        'brasil-yellow': '#ffd700',
        'brasil-white': '#ffffff',
        'brasil-dark': '#0d1b0e',
      },
    },
  },
  plugins: [],
}
