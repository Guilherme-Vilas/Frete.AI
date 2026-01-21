"""
Agente Rastreador (Tracker): Responsável pela busca geo-espacial de ativos logísticos.

Este agente implementa a primeira etapa do pipeline de despacho Mobiis, focando em:
- Rastreamento Geo-Espacial com Redis GEORADIUS
- Busca de ativos logísticos próximos à origem da carga
- Ranking por eficiência (distância × SLA × margem)
- Rastreamento de performance (latência target <10ms)

# TECH LEAD NOTE: Redis Geospatial para latência <10ms mesmo com 1M+ ativos.
# Circuit breaker com fallback em memória se Redis falhar.
# Integrar com Kafka para publicação de eventos de rastreamento.
# OpenTelemetry para monitoração de P99 latência.

# TECH LEAD NOTE: Sharding por zona logística para escalabilidade horizontal.
# TTL: 2 horas para ativos offline. Update GPS a cada 30-60 segundos.
"""

import logging
import time
import random
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import math

from pydantic import ValidationError

from schemas import (
    RequisicaoCarga,
    ResultadoRastreamento,
    AtivoLogistico,
    GeoLocalizacao,
    TipoFrotaEnum,
    StatusGestaRiscoEnum,
)
from exceptions import RetrieverError, TimeoutError as CustomTimeoutError

logger = logging.getLogger(__name__)


