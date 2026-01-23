'use client'

import { X } from 'lucide-react'
import { useState } from 'react'
import AnalysisModal from './AnalysisModal'

interface CargaFormModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function CargaFormModal({ isOpen, onClose }: CargaFormModalProps) {
  const [formData, setFormData] = useState({
    origem: '',
    destino: '',
    peso: '',
    valor: '',
  })
  const [showAnalysis, setShowAnalysis] = useState(false)
  const [cargaParaAnalisar, setCargaParaAnalisar] = useState<{
    origem: string
    destino: string
    peso: number
    valor: number
  } | null>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.origem || !formData.destino || !formData.peso || !formData.valor) {
      alert('Preencha todos os campos')
      return
    }

    setCargaParaAnalisar({
      origem: formData.origem,
      destino: formData.destino,
      peso: parseFloat(formData.peso),
      valor: parseFloat(formData.valor),
    })
    setShowAnalysis(true)
  }

  const handleClose = () => {
    setFormData({ origem: '', destino: '', peso: '', valor: '' })
    setShowAnalysis(false)
    setCargaParaAnalisar(null)
    onClose()
  }

  if (!isOpen) return null

  return (
    <>
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-2xl max-w-lg w-full">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6 flex justify-between items-center border-b border-blue-800">
            <h2 className="text-2xl font-bold">Criar Nova Carga</h2>
            <button
              onClick={handleClose}
              className="hover:bg-blue-700 p-2 rounded-lg transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-8 space-y-4">
            <div>
              <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                Origem
              </label>
              <input
                type="text"
                placeholder="ex: São Paulo, SP"
                value={formData.origem}
                onChange={(e) => setFormData({ ...formData, origem: e.target.value })}
                className="w-full px-4 py-2 border border-blue-200 dark:border-blue-700 rounded-lg bg-white dark:bg-slate-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                Destino
              </label>
              <input
                type="text"
                placeholder="ex: Rio de Janeiro, RJ"
                value={formData.destino}
                onChange={(e) => setFormData({ ...formData, destino: e.target.value })}
                className="w-full px-4 py-2 border border-blue-200 dark:border-blue-700 rounded-lg bg-white dark:bg-slate-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                  Peso (kg)
                </label>
                <input
                  type="number"
                  placeholder="ex: 18000"
                  value={formData.peso}
                  onChange={(e) => setFormData({ ...formData, peso: e.target.value })}
                  className="w-full px-4 py-2 border border-blue-200 dark:border-blue-700 rounded-lg bg-white dark:bg-slate-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                  Valor (R$)
                </label>
                <input
                  type="number"
                  placeholder="ex: 3500"
                  value={formData.valor}
                  onChange={(e) => setFormData({ ...formData, valor: e.target.value })}
                  className="w-full px-4 py-2 border border-blue-200 dark:border-blue-700 rounded-lg bg-white dark:bg-slate-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-4">
              <button
                type="submit"
                className="flex-1 px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold rounded-lg transition-colors"
              >
                🚀 Analisar Carga
              </button>
              <button
                type="button"
                onClick={handleClose}
                className="flex-1 px-6 py-3 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 font-semibold rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
              >
                Cancelar
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Analysis Modal */}
      <AnalysisModal
        isOpen={showAnalysis}
        onClose={() => {
          setShowAnalysis(false)
          handleClose()
        }}
        cargaData={cargaParaAnalisar || { origem: '', destino: '', peso: 0, valor: 0 }}
      />
    </>
  )
}
