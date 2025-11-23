/** @type {import('tailwindcss').Config} */
module.exports = {
  // Abilita dark mode basato sulla classe 'dark' nell'elemento HTML
  darkMode: 'class',
  // CONFIGURAZIONE CRITICA: Indica a Tailwind dove trovare i tuoi file sorgente
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './pages/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
    './hooks/**/*.{js,ts,jsx,tsx}',
    './lib/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      // Custom Indigo palette for Light/Dark mode with WCAG AA compliance
      colors: {
        indigo: {
          // Lightest - backgrounds
          50: '#EEF2FF',
          100: '#E0E7FF',
          // Medium light - secondary elements
          200: '#C7D2FE',
          300: '#A5B4FC',
          // Medium - primary interactive elements
          400: '#818CF8',
          500: '#6366F1',
          600: '#4F46E5',
          // Dark - text and emphasis
          700: '#4338CA',
          800: '#3730A3',
          900: '#312E81',
          950: '#1e1b4b',  // Darkest for dark mode backgrounds
        },
      },
      // Typography scale for mobile-first design
      fontSize: {
        'xs': ['0.875rem', { lineHeight: '1.4' }],      // 14px - small text
        'sm': ['0.9375rem', { lineHeight: '1.5' }],     // 15px - body text small
        'base': ['1rem', { lineHeight: '1.5' }],        // 16px - body text
        'lg': ['1.125rem', { lineHeight: '1.5' }],      // 18px - large body
        'xl': ['1.25rem', { lineHeight: '1.4' }],       // 20px - H3
        '2xl': ['1.5rem', { lineHeight: '1.4' }],       // 24px - H2
        '3xl': ['1.875rem', { lineHeight: '1.3' }],     // 30px - H1 mobile
        '4xl': ['2.25rem', { lineHeight: '1.25' }],     // 36px - H1 desktop
      },
      // Touch-friendly spacing
      spacing: {
        '11': '2.75rem',  // 44px - minimum touch target
        '13': '3.25rem',  // 52px - comfortable touch target
      },
      // Focus ring for accessibility
      ringWidth: {
        '3': '3px',
      },
      ringColor: {
        'focus': '#6366F1', // indigo-500
      },
      // Border radius for modern UI
      borderRadius: {
        'md': '0.5rem',   // 8px
        'lg': '0.75rem',  // 12px
        'xl': '1rem',     // 16px
      }
    },
  },
  plugins: [],
}