class SimuladorAtivosLogisticos:
    """
    Simulador de frota de ativos logísticos Mobiis.
    
    Em produção, seria integrado com:
    - Redis Geospatial para índice geo de ativos
    - PostgreSQL com PostGIS para histórico de rotas
    - GPS em tempo real via Kafka + streaming
    - API de Gerenciamento de Frota
    
    # TODO: Integração com Redis Geospatial real
    """
    
    def __init__(self) -> None:
        """Inicializa frota com ativos de exemplo."""
        self._ativos: Dict[str, AtivoLogistico] = {
            "ABC-1234": AtivoLogistico(
                id_placa="ABC-1234",
                tipo_frota=TipoFrotaEnum.BITREM,
                motorista_id="123.456.789-00",
                motorista_nome="João Silva",
                geoloc_atual=GeoLocalizacao(
                    latitude=-23.5505,
                    longitude=-46.6333,
                    zona_logistica="SP-Capital"
                ),
                status_gerenciamento_risco=StatusGestaRiscoEnum.VIGENTE,
                data_vencimento_gr=datetime(2026, 6, 30).date(),
                historico_sla=0.95,
                custo_km_base=30.50,
                dias_cadastro=450,
                num_entregas_completas=2847,
                capacidade_kg=25000,
                tipos_frota_aceitos=[TipoFrotaEnum.BITREM],
            ),
            "XYZ-5678": AtivoLogistico(
                id_placa="XYZ-5678",
                tipo_frota=TipoFrotaEnum.CARRETA,
                motorista_id="987.654.321-00",
                motorista_nome="Maria Santos",
                geoloc_atual=GeoLocalizacao(
                    latitude=-23.4729,
                    longitude=-46.5550,
                    zona_logistica="SP-Capital"
                ),
                status_gerenciamento_risco=StatusGestaRiscoEnum.VIGENTE,
                data_vencimento_gr=datetime(2026, 8, 15).date(),
                historico_sla=0.92,
                custo_km_base=28.00,
                dias_cadastro=320,
                num_entregas_completas=1654,
                capacidade_kg=20000,
                tipos_frota_aceitos=[TipoFrotaEnum.CARRETA],
            ),
            "MNO-9999": AtivoLogistico(
                id_placa="MNO-9999",
                tipo_frota=TipoFrotaEnum.TRUCK,
                motorista_id="111.222.333-44",
                motorista_nome="Leonardo Silva",
                geoloc_atual=GeoLocalizacao(
                    latitude=-23.5580,
                    longitude=-46.6720,
                    zona_logistica="SP-Capital"
                ),
                status_gerenciamento_risco=StatusGestaRiscoEnum.VIGENTE,
                data_vencimento_gr=datetime(2026, 9, 20).date(),
                historico_sla=0.88,
                custo_km_base=32.75,
                dias_cadastro=18,  # Novo motorista (< 30 dias)
                num_entregas_completas=45,
                capacidade_kg=15000,
                tipos_frota_aceitos=[TipoFrotaEnum.TRUCK],
            ),
            "PQR-2468": AtivoLogistico(
                id_placa="PQR-2468",
                tipo_frota=TipoFrotaEnum.BITREM,
                motorista_id="555.666.777-88",
                motorista_nome="José Oliveira",
                geoloc_atual=GeoLocalizacao(
                    latitude=-23.3815,
                    longitude=-46.7394,
                    zona_logistica="SP-ABC"
                ),
                status_gerenciamento_risco=StatusGestaRiscoEnum.VENCIDO,  # GR VENCIDO!
                data_vencimento_gr=datetime(2025, 12, 15).date(),  # Vencido
                historico_sla=0.91,
                custo_km_base=31.20,
                dias_cadastro=680,
                num_entregas_completas=3421,
                capacidade_kg=25000,
                tipos_frota_aceitos=[TipoFrotaEnum.BITREM],
            ),
            "STU-3579": AtivoLogistico(
                id_placa="STU-3579",
                tipo_frota=TipoFrotaEnum.CARRETA,
                motorista_id="999.888.777-66",
                motorista_nome="Marcos Costa",
                geoloc_atual=GeoLocalizacao(
                    latitude=-23.4200,
                    longitude=-46.4700,
                    zona_logistica="SP-Leste"
                ),
                status_gerenciamento_risco=StatusGestaRiscoEnum.VIGENTE,
                data_vencimento_gr=datetime(2026, 7, 10).date(),
                historico_sla=0.93,
                custo_km_base=27.50,
                dias_cadastro=250,
                num_entregas_completas=1456,
                capacidade_kg=18000,
                tipos_frota_aceitos=[TipoFrotaEnum.CARRETA],
            ),
        }
    
    def obter_ativos_por_zona(self, zona: Optional[str] = None) -> List[AtivoLogistico]:
        """Retorna ativos por zona logística (simula Redis GEORADIUS)."""
        if zona is None:
            return list(self._ativos.values())
        return [
            a for a in self._ativos.values()
            if a.geoloc_atual.zona_logistica == zona
        ]
    
    def obter_ativo(self, id_placa: str) -> Optional[AtivoLogistico]:
        """Retorna um ativo específico."""
        return self._ativos.get(id_placa)
                nome="Luminária Smart WiFi",
                categoria="Casa Inteligente",
                descricao="Luminária com controle remoto via app",
                preco=149.99,
                tags=["WiFi", "Automação", "LED"],
                similaridade_score=0.72,
                recencia_historico=45,
                vendor="SmartHome Pro",
            ),
            "SKU-CASA-002": Produto(
                id="SKU-CASA-002",
                nome="Câmera de Segurança IP",
                categoria="Casa Inteligente",
                descricao="Câmera HD com visão noturna e detecção de movimento",
                preco=299.99,
                tags=["Segurança", "HD", "IP"],
                similaridade_score=0.68,
                recencia_historico=None,
                vendor="SecurityTech",
            ),
            "SKU-MODA-001": Produto(
                id="SKU-MODA-001",
                nome="Camiseta Premium Comfort",
                categoria="Moda",
                descricao="Camiseta de algodão com design exclusivo",
                preco=79.90,
                tags=["Algodão", "Casual", "Design"],
                similaridade_score=0.55,
                recencia_historico=60,
                vendor="FashionBrand",
            ),
            "SKU-ESPORT-001": Produto(
                id="SKU-ESPORT-001",
                nome="Mochila para Esportes",
                categoria="Esportes",
                descricao="Mochila ergonômica com compartimentos especiais",
                preco=189.99,
                tags=["Esporte", "Ergonômica", "Impermeável"],
                similaridade_score=0.70,
                recencia_historico=None,
                vendor="SportsGear",
            ),
        }
    
    def obter_todos_produtos(self) -> List[Produto]:
        """Retorna todos os produtos do catálogo."""
        return list(self._produtos.values())
    
    def obter_por_categoria(self, categoria: str) -> List[Produto]:
        """Retorna produtos filtrados por categoria."""
        return [p for p in self._produtos.values() if p.categoria == categoria]
    
    def obter_por_ids(self, ids: List[str]) -> List[Produto]:
        """Retorna produtos pelos IDs."""
        return [self._produtos[id] for id in ids if id in self._produtos]


