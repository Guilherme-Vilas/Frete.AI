'use client'

import { X, Loader, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { useState, useEffect } from 'react'

interface AnalysisModalProps {
  isOpen: boolean
  onClose: () => void
  cargaData: {
    origem: string
    destino: string
    peso: number
    valor: number
  }
}

interface AnalysisResult {
  id: string
  status: string
  margem: string
  motorista_recomendado?: string
  analise?: {
    decisao: string
    tempo_processamento_ms: number
    motorista_recomendado?: string
  }
}

export default function AnalysisModal({ isOpen, onClose, cargaData }: AnalysisModalProps) {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen && cargaData) {
      analisarCarga()
    }
  }, [isOpen, cargaData])

  const analisarCarga = async () => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch('http://localhost:8000/cargas/analisar', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          origem: cargaData.origem,
          destino: cargaData.destino,
          peso: cargaData.peso,
          valor: cargaData.valor,
          tipo_freta: 'Truck',
        }),
      })

      if (!response.ok) {
        throw new Error(`Erro na API: ${response.statusText}`)
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro desconhecido')
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6 flex justify-between items-center border-b border-blue-800">
          <h2 className="text-2xl font-bold">Análise de Carga em Tempo Real</h2>
          <button
            onClick={onClose}
            className="hover:bg-blue-700 p-2 rounded-lg transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-8">
          {/* Loading State */}
          {loading && (
            <div className="flex flex-col items-center justify-center py-12 space-y-4">
              <div className="relative w-16 h-16">
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-blue-700 rounded-full animate-spin" />
                <div className="absolute inset-2 bg-white dark:bg-slate-800 rounded-full" />
                <Loader className="absolute inset-0 m-auto w-8 h-8 text-blue-600 animate-spin" />
              </div>
              <p className="text-lg font-semibold text-slate-700 dark:text-slate-200">
                Analisando carga com IA...
              </p>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Executando pipeline de despacho
              </p>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="space-y-4">
              <div className="bg-red-100 dark:bg-red-900 border border-red-300 dark:border-red-700 rounded-lg p-4 flex gap-3">
                <XCircle className="w-6 h-6 text-red-600 dark:text-red-400 flex-shrink-0" />
                <div>
                  <h3 className="font-bold text-red-800 dark:text-red-200">Erro na Análise</h3>
                  <p className="text-red-700 dark:text-red-300 text-sm mt-1">{error}</p>
                </div>
              </div>
              <button
                onClick={analisarCarga}
                className="w-full px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
              >
                Tentar Novamente
              </button>
            </div>
          )}

          {/* Success State */}
          {result && !loading && !error && (
            <div className="space-y-6">
              {/* Dados da Carga */}
              <div className="bg-slate-50 dark:bg-slate-700 p-4 rounded-lg">
                <h3 className="font-bold text-slate-900 dark:text-white mb-3">Detalhes da Carga</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Origem</p>
                    <p className="font-semibold text-slate-900 dark:text-white">{cargaData.origem}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Destino</p>
                    <p className="font-semibold text-slate-900 dark:text-white">{cargaData.destino}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Peso</p>
                    <p className="font-semibold text-slate-900 dark:text-white">{cargaData.peso} kg</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Valor</p>
                    <p className="font-semibold text-slate-900 dark:text-white">R$ {cargaData.valor.toFixed(2)}</p>
                  </div>
                </div>
              </div>

              {/* Status Decision */}
              <div className={`p-4 rounded-lg border-2 ${
                result.status === 'Aprovada'
                  ? 'bg-green-50 dark:bg-green-900/20 border-green-300 dark:border-green-700'
                  : result.status === 'Rejeitada'
                  ? 'bg-red-50 dark:bg-red-900/20 border-red-300 dark:border-red-700'
                  : 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-300 dark:border-yellow-700'
              }`}>
                <div className="flex items-center gap-3">
                  {result.status === 'Aprovada' ? (
                    <CheckCircle className="w-8 h-8 text-green-600 dark:text-green-400" />
                  ) : result.status === 'Rejeitada' ? (
                    <XCircle className="w-8 h-8 text-red-600 dark:text-red-400" />
                  ) : (
                    <AlertCircle className="w-8 h-8 text-yellow-600 dark:text-yellow-400" />
                  )}
                  <div>
                    <p className="text-sm font-semibold text-slate-600 dark:text-slate-400">Decisão da IA</p>
                    <p className={`text-2xl font-bold ${
                      result.status === 'Aprovada'
                        ? 'text-green-700 dark:text-green-400'
                        : result.status === 'Rejeitada'
                        ? 'text-red-700 dark:text-red-400'
                        : 'text-yellow-700 dark:text-yellow-400'
                    }`}>
                      {result.status}
                    </p>
                  </div>
                </div>
              </div>

              {/* Analysis Results */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg border border-blue-200 dark:border-blue-700">
                  <p className="text-sm text-slate-600 dark:text-slate-400 font-semibold">Margem de Contribuição</p>
                  <p className="text-3xl font-bold text-blue-700 dark:text-blue-400 mt-2">{result.margem}</p>
                </div>
                {result.analise?.tempo_processamento_ms && (
                  <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg border border-purple-200 dark:border-purple-700">
                    <p className="text-sm text-slate-600 dark:text-slate-400 font-semibold">Tempo de Análise</p>
                    <p className="text-3xl font-bold text-purple-700 dark:text-purple-400 mt-2">
                      {result.analise.tempo_processamento_ms}ms
                    </p>
                  </div>
                )}
              </div>

              {/* Recommendations */}
              {result.motorista_recomendado && (
                <div className="bg-emerald-50 dark:bg-emerald-900/20 p-4 rounded-lg border border-emerald-200 dark:border-emerald-700">
                  <p className="text-sm font-semibold text-emerald-700 dark:text-emerald-400 mb-2">🚚 Motorista Recomendado</p>
                  <p className="text-lg font-bold text-slate-900 dark:text-white">{result.motorista_recomendado}</p>
                </div>
              )}

              {/* ID */}
              <div className="bg-slate-100 dark:bg-slate-700 p-3 rounded-lg">
                <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">ID: {result.id}</p>
              </div>

              {/* Actions */}
              <div className="flex gap-3">
                <button
                  onClick={onClose}
                  className="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
                >
                  ✓ Confirmar e Fechar
                </button>
                <button
                  onClick={analisarCarga}
                  className="flex-1 px-6 py-3 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 font-semibold rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                >
                  Analisar Novamente
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
