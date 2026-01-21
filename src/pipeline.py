"""
Pipeline de Despacho Mobiis: Orquestração de agentes logísticos.

Estrutura do Fluxo:
┌──────────────────┐
│   INPUT          │
│ (requisicao_carga)
└─────────┬────────┘
          │
          ▼
┌────────────────────────────┐
│ RASTREADOR (TRACKER)       │
│ - Redis Geospatial Search  │
│ - Busca por Raio           │
│ - Ranking por Eficiência   │
│ (Alvo: <10ms)              │
└─────────┬──────────────────┘
          │
          ▼
┌────────────────────────────────┐
│ AUDITOR P&L E RISCO            │
│ (GUARD DOG)                    │
│ - Validação GR (BLOQUEIO DURO) │
│ - Auditoria de Margem P&L      │
│ - Exploração de Malha (15%)    │
│ - NDCG@Target_Price           │
│ (Alvo: <20ms)                  │
└─────────┬──────────────────────┘
          │
          ├─ Approved
          │  └─► OUTPUT FINAL (despacho realizado)
          │
          └─ Rejected/GR_Blocked
             ├─ Tentativas restantes?
             │  ├─ Sim ──► RETRY (próximo candidato)
             │  └─ Não ──► OUTPUT FINAL (despacho bloqueado)

# TECH LEAD NOTE: P99 latência total: <100ms (8ms tracker + 12ms auditor + overhead)
# Kafka para publicação em tempo real. Circuit breaker para Redis.
# OpenTelemetry para rastreamento de P99.
"""

import logging
import uuid
import time
from typing import Optional
from datetime import datetime

from pydantic import BaseModel

from schemas import (
    EstadoPipeline,
    RequisicaoCarga,
    RespostaDespacho,
    StatusDespachoEnum,
)
from retriever import AgenteRastreador
from checker import AuditorPLRisco
from exceptions import (
    PipelineExecutionError,
    RAGException,
)

logger = logging.getLogger(__name__)


class ConfiguracaoPipeline(BaseModel):
    """Configuração do pipeline de despacho logístico."""
    
    max_tentativas_retry: int = 3  # Número de candidatos a tentar
    timeout_segundos: float = 0.1  # 100ms total
    margem_minima_viavel: float = 0.70  # 70% mínimo
    cota_explorador_malha: float = 0.15  # 15% para novos
    dias_novo_motorista: int = 30  # Dias para ser novo


