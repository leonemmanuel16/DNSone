import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#0a3d62",
          light: "#3d7faf",
          accent: "#d35400",
        },
      },
    },
  },
  plugins: [],
};

export default config;
