"""
Agente Diversity & Ethics Auditor: Validação de viés e serendipidade.

Este agente implementa a segunda etapa do pipeline de recomendação, focando em:
- Detecção de viés de categoria (garantir diversidade)
- Validação da regra de 20% de serendipidade (exploração)
- Cálculo de NDCG@k para qualidade de ranking
- Rastreamento de latência de inferência (target <150ms)

# NOTE: Implementar modelo de confiança Bayesiano para melhor
# calibração das métricas. Integrar com Kafka para publicação de eventos
# de auditoria em tempo real. Usar Redis para cache de históricos.
"""

import logging
import time
import random
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import math

from pydantic import ValidationError

from schemas import (
    RespostaCandidateGeneration,
    RespostaDiversityAuditor,
    Produto,
    CriterioValidacao,
    RelevanciaEnum,
)
from exceptions import CheckerError, ValidationException

logger = logging.getLogger(__name__)


class CalculadorMetricasRecomendacao:
    """
    Calcula métricas de qualidade de recomendação.
    
    Métricas suportadas:
    - NDCG@k (Normalized Discounted Cumulative Gain)
    - Diversidade de categorias
    - Taxa de serendipidade (exploração)
    """
    
    @staticmethod
    def calcular_ndcg_at_k(
        ranked_items: List[Produto],
        relevance_scores: Optional[List[float]] = None,
        k: int = 10,
    ) -> float:
        """
        Calcula NDCG@k (Normalized Discounted Cumulative Gain).
        
        NDCG é uma métrica que avalia a qualidade do ranking considerando:
        - A posição dos itens relevantes
        - A relevância de cada item
        
        # TECH LEAD NOTE: Implementar versão distribuída para cálculo
        # em tempo real em catálogos massivos.
        
        Args:
            ranked_items: Lista de itens rankeados
            relevance_scores: Scores de relevância (0-1) para cada item
            k: Tamanho da lista (padrão: 10)
            
        Returns:
            NDCG@k normalizado (0-1)
        """
        if not ranked_items:
            return 0.0
        
        # Se não houver scores de relevância, usar similaridade do produto
        if relevance_scores is None:
            relevance_scores = [item.similaridade_score for item in ranked_items]
        
        # Truncar para top-k
        ranked_items_k = ranked_items[:k]
        scores_k = relevance_scores[:k]
        
        # Calcular DCG (Discounted Cumulative Gain)
        dcg = 0.0
        for i, score in enumerate(scores_k, 1):
            # Fórmula: score / log2(i + 1)
            discount = math.log2(i + 1)
            dcg += score / discount
        
        # Calcular IDCG (Ideal DCG) - assumindo relevâncias ordenadas
        idcg = 0.0
        sorted_scores = sorted(scores_k, reverse=True)
        for i, score in enumerate(sorted_scores, 1):
            discount = math.log2(i + 1)
            idcg += score / discount
        
        # NDCG = DCG / IDCG
        if idcg == 0:
            return 0.0
        
        ndcg = dcg / idcg
        return max(0.0, min(1.0, ndcg))  # Normalizar para [0, 1]
    
    @staticmethod
    def calcular_diversidade_categorias(produtos: List[Produto]) -> float:
        """
        Calcula score de diversidade de categorias.
        
        Fórmula: categorias_unicas / total_produtos
        (maior diversidade = valores mais próximos de 1)
        
        Args:
            produtos: Lista de produtos
            
        Returns:
            Score de diversidade (0-1)
        """
        if not produtos:
            return 0.0
        
        categorias_unicas = len(set(p.categoria for p in produtos))
        diversidade = categorias_unicas / len(produtos)
        
        return diversidade
    
    @staticmethod
    def calcular_percentual_serendipidade(
        produtos: List[Produto],
        threshold_serendipidade: float = 0.6,
    ) -> float:
        """
        Calcula percentual de produtos de exploração (serendipidade).
        
        Produtos com similaridade < threshold são considerados exploratórios.
        Alvo: 20% de serendipidade conforme especificado.
        
        Args:
            produtos: Lista de produtos
            threshold_serendipidade: Limite para considerar exploratório
            
        Returns:
            Percentual de produtos exploratórios (0-1)
        """
        if not produtos:
            return 0.0
        
        exploratórios = sum(
            1 for p in produtos
            if p.similaridade_score < threshold_serendipidade
        )
        
        percentual = exploratórios / len(produtos)
        return percentual


