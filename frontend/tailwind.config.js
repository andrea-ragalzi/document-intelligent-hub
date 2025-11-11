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
      // Estensioni personalizzate del tema, ad esempio:
      colors: {
        // La tua palette personalizzata. Ho aggiunto un colore primario fittizio
        primary: {
          500: '#3b82f6', // Un blu
          600: '#2563eb', // Un blu più scuro
        }
      },
      // Animazioni, Font, ecc.
    },
  },
  plugins: [],
}