'use client'

import { TrendingUp, Truck, Users, CheckCircle } from 'lucide-react'
import StatCard from './StatCard'
import DispatchCard from './DispatchCard'

export default function Dashboard() {
  // Mock data
  const stats: Array<{ title: string; value: string; icon: typeof Truck; color: 'blue' | 'green' | 'purple' | 'emerald'; change: string }> = [
    { title: 'Despachos Hoje', value: '24', icon: Truck, color: 'blue', change: '+12% vs ontem' },
    { title: 'Taxa de Sucesso', value: '96.8%', icon: CheckCircle, color: 'green', change: '+2.3%' },
    { title: 'Motoristas Ativos', value: '156', icon: Users, color: 'purple', change: '+8 esta semana' },
    { title: 'Frete Processado', value: 'R$ 45.2K', icon: TrendingUp, color: 'emerald', change: '+18% vs semana' },
  ]

  const recentDispatches: Array<{
    id: string
    origin: string
    destination: string
    driver: string
    status: 'approved' | 'rejected' | 'pending'
    value: string
    timestamp: string
    margin: string
  }> = [
    {
      id: 'CARGA-2026-001',
      origin: 'São Paulo, SP',
      destination: 'Rio de Janeiro, RJ',
      driver: 'Maria Santos',
      status: 'approved',
      value: 'R$ 3.500',
      timestamp: '2 min atrás',
      margin: '90.6%',
    },
    {
      id: 'CARGA-2026-002',
      origin: 'Rio de Janeiro, RJ',
      destination: 'Paraná',
      driver: 'Leonardo Silva',
      status: 'approved',
      value: 'R$ 2.500',
      timestamp: '5 min atrás',
      margin: '96.7%',
    },
    {
      id: 'CARGA-2026-003',
      origin: 'Curitiba, PR',
      destination: 'Porto Alegre, RS',
      driver: 'Fallback: Marcos Costa',
      status: 'rejected',
      value: 'R$ 2.800',
      timestamp: '8 min atrás',
      margin: '0%',
    },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-950 dark:to-blue-950 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="animate-fade-in-up">
          <h1 className="text-4xl sm:text-5xl font-bold bg-gradient-to-r from-blue-700 to-blue-900 dark:from-blue-400 dark:to-blue-600 bg-clip-text text-transparent">
            Dashboard de Despachos
          </h1>
          <p className="text-slate-600 dark:text-slate-300 mt-2">Gerenciamento inteligente de cargas em tempo real</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, i) => (
            <div key={i} style={{ animationDelay: `${i * 100}ms` }} className="animate-fade-in-up">
              <StatCard {...stat} />
            </div>
          ))}
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Recent Dispatches */}
          <div className="lg:col-span-2 animate-fade-in-up">
            <div className="bg-white dark:bg-slate-800 p-6 rounded-lg shadow-md border border-blue-200 dark:border-blue-700">
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6 flex items-center gap-2">
                <Truck className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                Despachos Recentes
              </h2>
              <div className="space-y-4">
                {recentDispatches.map((dispatch) => (
                  <DispatchCard key={dispatch.id} dispatch={dispatch} />
                ))}
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="animate-fade-in-up space-y-6">
            <div className="bg-white dark:bg-slate-800 p-6 rounded-lg shadow-md border border-blue-200 dark:border-blue-700">
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Ações Rápidas</h3>
              <div className="space-y-3">
                <button className="w-full px-6 py-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold rounded-lg transition-all">
                  + Nova Carga
                </button>
                <button className="w-full px-6 py-2 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 font-semibold rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-all">
                  Ver Motoristas
                </button>
              </div>
            </div>

            {/* Performance Summary */}
            <div className="bg-white dark:bg-slate-800 p-6 rounded-lg shadow-md border border-blue-200 dark:border-blue-700">
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Performance</h3>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-sm mb-1 text-slate-700 dark:text-slate-300">
                    <span>Latência Média</span>
                    <span className="font-bold">0.65ms</span>
                  </div>
                  <div className="w-full bg-blue-100 dark:bg-blue-900 rounded-full h-2">
                    <div className="bg-gradient-to-r from-blue-600 to-blue-700 h-2 rounded-full" style={{ width: '65%' }} />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1 text-slate-700 dark:text-slate-300">
                    <span>Margem Média</span>
                    <span className="font-bold">93.66%</span>
                  </div>
                  <div className="w-full bg-blue-100 dark:bg-blue-900 rounded-full h-2">
                    <div className="bg-gradient-to-r from-blue-600 to-blue-700 h-2 rounded-full" style={{ width: '93.66%' }} />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
