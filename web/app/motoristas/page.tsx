'use client'

import { Users, Search } from 'lucide-react'

export default function Motoristas() {
  const motoristas = [
    {
      id: 1,
      nome: 'Maria Santos',
      placa: 'XYZ-5678',
      tipo: 'Carreta',
      status: 'Online',
      sla: '95%',
      dias_cadastro: 120,
    },
    {
      id: 2,
      nome: 'Leonardo Silva',
      placa: 'MNO-9999',
      tipo: 'Truck',
      status: 'Online',
      sla: '72%',
      dias_cadastro: 18,
    },
    {
      id: 3,
      nome: 'Marcos Costa',
      placa: 'STU-3579',
      tipo: 'Carreta',
      status: 'Offline',
      sla: '88%',
      dias_cadastro: 85,
    },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-700 to-blue-900 bg-clip-text text-transparent">
            Rede de Motoristas
          </h1>
          <p className="text-slate-600 mt-2">Gerencie seus motoristas e veja o desempenho em tempo real</p>
        </div>

        {/* Search */}
        <div className="mb-8">
          <div className="relative">
            <Search className="absolute left-3 top-3 text-slate-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Buscar motorista..."
              className="w-full pl-10 pr-4 py-2 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {motoristas.map((motorista) => (
            <div key={motorista.id} className="card p-6 card-hover">
              <div className="flex items-start justify-between mb-4">
                <div className="bg-gradient-blue text-white p-3 rounded-lg">
                  <Users className="w-6 h-6" />
                </div>
                <span className={`text-xs font-bold px-3 py-1 rounded-full ${
                  motorista.status === 'Online'
                    ? 'bg-green-100 text-green-700'
                    : 'bg-slate-200 text-slate-700'
                }`}>
                  {motorista.status}
                </span>
              </div>

              <h3 className="text-xl font-bold text-slate-900 mb-1">{motorista.nome}</h3>
              <p className="text-blue-600 font-semibold mb-4">{motorista.placa}</p>

              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-600">Tipo de Frota</span>
                  <span className="font-semibold text-slate-900">{motorista.tipo}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">SLA Performance</span>
                  <span className="font-semibold text-slate-900">{motorista.sla}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">Dias Cadastro</span>
                  <span className="font-semibold text-slate-900">{motorista.dias_cadastro}</span>
                </div>
              </div>

              <button className="btn-primary w-full mt-4">Ver Detalhes</button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
