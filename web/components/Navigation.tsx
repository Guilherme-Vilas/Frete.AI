'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Truck, BarChart3, Users, History, Menu, X } from 'lucide-react'
import { useState } from 'react'

export default function Navigation() {
  const [isOpen, setIsOpen] = useState(false)
  const pathname = usePathname()

  const links = [
    { href: '/', label: 'Dashboard', icon: BarChart3 },
    { href: '/cargas', label: 'Cargas', icon: Truck },
    { href: '/motoristas', label: 'Motoristas', icon: Users },
    { href: '/historico', label: 'Histórico', icon: History },
  ]

  return (
    <nav className="bg-gradient-blue text-white shadow-2xl sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 group">
            <div className="bg-white p-2 rounded-lg group-hover:scale-110 transition-transform">
              <Truck className="text-blue-700 w-6 h-6" />
            </div>
            <span className="text-xl font-bold hidden sm:inline">Frete.ai</span>
          </Link>

          {/* Desktop Menu */}
          <div className="hidden md:flex items-center gap-1">
            {links.map((link) => {
              const isActive = pathname === link.href
              const Icon = link.icon
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all duration-200 ${
                    isActive
                      ? 'bg-white text-blue-700 font-semibold'
                      : 'hover:bg-blue-600 text-white'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {link.label}
                </Link>
              )
            })}
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden p-2 hover:bg-blue-600 rounded-lg transition-colors"
            onClick={() => setIsOpen(!isOpen)}
          >
            {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {isOpen && (
          <div className="md:hidden pb-4 space-y-2">
            {links.map((link) => {
              const isActive = pathname === link.href
              const Icon = link.icon
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`flex items-center gap-2 px-4 py-3 rounded-lg transition-all ${
                    isActive
                      ? 'bg-white text-blue-700 font-semibold'
                      : 'hover:bg-blue-600'
                  }`}
                  onClick={() => setIsOpen(false)}
                >
                  <Icon className="w-4 h-4" />
                  {link.label}
                </Link>
              )
            })}
          </div>
        )}
      </div>
    </nav>
  )
}