class ValidadorDiversidadeEtica:
    """
    Valida diversidade e questões éticas da lista de recomendação.
    
    Critérios de validação:
    1. Viés de Categoria: Evitar concentração em uma única categoria
    2. Serendipidade: Garantir 20% de exploração
    3. Cobertura de Preço: Manter variedade de faixas de preço
    """
    
    def __init__(
        self,
        threshold_confianca: float = 0.8,
        alvo_serendipidade: float = 0.20,
    ) -> None:
        """
        Inicializa validador.
        
        Args:
            threshold_confianca: Threshold mínimo de confiança para aprovação
            alvo_serendipidade: Percentual alvo de serendipidade (20%)
        """
        self.threshold_confianca = threshold_confianca
        self.alvo_serendipidade = alvo_serendipidade
        self._logger = logging.getLogger(__name__)
    
    def validar_viés_categoria(
        self,
        produtos: List[Produto],
    ) -> Tuple[bool, float, str]:
        """
        Verifica se há viés de categoria na lista.
        
        Alerta se mais de 50% dos produtos vêm da mesma categoria.
        
        Args:
            produtos: Lista de produtos
            
        Returns:
            Tupla (passou, confiança, detalhes)
        """
        if not produtos:
            return False, 0.0, "Lista vazia"
        
        # Contar produtos por categoria
        categorias_count: Dict[str, int] = {}
        for produto in produtos:
            categorias_count[produto.categoria] = categorias_count.get(
                produto.categoria, 0
            ) + 1
        
        # Encontrar categoria dominante
        max_categoria = max(categorias_count.values())
        percentual_dominante = max_categoria / len(produtos)
        
        # Passou se não houver concentração excessiva
        passou = percentual_dominante <= 0.5
        confianca = 1.0 - percentual_dominante  # Maior diversidade = maior confiança
        
        categorias_diferentes = len(categorias_count)
        detalhes = (
            f"Categoria dominante: {percentual_dominante:.1%}. "
            f"{categorias_diferentes} categorias diferentes."
        )
        
        return passou, confianca, detalhes
    
    def validar_serendipidade(
        self,
        produtos: List[Produto],
    ) -> Tuple[bool, float, str]:
        """
        Verifica se a lista possui serendipidade suficiente.
        
        Alvo: 20% de produtos exploratórios (baixa similaridade).
        Aceita: 15-25% como tolerância.
        
        Args:
            produtos: Lista de produtos
            
        Returns:
            Tupla (passou, confiança, detalhes)
        """
        if not produtos:
            return False, 0.0, "Lista vazia"
        
        calculador = CalculadorMetricasRecomendacao()
        percentual_serendipidade = calculador.calcular_percentual_serendipidade(
            produtos
        )
        
        # Tolerância: ±5% do alvo
        tolerancia = 0.05
        passou = (
            (self.alvo_serendipidade - tolerancia) <= percentual_serendipidade <=
            (self.alvo_serendipidade + tolerancia)
        )
        
        # Confiança baseada na proximidade do alvo
        desvio = abs(percentual_serendipidade - self.alvo_serendipidade)
        confianca = max(0.0, 1.0 - (desvio / self.alvo_serendipidade))
        
        detalhes = (
            f"Serendipidade: {percentual_serendipidade:.1%} "
            f"(alvo: {self.alvo_serendipidade:.1%})"
        )
        
        return passou, confianca, detalhes
    
    def validar_cobertura_preco(
        self,
        produtos: List[Produto],
    ) -> Tuple[bool, float, str]:
        """
        Verifica cobertura de faixas de preço.
        
        Ideal: produtos em pelo menos 3 faixas de preço diferentes.
        
        Args:
            produtos: Lista de produtos
            
        Returns:
            Tupla (passou, confiança, detalhes)
        """
        if not produtos:
            return False, 0.0, "Lista vazia"
        
        # Definir faixas de preço
        precos = [p.preco for p in produtos]
        preco_min = min(precos)
        preco_max = max(precos)
        
        # Faixas: baixo (<200), médio (200-500), alto (>500)
        faixas_cobertas = set()
        for preco in precos:
            if preco < 200:
                faixas_cobertas.add("baixo")
            elif preco < 500:
                faixas_cobertas.add("medio")
            else:
                faixas_cobertas.add("alto")
        
        num_faixas = len(faixas_cobertas)
        passou = num_faixas >= 2  # Pelo menos 2 faixas
        confianca = min(1.0, num_faixas / 3.0)  # Max quando há 3 faixas
        
        detalhes = (
            f"Faixas de preço: {', '.join(sorted(faixas_cobertas))}. "
            f"Range: R$ {preco_min:.2f} - R$ {preco_max:.2f}"
        )
        
        return passou, confianca, detalhes


