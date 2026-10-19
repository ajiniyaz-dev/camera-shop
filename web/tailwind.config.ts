import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Surfaces and structure
        navy: "#101D35",
        mist: "#F3F6FC",
        line: "#DCE4F0",
        ink: "#172033",
        mute: "#64748B",
        // Accents
        brand: "#2563EB",
        sky: "#60A5FA",
        teal: "#0D9488",
        // Cart actions — keep the established selection red
        cart: "#FF414D",
        "cart-hover": "#C62828",
      },
      boxShadow: {
        card: "0 1px 2px rgb(16 29 53 / 0.06), 0 8px 24px rgb(16 29 53 / 0.06)",
        lift: "0 4px 16px rgb(37 99 235 / 0.18)",
        cart: "0 2px 8px rgb(255 65 77 / 0.35)",
      },
      transitionTimingFunction: {
        soft: "cubic-bezier(0.22, 1, 0.36, 1)",
      },
    },
  },
  plugins: [],
};

export default config;
