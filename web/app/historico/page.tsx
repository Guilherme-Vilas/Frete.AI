'use client'

import { History, Filter } from 'lucide-react'

export default function Historico() {
  const historico = [
    {
      id: 'CARGA-2026-001',
      motorista: 'Maria Santos',
      status: 'Entregue',
      valor: 'R$ 3.500',
      margem: '90.6%',
      tempo: '2h 15min',
      data: '21/01/2026 14:30',
    },
    {
      id: 'CARGA-2026-002',
      motorista: 'Leonardo Silva',
      status: 'Entregue',
      valor: 'R$ 2.500',
      margem: '96.7%',
      tempo: '3h 45min',
      data: '21/01/2026 10:15',
    },
    {
      id: 'CARGA-2026-003',
      motorista: 'Marcos Costa',
      status: 'Entregue',
      valor: 'R$ 2.800',
      margem: '78.2%',
      tempo: '2h 30min',
      data: '21/01/2026 09:00',
    },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-950 dark:to-blue-950 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-700 to-blue-900 dark:from-blue-400 dark:to-blue-600 bg-clip-text text-transparent">
            Histórico de Despachos
          </h1>
          <p className="text-slate-600 dark:text-slate-300 mt-2">Visualize o histórico completo de operações</p>
        </div>

        {/* Filter */}
        <div className="mb-8">
          <button className="flex items-center gap-2 px-4 py-2 border border-blue-300 dark:border-blue-700 rounded-lg hover:bg-blue-50 dark:hover:bg-slate-800 transition-colors">
            <Filter className="w-4 h-4" />
            Filtrar
          </button>
        </div>

        {/* Timeline */}
        <div className="space-y-6">
          {historico.map((item) => (
            <div key={item.id} className="bg-white dark:bg-slate-800 p-6 rounded-lg shadow-md border border-blue-200 dark:border-blue-700 hover:shadow-lg dark:hover:shadow-blue-900/20 transition-all">
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                <div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 uppercase mb-1">Carga</p>
                  <p className="font-bold text-blue-700 dark:text-blue-400">{item.id}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 uppercase mb-1">Motorista</p>
                  <p className="font-semibold text-slate-900 dark:text-white">{item.motorista}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 uppercase mb-1">Valor</p>
                  <p className="font-semibold text-slate-900 dark:text-white">{item.valor}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 uppercase mb-1">Performance</p>
                  <p className="font-semibold text-green-600 dark:text-green-400">{item.margem}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-500 dark:text-slate-400 uppercase mb-1">Data/Hora</p>
                  <p className="font-semibold text-slate-900 dark:text-white">{item.data}</p>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-blue-100 dark:border-blue-700 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 rounded-full text-sm font-semibold bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200">{item.status}</span>
                  <span className="text-sm text-slate-600 dark:text-slate-400">Tempo: {item.tempo}</span>
                </div>
                <button className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-semibold text-sm">Ver Detalhes →</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
