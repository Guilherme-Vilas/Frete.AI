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
from typing import Dict, Any, Optional
from datetime import datetime

from schemas import (
    EstadoPipeline,
    RequisicaoCarga,
    RespostaFinal,
    RelevanciaEnum,
    HistoricoUsuario,
)
from retriever import AgenteCandidateGeneration
from checker import AgenteDiversityAuditor
from exceptions import (
    PipelineExecutionError,
    RAGException,
)

logger = logging.getLogger(__name__)


class ConfiguracaoPipeline(BaseModel):
    """Configuração do pipeline de recomendação."""
    
    max_tentativas_retry: int = 2
    timeout_segundos: float = 30.0
    threshold_confianca_checker: float = 0.8
    relevancia_threshold: float = 0.5
    max_candidatos: int = 100


class PipelineRecomendacao:
    """
    Pipeline de Recomendação Multi-Agentes Mobiis.
    
    Orquestra a execução de:
    1. Candidate Generation: Gera candidatos com Content-Based Filtering
    2. Diversity & Ethics Auditor: Valida diversidade e serendipidade
    
    Implementa lógica de retry e fallback seguro.
    """
    
    def __init__(
        self,
        configuracao: Optional[ConfiguracaoPipeline] = None,
        candidate_generator: Optional[AgenteCandidateGeneration] = None,
        diversity_auditor: Optional[AgenteDiversityAuditor] = None,
    ) -> None:
        """
        Inicializa o pipeline.
        
        Args:
            configuracao: Configuração do pipeline
            candidate_generator: Agente de geração de candidatos
            diversity_auditor: Auditor de diversidade
        """
        self.config = configuracao or ConfiguracaoPipeline()
        self.candidate_generator = candidate_generator or AgenteCandidateGeneration(
            timeout_seconds=self.config.timeout_segundos,
            max_candidatos=self.config.max_candidatos,
            relevancia_threshold=self.config.relevancia_threshold,
        )
        self.diversity_auditor = diversity_auditor or AgenteDiversityAuditor(
            threshold_confianca_global=self.config.threshold_confianca_checker,
        )
        self._logger = logging.getLogger(__name__)
    
    def executar(
        self,
        usuario_id: str,
        historico_usuario: Optional[HistoricoUsuario] = None,
        top_k: int = 10,
    ) -> RespostaFinal:
        """
        Executa o pipeline de recomendação.
        
        # TECH LEAD NOTE: Medir latência total para garantir <150ms.
        # Publicar eventos em Kafka: mobiis.recommendations.generated
        # e mobiis.recommendations.audited.
        
        Args:
            usuario_id: ID do usuário
            historico_usuario: Histórico de interações do usuário
            top_k: Número de recomendações solicitadas
            
        Returns:
            RespostaFinal com recomendações aprovadas
            
        Raises:
            PipelineExecutionError: Se erro crítico ocorrer
        """
        tempo_inicio = time.time()
        id_execucao = str(uuid.uuid4())
        
        self._logger.info(
            f"[PIPELINE] Iniciando recomendação para usuário: {usuario_id} "
            f"(ID: {id_execucao})"
        )
        
        try:
            # Estado do pipeline
            estado = EstadoPipeline(
                id_execucao=id_execucao,
                etapa="candidate_generation",
                usuario_id=usuario_id,
                top_k_solicitado=top_k,
                tentativas_restantes=self.config.max_tentativas_retry,
            )
            
            # Loop para retry (em vez de recursão)
            tentativa_atual = 0
            while tentativa_atual <= self.config.max_tentativas_retry:
                tentativa_atual += 1
                
                # 1. CANDIDATE GENERATION
                self._logger.info("[PIPELINE] ► Etapa 1: Candidate Generation")
                resultado_cand_gen = self.candidate_generator.processar(
                    CandidateGenerationInput(
                        usuario_id=usuario_id,
                        historico_usuario=historico_usuario,
                        top_k=top_k,
                    )
                )
                
                estado.resultado_candidate_generation = resultado_cand_gen
                tempo_cand_gen = (time.time() - tempo_inicio) * 1000
                self._logger.info(
                    f"[PIPELINE] ✓ Candidate Generation concluído em {tempo_cand_gen:.2f}ms"
                )
                
                # 2. DIVERSITY & ETHICS AUDIT
                self._logger.info("[PIPELINE] ► Etapa 2: Diversity & Ethics Audit")
                resultado_audit = self.diversity_auditor.processar(resultado_cand_gen)
                
                estado.resultado_diversity_auditor = resultado_audit
                tempo_audit = (time.time() - tempo_inicio) * 1000
                self._logger.info(
                    f"[PIPELINE] ✓ Diversity Audit concluído em {tempo_audit:.2f}ms"
                )
                
                # Verificar se passou na validação
                if resultado_audit.validacao_passou:
                    self._logger.info("[PIPELINE] ✓ Recomendações aprovadas na auditoria")
                    estado.etapa = "completed"
                    break  # Sair do loop se passou
                else:
                    self._logger.warning("[PIPELINE] ✗ Recomendações não passaram na auditoria")
                    # Verificar se há mais tentativas
                    if tentativa_atual <= self.config.max_tentativas_retry:
                        self._logger.info(
                            f"[PIPELINE] ► Retentando... (tentativa {tentativa_atual + 1} de {self.config.max_tentativas_retry + 1})"
                        )
                        estado.historico_tentativas.append({
                            "timestamp": datetime.utcnow().isoformat(),
                            "motivo": resultado_audit.motivo_rejeicao,
                            "ndcg": resultado_audit.ndcg_at_k,
                        })
                        # Continuar o loop para próxima tentativa
                    else:
                        self._logger.error("[PIPELINE] ✗ Máximo de tentativas atingido. Retornando melhor resultado.")
                        estado.etapa = "completed_with_fallback"
                        break  # Sair do loop - sem mais tentativas
            
            # Calcular latência total
            tempo_total = (time.time() - tempo_inicio) * 1000
            estado.latencia_total_ms = tempo_total
            
            # Preparar resposta final
            resposta = self._preparar_resposta_final(estado, tempo_total)
            
            self._logger.info(
                f"[PIPELINE] ✓ Pipeline concluído com sucesso em {tempo_total:.2f}ms "
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
    ) -> RespostaFinal:
        """
        Prepara resposta final para o usuário.
        
        Args:
            estado: Estado final do pipeline
            latencia_total_ms: Latência total em ms
            
        Returns:
            RespostaFinal estruturada
        """
        if not estado.resultado_diversity_auditor:
            # Usar resultado do Candidate Generation como fallback
            produtos = estado.resultado_candidate_generation.candidates
            relevancia = RelevanciaEnum.BAIXA
            ndcg = None
            diversidade = 0.0
            serendipidade = 0.0
        else:
            # Usar resultado da auditoria (preferred)
            produtos = estado.resultado_diversity_auditor.candidates_ajustados
            relevancia = estado.resultado_diversity_auditor.relevancia
            ndcg = estado.resultado_diversity_auditor.ndcg_at_k
            diversidade = estado.resultado_diversity_auditor.diversidade_categorias
            serendipidade = estado.resultado_diversity_auditor.percentual_serendipidade
        
        return RespostaFinal(
            produtos=produtos,
            relevancia=relevancia,
            ndcg_at_k=ndcg,
            diversidade_categorias=diversidade,
            percentual_serendipidade=serendipidade,
            metadata={
                "etapa_final": estado.etapa,
                "tentativas_usadas": self.config.max_tentativas_retry - estado.tentativas_restantes + 1,
                "historico_tentativas": estado.historico_tentativas,
            },
            id_execucao=estado.id_execucao,
            latencia_total_ms=latencia_total_ms,
        )
