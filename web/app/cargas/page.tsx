'use client'

import { Truck, Plus, Search, Trash2 } from 'lucide-react'
import { useState } from 'react'

interface Carga {
  id: string
  origem: string
  destino: string
  peso: string
  valor: string
  status: string
}

export default function Cargas() {
  const [showForm, setShowForm] = useState(false)
  const [cargas, setCargas] = useState<Carga[]>([
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
  ])
  const [formData, setFormData] = useState({
    origem: '',
    destino: '',
    peso: '',
    valor: '',
  })
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(false)

  const handleAddCarga = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.origem || !formData.destino || !formData.peso || !formData.valor) {
      alert('Preencha todos os campos')
      return
    }

    setLoading(true)
    try {
      // Chamar API de análise
      const response = await fetch('http://localhost:8000/cargas/analisar', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          origem: formData.origem,
          destino: formData.destino,
          peso: parseFloat(formData.peso),
          valor: parseFloat(formData.valor),
          tipo_freta: 'Truck',
        }),
      })

      if (!response.ok) {
        throw new Error(`Erro na API: ${response.statusText}`)
      }

      const result = await response.json()

      // Criar carga com os dados retornados
      const newCarga: Carga = {
        id: result.id,
        origem: result.origem,
        destino: result.destino,
        peso: result.peso,
        valor: result.valor,
        status: result.status,
      }

      setCargas([...cargas, newCarga])
      setFormData({ origem: '', destino: '', peso: '', valor: '' })
      setShowForm(false)
      
      // Mostrar resultado
      alert(`✓ Carga analisada!\n\nID: ${result.id}\nStatus: ${result.status}\nMargem: ${result.margem || 'N/A'}`)
    } catch (error) {
      console.error('Erro:', error)
      alert(`✗ Erro ao analisar carga:\n${error instanceof Error ? error.message : 'Erro desconhecido'}`)
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteCarga = (id: string) => {
    setCargas(cargas.filter(c => c.id !== id))
  }

  const filteredCargas = cargas.filter(carga =>
    carga.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    carga.origem.toLowerCase().includes(searchTerm.toLowerCase()) ||
    carga.destino.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-950 dark:to-blue-950 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-700 to-blue-900 dark:from-blue-400 dark:to-blue-600 bg-clip-text text-transparent">
            Gerenciamento de Cargas
          </h1>
          <p className="text-slate-600 dark:text-slate-300 mt-2">Visualize e gerencie todas as suas cargas</p>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-4 mb-8">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-3 text-slate-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Buscar carga..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-blue-200 dark:border-blue-700 rounded-lg bg-white dark:bg-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button 
            onClick={() => setShowForm(!showForm)} 
            className="px-6 py-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-all"
          >
            <Plus className="w-5 h-5" />
            Nova Carga
          </button>
        </div>

        {/* Form */}
        {showForm && (
          <div className="bg-white dark:bg-slate-800 p-8 mb-8 rounded-lg shadow-md border border-blue-200 dark:border-blue-700 animate-fade-in-up">
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">Criar Nova Carga</h2>
            <form onSubmit={handleAddCarga} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <input 
                  type="text" 
                  placeholder="Origem" 
                  value={formData.origem}
                  onChange={(e) => setFormData({...formData, origem: e.target.value})}
                  className="px-4 py-2 border border-blue-200 dark:border-blue-700 rounded-lg bg-white dark:bg-slate-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500" 
                />
                <input 
                  type="text" 
                  placeholder="Destino" 
                  value={formData.destino}
                  onChange={(e) => setFormData({...formData, destino: e.target.value})}
                  className="px-4 py-2 border border-blue-200 dark:border-blue-700 rounded-lg bg-white dark:bg-slate-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500" 
                />
                <input 
                  type="number" 
                  placeholder="Peso (kg)" 
                  value={formData.peso}
                  onChange={(e) => setFormData({...formData, peso: e.target.value})}
                  className="px-4 py-2 border border-blue-200 dark:border-blue-700 rounded-lg bg-white dark:bg-slate-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500" 
                />
                <input 
                  type="number" 
                  placeholder="Valor Frete (R$)" 
                  value={formData.valor}
                  onChange={(e) => setFormData({...formData, valor: e.target.value})}
                  className="px-4 py-2 border border-blue-200 dark:border-blue-700 rounded-lg bg-white dark:bg-slate-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500" 
                />
              </div>
              <div className="flex gap-2">
                <button 
                  type="submit" 
                  disabled={loading}
                  className="px-6 py-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:from-blue-400 disabled:to-blue-500 text-white font-semibold rounded-lg transition-all disabled:cursor-not-allowed"
                >
                  {loading ? '⏳ Analisando...' : 'Criar Carga'}
                </button>
                <button 
                  type="button" 
                  onClick={() => setShowForm(false)} 
                  className="px-6 py-2 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 font-semibold rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-all"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Table */}
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-md border border-blue-200 dark:border-blue-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gradient-to-r from-blue-600 to-blue-700 text-white">
                <tr>
                  <th className="px-6 py-4 text-left font-semibold">ID</th>
                  <th className="px-6 py-4 text-left font-semibold">Origem</th>
                  <th className="px-6 py-4 text-left font-semibold">Destino</th>
                  <th className="px-6 py-4 text-left font-semibold">Peso</th>
                  <th className="px-6 py-4 text-left font-semibold">Valor</th>
                  <th className="px-6 py-4 text-left font-semibold">Status</th>
                  <th className="px-6 py-4 text-left font-semibold">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-blue-100 dark:divide-blue-700">
                {filteredCargas.map((carga) => (
                  <tr key={carga.id} className="hover:bg-blue-50 dark:hover:bg-slate-700 transition-colors">
                    <td className="px-6 py-4 font-semibold text-blue-700 dark:text-blue-400">{carga.id}</td>
                    <td className="px-6 py-4 text-slate-700 dark:text-slate-300">{carga.origem}</td>
                    <td className="px-6 py-4 text-slate-700 dark:text-slate-300">{carga.destino}</td>
                    <td className="px-6 py-4 text-slate-700 dark:text-slate-300">{carga.peso}</td>
                    <td className="px-6 py-4 font-semibold text-slate-900 dark:text-white">{carga.valor}</td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                        carga.status === 'Despachada' 
                          ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                          : 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200'
                      }`}>
                        {carga.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => handleDeleteCarga(carga.id)}
                        className="p-2 hover:bg-red-100 dark:hover:bg-red-900 rounded-lg text-red-600 dark:text-red-400 transition-colors"
                        title="Deletar carga"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filteredCargas.length === 0 && (
              <div className="px-6 py-8 text-center text-slate-500 dark:text-slate-400">
                Nenhuma carga encontrada
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