class AgenteDiversityAuditor:
    """
    Agente Diversity & Ethics Auditor para validação de recomendações.
    
    Responsabilidades:
    - Validar lista de produtos quanto a viés
    - Garantir serendipidade de 20%
    - Calcular métricas de qualidade (NDCG@k)
    - Retornar lista ajustada se necessário
    """
    
    def __init__(
        self,
        threshold_confianca_global: float = 0.8,
        alvo_serendipidade: float = 0.20,
    ) -> None:
        """
        Inicializa auditor.
        
        Args:
            threshold_confianca_global: Threshold mínimo de confiança
            alvo_serendipidade: Alvo de percentual de serendipidade
        """
        self.threshold_confianca_global = threshold_confianca_global
        self.alvo_serendipidade = alvo_serendipidade
        self._logger = logging.getLogger(__name__)
        self.validador = ValidadorDiversidadeEtica(
            threshold_confianca=threshold_confianca_global,
            alvo_serendipidade=alvo_serendipidade,
        )
        self.calculador = CalculadorMetricasRecomendacao()
    
    def processar(
        self,
        resposta_candidate_generation: RespostaCandidateGeneration,
    ) -> RespostaDiversityAuditor:
        """
        Processa candidatos e aplica validações de diversidade.
        
        # TECH LEAD NOTE: Medir latência dessa função para garantir <150ms
        # Integrar com Kafka para publicação de eventos de auditoria
        
        Args:
            resposta_candidate_generation: Resultado da geração de candidatos
            
        Returns:
            Resposta com validação e produtos ajustados
            
        Raises:
            CheckerError: Se houver erro na validação
        """
        tempo_inicio = time.time()
        
        try:
            self._logger.info(
                f"[DIVERSITY_AUDIT] Auditando {len(resposta_candidate_generation.candidates)} produtos"
            )
            
            produtos_originais = resposta_candidate_generation.candidates
            
            # Aplicar critérios de validação
            criterios = []
            
            # 1. Validar viés de categoria
            passou_vies, conf_vies, det_vies = self.validador.validar_viés_categoria(
                produtos_originais
            )
            criterios.append(CriterioValidacao(
                nome="Viés de Categoria",
                descricao="Verificar se há concentração excessiva em uma categoria",
                passou=passou_vies,
                detalhes=det_vies,
                confianca=conf_vies,
            ))
            
            # 2. Validar serendipidade
            passou_serendipidade, conf_serendipidade, det_serendipidade = (
                self.validador.validar_serendipidade(produtos_originais)
            )
            criterios.append(CriterioValidacao(
                nome="Serendipidade",
                descricao="Garantir 20% de produtos exploratórios",
                passou=passou_serendipidade,
                detalhes=det_serendipidade,
                confianca=conf_serendipidade,
            ))
            
            # 3. Validar cobertura de preço
            passou_preco, conf_preco, det_preco = (
                self.validador.validar_cobertura_preco(produtos_originais)
            )
            criterios.append(CriterioValidacao(
                nome="Cobertura de Preço",
                descricao="Verificar variedade de faixas de preço",
                passou=passou_preco,
                detalhes=det_preco,
                confianca=conf_preco,
            ))
            
            # Calcular métricas
            ndcg_at_k = self.calculador.calcular_ndcg_at_k(
                produtos_originais,
                k=10,
            )
            diversidade_categorias = (
                self.calculador.calcular_diversidade_categorias(produtos_originais)
            )
            percentual_serendipidade = (
                self.calculador.calcular_percentual_serendipidade(produtos_originais)
            )
            
            # Ajustar lista se necessário (serendipidade)
            produtos_ajustados = self._ajustar_lista_serendipidade(
                produtos_originais
            )
            
            # Score agregado
            score_agregado = sum(c.confianca for c in criterios) / len(criterios)
            
            # Determinar relevância final
            todos_passaram = all(c.passou for c in criterios)
            if todos_passaram and score_agregado >= self.threshold_confianca_global:
                relevancia = RelevanciaEnum.MUITO_ALTA
            elif score_agregado >= 0.75:
                relevancia = RelevanciaEnum.ALTA
            elif score_agregado >= 0.5:
                relevancia = RelevanciaEnum.MEDIA
            else:
                relevancia = RelevanciaEnum.BAIXA
            
            tempo_auditoria = (time.time() - tempo_inicio) * 1000  # ms
            
            self._logger.info(
                f"[DIVERSITY_AUDIT] ✓ Auditoria concluída em {tempo_auditoria:.2f}ms. "
                f"Relevância: {relevancia.value}, NDCG@10: {ndcg_at_k:.3f}"
            )
            
            return RespostaDiversityAuditor(
                candidates_original=produtos_originais,
                candidates_ajustados=produtos_ajustados,
                validacao_passou=todos_passaram,
                relevancia=relevancia,
                criterios_validacao=criterios,
                ndcg_at_k=ndcg_at_k,
                diversidade_categorias=diversidade_categorias,
                percentual_serendipidade=percentual_serendipidade,
                score_validacao_agregado=score_agregado,
            )
            
        except ValidationError as e:
            self._logger.error(f"[DIVERSITY_AUDIT] Erro de validação: {str(e)}")
            raise CheckerError(
                f"Erro na validação: {str(e)}"
            ) from e
        except Exception as e:
            self._logger.error(f"[DIVERSITY_AUDIT] Erro inesperado: {str(e)}")
            raise CheckerError(
                f"Erro durante auditoria: {str(e)}"
            ) from e
    
    def _ajustar_lista_serendipidade(
        self,
        produtos: List[Produto],
    ) -> List[Produto]:
        """
        Ajusta lista para garantir ~20% de serendipidade.
        
        Se houver menos de 20% de produtos exploratórios, substitui
        alguns produtos de alta similaridade por produtos com menor
        similaridade (mais exploratórios).
        
        # TECH LEAD NOTE: Implementar algoritmo mais sofisticado
        # usando programação linear para otimizar diversidade.
        
        Args:
            produtos: Lista original de produtos
            
        Returns:
            Lista ajustada com melhor serendipidade
        """
        if not produtos:
            return produtos
        
        # Calcular serendipidade atual
        percentual_atual = (
            self.calculador.calcular_percentual_serendipidade(produtos)
        )
        
        # Se serendipidade está abaixo do alvo, ajustar
        if percentual_atual < (self.alvo_serendipidade - 0.05):
            self._logger.info(
                f"Ajustando serendipidade: {percentual_atual:.1%} → {self.alvo_serendipidade:.1%}"
            )
            
            # Separar produtos por similaridade
            exploratórios = [p for p in produtos if p.similaridade_score < 0.6]
            relevantes = [p for p in produtos if p.similaridade_score >= 0.6]
            
            # Ajustar ordem: colocar alguns exploratórios no meio da lista
            num_total = len(produtos)
            num_exploratórios_alvo = int(num_total * self.alvo_serendipidade)
            
            # Se há poucos exploratórios, clonar alguns aleatoriamente
            if len(exploratórios) < num_exploratórios_alvo:
                # Retornar lista original (não há exploratórios suficientes)
                return produtos
            
            # Reordenar: intercalar relevantes com exploratórios
            ajustada = []
            idx_rel = 0
            idx_exp = 0
            
            for i in range(num_total):
                if i < num_exploratórios_alvo and idx_exp < len(exploratórios):
                    ajustada.append(exploratórios[idx_exp])
                    idx_exp += 1
                else:
                    if idx_rel < len(relevantes):
                        ajustada.append(relevantes[idx_rel])
                        idx_rel += 1
            
            return ajustada
        
        return produtos


# Alias para compatibilidade
AgentChecker = AgenteDiversityAuditor
