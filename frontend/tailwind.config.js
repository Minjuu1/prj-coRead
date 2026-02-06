/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Agent colors
        instrumental: '#F59E0B',
        critical: '#3B82F6',
        aesthetic: '#A855F7',
      },
    },
  },
  plugins: [],
}
