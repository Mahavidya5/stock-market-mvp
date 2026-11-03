/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: { gain: "#059669", loss: "#dc2626", brand: { DEFAULT: "#2563eb", dark: "#1d4ed8", soft: "#eff6ff" } },
      fontFamily: { sans: ["Inter", "system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"] },
      boxShadow: { card: "0 1px 2px rgba(15,23,42,.04), 0 1px 3px rgba(15,23,42,.06)" },
    },
  },
  plugins: [],
};
