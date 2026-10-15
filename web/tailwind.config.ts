import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: "#071A35",
        brand: "#1769AA",
        teal: "#20B8A5",
        mist: "#F2F6FA",
      },
    },
  },
  plugins: [],
};

export default config;
