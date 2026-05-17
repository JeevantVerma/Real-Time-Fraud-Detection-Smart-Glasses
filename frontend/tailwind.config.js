/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ["\"Space Grotesk\"", "ui-sans-serif", "system-ui"],
        mono: ["\"JetBrains Mono\"", "ui-monospace", "SFMono-Regular"],
      },
      colors: {
        ink: "#0b0f1a",
        inkSoft: "#11182a",
      },
      boxShadow: {
        glow: "0 0 30px rgba(56, 189, 248, 0.25)",
      },
    },
  },
  plugins: [],
}