class AgenteCandidateGeneration:
    """
    Agente responsável pela geração de candidatos de produtos.
    
    Implementa Content-Based Filtering baseado em:
    - Similaridade com histórico de visualizações
    - Histórico de compras
    - Preferências de categoria
    - Serendipidade (exploração)
    """
    
    def __init__(
        self,
        timeout_seconds: float = 10.0,
        max_candidatos: int = 100,
        relevancia_threshold: float = 0.5,
    ) -> None:
        """
        Inicializa agente.
        
        Args:
            timeout_seconds: Timeout máximo em segundos
            max_candidatos: Máximo de candidatos a retornar
            relevancia_threshold: Threshold mínimo de similaridade
        """
        self.timeout_seconds = timeout_seconds
        self.max_candidatos = max_candidatos
        self.relevancia_threshold = relevancia_threshold
        self._logger = logging.getLogger(__name__)
        self.catalogo = SimuladorCatalogoProdutos()
    
    def processar(
        self,
        entrada: CandidateGenerationInput,
    ) -> RespostaCandidateGeneration:
        """
        Processa entrada e gera candidatos de produtos.
        
        # TECH LEAD NOTE: Medir latência dessa função
        # Integrar com OpenTelemetry para rastreamento distribuído
        
        Args:
            entrada: Input validado
            
        Returns:
            Resposta com candidatos gerados
            
        Raises:
            RetrieverError: Se houver erro na geração
        """
        tempo_inicio = time.time()
        
        try:
            self._logger.info(
                f"[CANDIDATE_GEN] Gerando candidatos para usuário: {entrada.usuario_id}"
            )
            
            # Obter todos os produtos
            produtos_disponiveis = self.catalogo.obter_todos_produtos()
            
            # Filtrar por categoria se especificado
            if entrada.filtros_categoria:
                produtos_disponiveis = [
                    p for p in produtos_disponiveis
                    if p.categoria in entrada.filtros_categoria
                ]
            
            # Calcular scores de similaridade
            scores = self._calcular_scores_similaridade(
                entrada.historico_usuario,
                produtos_disponiveis,
            )
            
            # Rankear produtos
            produtos_rankeados = sorted(
                zip(produtos_disponiveis, scores),
                key=lambda x: x[1],
                reverse=True,
            )
            
            # Filtrar por threshold
            produtos_validos = [
                p for p, score in produtos_rankeados
                if score >= self.relevancia_threshold
            ]
            
            # Limitar ao top-k solicitado
            candidatos = produtos_validos[:entrada.top_k]
            
            tempo_geracao = (time.time() - tempo_inicio) * 1000  # em ms
            
            self._logger.info(
                f"[CANDIDATE_GEN] ✓ Gerados {len(candidatos)} candidatos em {tempo_geracao:.2f}ms"
            )
            
            return RespostaCandidateGeneration(
                usuario_id=entrada.usuario_id,
                candidates=candidatos,
                metodo_geracao="content_based",
                tempo_geracao_ms=tempo_geracao,
            )
            
        except ValidationError as e:
            self._logger.error(f"[CANDIDATE_GEN] Erro de validação: {str(e)}")
            raise RetrieverError(
                f"Erro na validação do candidato: {str(e)}"
            ) from e
        except Exception as e:
            self._logger.error(f"[CANDIDATE_GEN] Erro inesperado: {str(e)}")
            raise RetrieverError(
                f"Erro durante geração de candidatos: {str(e)}"
            ) from e
    
    def _calcular_scores_similaridade(
        self,
        historico: Optional[HistoricoUsuario],
        produtos: List[Produto],
    ) -> List[float]:
        """
        Calcula scores de similaridade para produtos.
        
        # TECH LEAD NOTE: Implementar busca vetorial com Faiss
        # para escalabilidade em catálogos com milhões de produtos.
        # Cache embeddings em Redis.
        
        Args:
            historico: Histórico do usuário
            produtos: Lista de produtos
            
        Returns:
            Lista de scores (um por produto)
        """
        if not historico:
            # Sem histórico, retornar scores baseados em similaridade padrão
            return [p.similaridade_score for p in produtos]
        
        scores = []
        for produto in produtos:
            # Excluir produtos já visualizados ou comprados
            if (produto.id in historico.produtos_visualizados or
                produto.id in historico.produtos_comprados):
                scores.append(0.0)
                continue
            
            # Score baseado em categoria
            score_categoria = 1.0 if (
                produto.categoria in historico.categorias_preferidas
            ) else 0.3
            
            # Score baseado em similaridade do produto
            score_similaridade = produto.similaridade_score
            
            # Score de recência (preferir produtos recentes)
            score_recencia = 1.0
            if produto.recencia_historico:
                # Diminuir score se visualizado há muito tempo
                score_recencia = max(0.5, 1.0 - (produto.recencia_historico / 365))
            
            # Combinar scores (média ponderada)
            score_final = (
                score_similaridade * 0.6 +
                score_categoria * 0.3 +
                score_recencia * 0.1
            )
            
            scores.append(score_final)
        
        return scores
