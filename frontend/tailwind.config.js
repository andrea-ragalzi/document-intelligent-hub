/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./hooks/**/*.{js,ts,jsx,tsx}",
    "./lib/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "rgb(var(--color-canvas) / <alpha-value>)",
        raised: "rgb(var(--color-raised) / <alpha-value>)",
        surface: "rgb(var(--color-surface) / <alpha-value>)",
        "surface-hover": "rgb(var(--color-surface-hover) / <alpha-value>)",
        ink: "rgb(var(--color-ink) / <alpha-value>)",
        muted: "rgb(var(--color-muted) / <alpha-value>)",
        quiet: "rgb(var(--color-quiet) / <alpha-value>)",
        line: "rgb(var(--color-line) / <alpha-value>)",
        accent: "rgb(var(--color-accent) / <alpha-value>)",
        "accent-hover": "rgb(var(--color-accent-hover) / <alpha-value>)",
        "on-accent": "rgb(var(--color-on-accent) / <alpha-value>)",
        focus: "rgb(var(--color-focus) / <alpha-value>)",
        danger: "rgb(var(--color-danger) / <alpha-value>)",
        warning: "rgb(var(--color-warning) / <alpha-value>)",
        success: "rgb(var(--color-success) / <alpha-value>)",
      },
      fontSize: {
        xs: ["0.875rem", { lineHeight: "1.4" }], // 14px - small text
        sm: ["0.9375rem", { lineHeight: "1.5" }], // 15px - body text small
        base: ["1rem", { lineHeight: "1.5" }], // 16px - body text
        lg: ["1.125rem", { lineHeight: "1.5" }], // 18px - large body
        xl: ["1.25rem", { lineHeight: "1.4" }], // 20px - H3
        "2xl": ["1.5rem", { lineHeight: "1.4" }], // 24px - H2
        "3xl": ["1.875rem", { lineHeight: "1.3" }], // 30px - H1 mobile
        "4xl": ["2.25rem", { lineHeight: "1.25" }], // 36px - H1 desktop
      },
      spacing: {
        11: "2.75rem",
        13: "3.25rem",
      },
      ringWidth: {
        3: "3px",
      },
      ringColor: {
        focus: "rgb(var(--color-focus) / <alpha-value>)",
      },
      borderRadius: {
        md: "0.5rem",
        lg: "0.75rem",
        xl: "1rem",
      },
    },
  },
  plugins: [],
};
