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
    badge: 'badge-approved',
    text: '✓ Aprovado',
    color: 'text-green-700',
  },
  rejected: {
    badge: 'badge-rejected',
    text: '✗ Rejeitado',
    color: 'text-red-700',
  },
  pending: {
    badge: 'badge-pending',
    text: '⏳ Pendente',
    color: 'text-yellow-700',
  },
}

export default function DispatchCard({ dispatch }: DispatchCardProps) {
  const config = statusConfig[dispatch.status]

  return (
    <div className="border border-blue-100 rounded-lg p-4 hover:border-blue-300 hover:shadow-md transition-all duration-200 bg-white">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Left side */}
        <div className="space-y-3">
          <div className="flex items-start justify-between">
            <div>
              <p className="font-bold text-slate-900">{dispatch.id}</p>
              <div className={statusConfig[dispatch.status].badge}>
                {statusConfig[dispatch.status].text}
              </div>
            </div>
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2 text-slate-600">
              <MapPin className="w-4 h-4 text-blue-600" />
              <span className="text-xs">{dispatch.origin}</span>
            </div>
            <div className="flex items-center gap-2 text-slate-600 ml-6">
              <span className="text-xs">→ {dispatch.destination}</span>
            </div>
          </div>
        </div>

        {/* Right side */}
        <div className="space-y-3">
          <div className="flex items-start justify-between">
            <div className="text-right">
              <p className="font-bold text-blue-700">{dispatch.value}</p>
              <p className="text-xs text-slate-500">Margem: {dispatch.margin}</p>
            </div>
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2 text-slate-600">
              <User className="w-4 h-4 text-blue-600" />
              <span className="text-xs">{dispatch.driver}</span>
            </div>
            <div className="flex items-center gap-2 text-slate-500">
              <Clock className="w-4 h-4 text-blue-400" />
              <span className="text-xs">{dispatch.timestamp}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
