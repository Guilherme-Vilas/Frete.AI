'use client'

import { LucideIcon } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string
  icon: LucideIcon
  color: 'blue' | 'green' | 'purple' | 'emerald'
  change: string
}

const colorMap = {
  blue: 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300',
  green: 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300',
  purple: 'bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300',
  emerald: 'bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300',
}

export default function StatCard({ title, value, icon: Icon, color, change }: StatCardProps) {
  return (
    <div className="bg-white dark:bg-slate-800 p-6 rounded-lg shadow-md border border-blue-200 dark:border-blue-700 hover:shadow-xl dark:hover:shadow-blue-900/20 transition-all duration-300 group">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <p className="text-slate-600 dark:text-slate-400 text-sm font-medium">{title}</p>
          <p className="text-3xl font-bold text-slate-900 dark:text-white mt-2">{value}</p>
          <p className="text-green-600 dark:text-green-400 text-xs mt-2 font-semibold">{change}</p>
        </div>
        <div className={`${colorMap[color]} p-3 rounded-lg group-hover:scale-110 transition-transform`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  )
}
