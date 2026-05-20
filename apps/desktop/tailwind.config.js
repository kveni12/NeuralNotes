/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "SF Pro Display",
          "SF Pro Text",
          "Inter",
          "sans-serif"
        ]
      },
      colors: {
        space: {
          950: "#03040a",
          900: "#070914",
          800: "#0d1122"
        },
        neural: {
          cyan: "#7de3ff",
          mint: "#8affc1",
          amber: "#ffd47a",
          rose: "#ff7aaa",
          violet: "#b79cff"
        }
      },
      boxShadow: {
        glow: "0 0 34px rgba(125, 227, 255, 0.28)",
        panel: "0 18px 80px rgba(0, 0, 0, 0.46)"
      }
    }
  },
  plugins: []
};
