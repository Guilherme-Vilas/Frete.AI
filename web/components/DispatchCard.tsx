'use client'

import { MapPin, User, Clock } from 'lucide-react'

interface DispatchCardProps {
  dispatch: {
    id: string
    origin: string
    destination: string
    driver: string
    status: 'approved' | 'rejected' | 'pending'
    value: string
    timestamp: string
    margin: string
  }
}

const statusConfig = {
  approved: {
    badge: 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200',
    text: '✓ Aprovado',
    color: 'text-green-700 dark:text-green-400',
  },
  rejected: {
    badge: 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200',
    text: '✗ Rejeitado',
    color: 'text-red-700 dark:text-red-400',
  },
  pending: {
    badge: 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200',
    text: '⏳ Pendente',
    color: 'text-yellow-700 dark:text-yellow-400',
  },
}

export default function DispatchCard({ dispatch }: DispatchCardProps) {
  const config = statusConfig[dispatch.status]

  return (
    <div className="border border-blue-100 dark:border-blue-700 rounded-lg p-4 hover:border-blue-300 dark:hover:border-blue-600 hover:shadow-md dark:hover:shadow-blue-900/20 transition-all duration-200 bg-white dark:bg-slate-700">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Left side */}
        <div className="space-y-3">
          <div className="flex items-start justify-between">
            <div>
              <p className="font-bold text-slate-900 dark:text-white">{dispatch.id}</p>
              <div className={`px-3 py-1 rounded-full text-sm font-semibold ${statusConfig[dispatch.status].badge}`}>
                {statusConfig[dispatch.status].text}
              </div>
            </div>
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
              <MapPin className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              <span className="text-xs">{dispatch.origin}</span>
            </div>
            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300 ml-6">
              <span className="text-xs">→ {dispatch.destination}</span>
            </div>
          </div>
        </div>

        {/* Right side */}
        <div className="space-y-3">
          <div className="flex items-start justify-between">
            <div className="text-right">
              <p className="font-bold text-blue-700 dark:text-blue-400">{dispatch.value}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400">Margem: {dispatch.margin}</p>
            </div>
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
              <User className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              <span className="text-xs">{dispatch.driver}</span>
            </div>
            <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
              <Clock className="w-4 h-4 text-blue-400 dark:text-blue-500" />
              <span className="text-xs">{dispatch.timestamp}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
