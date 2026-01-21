'use client'

import { Truck, Plus, Search } from 'lucide-react'
import { useState } from 'react'

export default function Cargas() {
  const [showForm, setShowForm] = useState(false)

  const cargas = [
    {
      id: 'CARGA-2026-001',
      origem: 'São Paulo, SP',
      destino: 'Rio de Janeiro, RJ',
      peso: '18.000 kg',
      valor: 'R$ 3.500',
      status: 'Despachada',
    },
    {
      id: 'CARGA-2026-002',
      origem: 'Rio de Janeiro, RJ',
      destino: 'Paraná',
      peso: '12.000 kg',
      valor: 'R$ 2.500',
      status: 'Despachada',
    },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-700 to-blue-900 bg-clip-text text-transparent">
            Gerenciamento de Cargas
          </h1>
          <p className="text-slate-600 mt-2">Visualize e gerencie todas as suas cargas</p>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-4 mb-8">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-3 text-slate-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Buscar carga..."
              className="w-full pl-10 pr-4 py-2 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button onClick={() => setShowForm(!showForm)} className="btn-primary flex items-center justify-center gap-2">
            <Plus className="w-5 h-5" />
            Nova Carga
          </button>
        </div>

        {/* Form */}
        {showForm && (
          <div className="card p-8 mb-8 animate-fade-in-up">
            <h2 className="text-2xl font-bold text-slate-900 mb-6">Criar Nova Carga</h2>
            <form className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <input type="text" placeholder="Origem" className="px-4 py-2 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
                <input type="text" placeholder="Destino" className="px-4 py-2 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
                <input type="number" placeholder="Peso (kg)" className="px-4 py-2 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
                <input type="number" placeholder="Valor Frete (R$)" className="px-4 py-2 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div className="flex gap-2">
                <button type="submit" className="btn-primary">Criar Carga</button>
                <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
              </div>
            </form>
          </div>
        )}

        {/* Table */}
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gradient-blue text-white">
                <tr>
                  <th className="px-6 py-4 text-left font-semibold">ID</th>
                  <th className="px-6 py-4 text-left font-semibold">Origem</th>
                  <th className="px-6 py-4 text-left font-semibold">Destino</th>
                  <th className="px-6 py-4 text-left font-semibold">Peso</th>
                  <th className="px-6 py-4 text-left font-semibold">Valor</th>
                  <th className="px-6 py-4 text-left font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-blue-100">
                {cargas.map((carga) => (
                  <tr key={carga.id} className="hover:bg-blue-50 transition-colors">
                    <td className="px-6 py-4 font-semibold text-blue-700">{carga.id}</td>
                    <td className="px-6 py-4 text-slate-700">{carga.origem}</td>
                    <td className="px-6 py-4 text-slate-700">{carga.destino}</td>
                    <td className="px-6 py-4 text-slate-700">{carga.peso}</td>
                    <td className="px-6 py-4 font-semibold text-slate-900">{carga.valor}</td>
                    <td className="px-6 py-4">
                      <span className="badge-approved">{carga.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
