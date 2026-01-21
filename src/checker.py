"""
Agente Auditor P&L e Risco (Guard Dog): Validação de despacho logístico.

Este agente implementa a segunda etapa do pipeline de despacho Mobiis, focando em:
- Validação de Gerenciamento de Risco (GR) - BLOQUEIO DURO se vencido
- Auditoria de margem de contribuição (viabilidade P&L)
- Estratégia de exploração de malha (15% para novos motoristas)
- Cálculo de NDCG@Target_Price (aderência ao preço-alvo)
- Rastreamento de latência de auditoria (target <20ms)

# TECH LEAD NOTE: GR vencido = BLOQUEIO IMEDIATO, sem apelo.
# Integrar com Kafka para publicação de eventos de auditoria.
# OpenTelemetry para métricas de P99 latência.
"""

import logging
import time
from typing import List, Optional
from datetime import datetime, date
import math

from schemas import (
    ResultadoRastreamento,
    ResultadoAuditoria,
    AtivoLogistico,
    RequisicaoCarga,
    CriterioValidacaoLogistica,
    StatusDespachoEnum,
)
from exceptions import CheckerError

logger = logging.getLogger(__name__)


class CalculadorMetricasLogistica:
    """
    Calcula métricas de P&L e logística.
    
    Métricas suportadas:
    - Margem de contribuição (P&L)
    - NDCG@Target_Price (aderência ao preço)
    - SLA Score
    """
    
    @staticmethod
    def calcular_margem_contribuicao(
        target_price: float,
        custo_variavel: float,
    ) -> float:
        """
        Calcula margem de contribuição em %.
        
        Fórmula:
        Margem = (Target - CustoVariavel) / Target
        
        Args:
            target_price: Valor alvo do frete
            custo_variavel: Custo variável estimado
            
        Returns:
            Margem em % (0-1)
        """
        if target_price <= 0:
            return 0.0
        
        margem = (target_price - custo_variavel) / target_price
        return max(0.0, min(1.0, margem))
    
    @staticmethod
    def calcular_ndcg_target_price(
        margem_real: float,
        margem_alvo: float = 0.75,
    ) -> float:
        """
        Calcula NDCG customizado para aderência ao target price.
        
        Fórmula:
        relevancia = 1 - |margem_real - margem_alvo| / margem_alvo
        
        Interpreta aderência ao preço-alvo como qualidade do ranking.
        
        Args:
            margem_real: Margem real calculada
            margem_alvo: Margem alvo (padrão: 75%)
            
        Returns:
            Score NDCG customizado (0-1)
        """
        if margem_alvo <= 0:
            return 0.0
        
        desvio = abs(margem_real - margem_alvo) / margem_alvo
        relevancia = max(0.0, 1.0 - desvio)
        
        return relevancia
    
    @staticmethod
    def calcular_custo_variavel_estimado(
        ativo: AtivoLogistico,
        requisicao: RequisicaoCarga,
    ) -> float:
        """
        Estima custo variável da rota.
        
        Componentes:
        - Combustível: custo_km_base × distancia
        - Risco adicional (para novos motoristas): -R$50
        
        Args:
            ativo: Ativo logístico
            requisicao: Requisição de carga
            
        Returns:
            Custo variável estimado em R$
        """
        distancia = ativo.distancia_km or 50  # Default 50km
        
        # Custo base de combustível/operação
        custo_base = ativo.custo_km_base * distancia
        
        # Ajuste de risco para novos motoristas
        dias_cadastro = ativo.dias_cadastro
        if dias_cadastro < 30:
            # Novo motorista: ajuste conservador de -R$50
            custo_risco = -50.0
        else:
            custo_risco = 0.0
        
        custo_total = custo_base + custo_risco
        return max(0.0, custo_total)


