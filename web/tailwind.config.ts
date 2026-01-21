import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        blue: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c3d66',
        },
      },
      backgroundImage: {
        'gradient-blue': 'linear-gradient(135deg, #0284c7 0%, #0369a1 50%, #0c3d66 100%)',
        'gradient-blue-light': 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
      },
    },
  },
  plugins: [],
}

export default config
