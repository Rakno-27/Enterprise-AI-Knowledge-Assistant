/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: "#0a0d14",
          secondary: "#121824",
          tertiary: "#1a2234",
          glass: "rgba(22, 30, 46, 0.75)",
        },
        border: {
          subtle: "rgba(255, 255, 255, 0.08)",
          highlight: "rgba(99, 102, 241, 0.3)",
        },
        text: {
          primary: "#f8fafc",
          secondary: "#94a3b8",
          muted: "#64748b",
        },
        accent: {
          primary: "#6366f1",
          hover: "#4f46e5",
          emerald: "#10b981",
        }
      },
      borderRadius: {
        sm: "8px",
        md: "12px",
        lg: "16px",
      },
      boxShadow: {
        glow: "0 0 25px rgba(99, 102, 241, 0.25)",
        card: "0 8px 32px rgba(0, 0, 0, 0.37)",
      }
    },
  },
  plugins: [],
}
