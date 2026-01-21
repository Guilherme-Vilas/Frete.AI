"use client"
import { Moon, Sun } from 'lucide-react'
import { useEffect, useState } from 'react'

export default function ThemeToggle() {
  const [dark, setDark] = useState(false)

  useEffect(() => {
    if (dark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [dark])

  return (
    <button
      aria-label="Alternar tema"
      className="ml-2 p-2 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900 transition-colors"
      onClick={() => setDark((v) => !v)}
    >
      {dark ? <Sun className="w-5 h-5 text-yellow-400" /> : <Moon className="w-5 h-5 text-blue-700" />}
    </button>
  )
}