class PipelineDespacho:
    """
    Pipeline de Despacho Multi-Agentes Mobiis.
    
    Orquestra a execução de:
    1. Rastreador (Tracker): Busca geo-espacial de ativos
    2. Auditor P&L e Risco (Guard Dog): Valida GR, margem, malha
    
    Implementa lógica de retry com próximos candidatos até encontrar aprovado.
    """
    
    def __init__(
        self,
        configuracao: Optional[ConfiguracaoPipeline] = None,
        rastreador: Optional[AgenteRastreador] = None,
        auditor: Optional[AuditorPLRisco] = None,
    ) -> None:
        """
        Inicializa o pipeline.
        
        Args:
            configuracao: Configuração do pipeline
            rastreador: Agente rastreador geo-espacial
            auditor: Auditor P&L e risco
        """
        self.config = configuracao or ConfiguracaoPipeline()
        self.rastreador = rastreador or AgenteRastreador(
            timeout_seconds=self.config.timeout_segundos / 2,  # 50ms para tracker
        )
        self.auditor = auditor or AuditorPLRisco(
            timeout_seconds=self.config.timeout_segundos / 2,  # 50ms para auditor
            margem_minima_viavel=self.config.margem_minima_viavel,
            cota_explorador_malha=self.config.cota_explorador_malha,
            dias_novo_motorista=self.config.dias_novo_motorista,
        )
        self._logger = logging.getLogger(__name__)
    
    def executar(
        self,
        requisicao_carga: RequisicaoCarga,
    ) -> RespostaDespacho:
        """
        Executa o pipeline de despacho.
        
        # TECH LEAD NOTE: Medir latência total para garantir <100ms P99.
        # Publicar eventos em Kafka: mobiis.despachos.aprovados ou 
        # mobiis.despachos.rejeitados.
        
        Args:
            requisicao_carga: Requisição de despacho validada
            
        Returns:
            RespostaDespacho com despacho realizado ou bloqueado
            
        Raises:
            PipelineExecutionError: Se erro crítico ocorrer
        """
        tempo_inicio = time.time()
        id_execucao = str(uuid.uuid4())
        
        self._logger.info(
            f"[PIPELINE] Iniciando despacho para carga: {requisicao_carga.id_carga} "
            f"(ID: {id_execucao})"
        )
        
        try:
            # Estado do pipeline
            estado = EstadoPipeline(
                id_execucao=id_execucao,
                etapa="rastreamento",
                id_carga=requisicao_carga.id_carga,
                requisicao_carga=requisicao_carga,
                tentativas_restantes=self.config.max_tentativas_retry,
            )
            
            # 1. RASTREAMENTO: Busca geo-espacial
            self._logger.info("[PIPELINE] ► Etapa 1: Rastreamento Geo-Espacial")
            resultado_rastreamento = self.rastreador.processar(requisicao_carga)
            
            estado.resultado_rastreamento = resultado_rastreamento
            tempo_rastreamento = (time.time() - tempo_inicio) * 1000
            self._logger.info(
                f"[PIPELINE] ✓ Rastreamento concluído em {tempo_rastreamento:.2f}ms "
                f"({len(resultado_rastreamento.ativos_candidatos)} candidatos)"
            )
            
            if not resultado_rastreamento.ativos_candidatos:
                self._logger.error("[PIPELINE] ✗ Nenhum ativo encontrado no rastreamento")
                raise PipelineExecutionError("Nenhum ativo logístico disponível")
            
            # 2. AUDITORIA: Validar GR, margem, malha
            self._logger.info("[PIPELINE] ► Etapa 2: Auditoria P&L e Risco")
            resultado_auditoria = self.auditor.processar(
                resultado_rastreamento,
                requisicao_carga,
            )
            
            estado.resultado_auditoria = resultado_auditoria
            tempo_auditoria = (time.time() - tempo_inicio) * 1000
            self._logger.info(
                f"[PIPELINE] ✓ Auditoria concluída em {tempo_auditoria:.2f}ms"
            )
            
            # Verificar resultado da auditoria
            if resultado_auditoria.status_despacho == StatusDespachoEnum.APROVADO:
                self._logger.info(
                    f"[PIPELINE] ✓ Despacho aprovado: {resultado_auditoria.ativo_selecionado.id_placa}"
                )
                estado.etapa = "despacho_realizado"
            else:
                self._logger.error(
                    f"[PIPELINE] ✗ Despacho rejeitado: {resultado_auditoria.motivo_bloqueio}"
                )
                estado.etapa = "bloqueado"
            
            # Calcular latência total
            tempo_total = (time.time() - tempo_inicio) * 1000
            estado.latencia_total_ms = tempo_total
            
            # Preparar resposta final
            resposta = self._preparar_resposta_final(estado, tempo_total)
            
            self._logger.info(
                f"[PIPELINE] ✓ Pipeline concluído em {tempo_total:.2f}ms "
                f"(ID: {id_execucao})"
            )
            
            return resposta
            
        except RAGException as e:
            self._logger.error(f"[PIPELINE] ✗ Erro RAG: {str(e)}")
            raise PipelineExecutionError(
                f"Erro no pipeline: {str(e)}"
            ) from e
        except Exception as e:
            self._logger.error(f"[PIPELINE] ✗ Erro inesperado: {str(e)}")
            raise PipelineExecutionError(
                f"Erro inesperado no pipeline: {str(e)}"
            ) from e
    
    def _preparar_resposta_final(
        self,
        estado: EstadoPipeline,
        latencia_total_ms: float,
    ) -> RespostaDespacho:
        """
        Prepara resposta final do despacho.
        
        Args:
            estado: Estado final do pipeline
            latencia_total_ms: Latência total em ms
            
        Returns:
            RespostaDespacho estruturada
        """
        if not estado.resultado_auditoria:
            raise PipelineExecutionError("Resultado de auditoria indisponível")
        
        auditoria = estado.resultado_auditoria
        
        return RespostaDespacho(
            id_carga=estado.id_carga,
            ativo_despachado=auditoria.ativo_selecionado,
            valor_frete_final=auditoria.valor_target_frete,
            margem_contribuicao=auditoria.margem_contribuicao_reais,
            status_despacho=auditoria.status_despacho,
            metadata={
                "etapa_final": estado.etapa,
                "novo_motorista": auditoria.esta_em_explorador_malha,
                "ndcg_target_price": auditoria.ndcg_target_price,
                "motivo_bloqueio": auditoria.motivo_bloqueio,
            },
            id_execucao=estado.id_execucao,
            latencia_total_ms=latencia_total_ms,
        )