class AuditorPLRisco:
    """
    Auditor P&L e Risco (Guard Dog): Responsável pela validação de despachos.
    
    Implementa validações críticas:
    - GR (Gerenciamento de Risco): BLOQUEIO IMEDIATO se vencido
    - Margem viável: mínimo 70% para aprovação
    - Exploração de malha: 15% de alocação para novos motoristas (<30 dias)
    - NDCG@Target_Price: aderência ao preço-alvo
    """
    
    def __init__(
        self,
        timeout_seconds: float = 0.02,  # 20ms para ter margem
        margem_minima_viavel: float = 0.70,
        cota_explorador_malha: float = 0.15,
        dias_novo_motorista: int = 30,
    ) -> None:
        """
        Inicializa auditor.
        
        Args:
            timeout_seconds: Timeout máximo em segundos
            margem_minima_viavel: Margem mínima para aprovação (padrão: 70%)
            cota_explorador_malha: Cota de alocação para novos (padrão: 15%)
            dias_novo_motorista: Dias para ser considerado novo (padrão: 30)
        """
        self.timeout_seconds = timeout_seconds
        self.margem_minima_viavel = margem_minima_viavel
        self.cota_explorador_malha = cota_explorador_malha
        self.dias_novo_motorista = dias_novo_motorista
        self._logger = logging.getLogger(__name__)
        self.calculador = CalculadorMetricasLogistica()
    
    def processar(
        self,
        resultado_rastreamento: ResultadoRastreamento,
        requisicao: RequisicaoCarga,
    ) -> ResultadoAuditoria:
        """
        Processa candidatos e realiza auditoria P&L e risco.
        
        Etapas:
        1. Iterar candidatos em ordem de eficiência
        2. Validar GR (bloqueio imediato se vencido)
        3. Validar margem (>=70% para aprovação)
        4. Validar exploração de malha (15% para novos)
        5. Retornar primeiro aprovado ou rejeitado
        
        Args:
            resultado_rastreamento: Resultado do rastreador
            requisicao: Requisição original
            
        Returns:
            Resultado da auditoria com despacho ou bloqueio
            
        Raises:
            CheckerError: Se houver erro na auditoria
        """
        tempo_inicio = time.time()
        
        try:
            self._logger.info(
                f"[AUDITOR] Auditando candidatos para carga: {requisicao.id_carga}"
            )
            
            if not resultado_rastreamento.ativos_candidatos:
                self._logger.error("[AUDITOR] Nenhum candidato para auditar")
                raise CheckerError("Nenhum ativo candidato disponível")
            
            # Iterar candidatos em ordem de eficiência
            for idx, ativo in enumerate(resultado_rastreamento.ativos_candidatos, 1):
                self._logger.info(f"[AUDITOR] Avaliando candidato {idx}/{len(resultado_rastreamento.ativos_candidatos)}: {ativo.id_placa}")
                
                # 1. Validar GR - BLOQUEIO IMEDIATO
                validacao_gr = self._validar_gr(ativo)
                if not validacao_gr.passou:
                    self._logger.warning(f"[AUDITOR] ❌ GR inválido para {ativo.id_placa}: {validacao_gr.detalhes}")
                    continue  # Próximo candidato
                
                # 2. Validar margem
                custo_variavel = self.calculador.calcular_custo_variavel_estimado(ativo, requisicao)
                margem = self.calculador.calcular_margem_contribuicao(
                    requisicao.target_price_frete,
                    custo_variavel,
                )
                
                validacao_margem = self._validar_margem(margem)
                if not validacao_margem.passou:
                    # Margem insuficiente
                    self._logger.info(f"[AUDITOR] ⚠ Margem insuficiente para {ativo.id_placa}: {margem:.2%}")
                    continue  # Próximo candidato
                
                # 3. Validar exploração de malha
                eh_novo = ativo.dias_cadastro < self.dias_novo_motorista
                validacao_malha = self._validar_exploracao_malha(ativo, eh_novo)
                
                if not validacao_malha.passou:
                    self._logger.info(f"[AUDITOR] ⚠ Cota de malha exaurida para novos motoristas")
                    # Se é novo e a cota acabou, rejeitar e continuar
                    if eh_novo:
                        continue  # Próximo candidato
                
                # 4. Calcular NDCG@Target_Price
                ndcg_target_price = self.calculador.calcular_ndcg_target_price(margem)
                
                # ✓ APROVADO!
                tempo_auditoria = (time.time() - tempo_inicio) * 1000  # em ms
                
                self._logger.info(
                    f"[AUDITOR] ✓ APROVADO: {ativo.id_placa} | "
                    f"Margem: {margem:.2%} | "
                    f"Novo: {eh_novo} | "
                    f"Tempo: {tempo_auditoria:.2f}ms"
                )
                
                criterios = [validacao_gr, validacao_margem, validacao_malha]
                
                return ResultadoAuditoria(
                    ativo_selecionado=ativo,
                    status_despacho=StatusDespachoEnum.APROVADO,
                    criterios_validacao=criterios,
                    valor_target_frete=requisicao.target_price_frete,
                    custo_variavel_estimado=custo_variavel,
                    margem_contribuicao_reais=margem,
                    ndcg_target_price=ndcg_target_price,
                    esta_em_explorador_malha=eh_novo and validacao_malha.passou,
                    tempo_auditoria_ms=tempo_auditoria,
                )
            
            # Nenhum candidato aprovado
            tempo_auditoria = (time.time() - tempo_inicio) * 1000
            
            self._logger.error(
                f"[AUDITOR] ❌ REJEITADO: Nenhum ativo aprovado após todas as validações"
            )
            
            # Retornar rejeição com o primeiro candidato (para logging)
            primeiro = resultado_rastreamento.ativos_candidatos[0]
            return ResultadoAuditoria(
                ativo_selecionado=primeiro,
                status_despacho=StatusDespachoEnum.REJEITADO,
                criterios_validacao=[],
                valor_target_frete=requisicao.target_price_frete,
                custo_variavel_estimado=primeiro.custo_km_base * (primeiro.distancia_km or 50),
                margem_contribuicao_reais=0.0,
                motivo_bloqueio="Nenhum ativo passou em todas as validações",
                tempo_auditoria_ms=tempo_auditoria,
            )
            
        except CheckerError:
            raise
        except Exception as e:
            self._logger.error(f"[AUDITOR] Erro na auditoria: {str(e)}")
            raise CheckerError(f"Erro durante auditoria P&L e risco: {str(e)}") from e
    
    def _validar_gr(self, ativo: AtivoLogistico) -> CriterioValidacaoLogistica:
        """
        Validação de GR: Gerenciamento de Risco (Seguro).
        
        Bloqueio IMEDIATO se vencido. Zero tolerância.
        
        Returns:
            CriterioValidacao com resultado
        """
        today = datetime.now().date()
        
        passou = (
            ativo.status_gerenciamento_risco.value == "vigente" and
            today <= ativo.data_vencimento_gr
        )
        
        detalhes = f"GR {'vigente' if passou else 'VENCIDO'} até {ativo.data_vencimento_gr}"
        
        return CriterioValidacaoLogistica(
            nome="Validação GR",
            descricao="Verifica se Gerenciamento de Risco (Seguro) está vigente",
            passou=passou,
            detalhes=detalhes,
            confianca=1.0,  # Certeza total nessa validação
        )
    
    def _validar_margem(self, margem: float) -> CriterioValidacaoLogistica:
        """
        Validação de margem: Viabilidade P&L.
        
        Rejeita se margem < 70%.
        
        Returns:
            CriterioValidacao com resultado
        """
        passou = margem >= self.margem_minima_viavel
        
        detalhes = f"Margem: {margem:.2%} (mín: {self.margem_minima_viavel:.2%})"
        
        return CriterioValidacaoLogistica(
            nome="Validação Margem P&L",
            descricao="Verifica se margem de contribuição é viável (>=70%)",
            passou=passou,
            detalhes=detalhes,
            confianca=0.95,  # Praticamente certeza
        )
    
    def _validar_exploracao_malha(
        self,
        ativo: AtivoLogistico,
        eh_novo: bool,
    ) -> CriterioValidacaoLogistica:
        """
        Validação de exploração de malha: 15% para novos motoristas.
        
        Se for novo (<30 dias), verifica se há cota disponível.
        Se for experiente, sempre passa.
        
        Returns:
            CriterioValidacao com resultado
        """
        if not eh_novo:
            # Motorista experiente: sempre passa
            return CriterioValidacaoLogistica(
                nome="Exploração Malha",
                descricao="Motorista experiente, sem restrição de cota",
                passou=True,
                detalhes="Experiente (>30 dias cadastro)",
                confianca=1.0,
            )
        
        # Motorista novo: verificar cota (simplificado: sempre há cota neste demo)
        passou = True  # Em produção, verificar histórico do dia
        detalhes = f"Novo motorista ({ativo.dias_cadastro} dias). Cota exploração: {self.cota_explorador_malha:.0%}"
        
        return CriterioValidacaoLogistica(
            nome="Exploração Malha",
            descricao="Valida alocação de 15% do dia para novos motoristas",
            passou=passou,
            detalhes=detalhes,
            confianca=0.85,
        )
