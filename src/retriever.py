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
import math
from typing import List, Optional
from datetime import datetime

from schemas import (
    RequisicaoCarga,
    ResultadoRastreamento,
    AtivoLogistico,
    GeoLocalizacao,
    TipoFrotaEnum,
    StatusGestaRiscoEnum,
)
from exceptions import RetrieverError

logger = logging.getLogger(__name__)


class SimuladorRedisGeospatial:
    """
    Simulador de Redis Geospatial para ambiente local.
    
    Em produção, seria integrado com:
    - Redis com módulo Geospatial real
    - GEORADIUS para busca por raio
    - Atualização de GPS a cada 30-60 segundos
    - TTL de 2 horas para ativos offline
    - Sharding por zona logística
    
    # TODO: Integração com Redis real
    """
    
    def __init__(self) -> None:
        """Inicializa frota com ativos de exemplo."""
        self._ativos: dict[str, AtivoLogistico] = {
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
    
    def _calcular_distancia_haversine(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """
        Calcula distância entre dois pontos usando fórmula de Haversine.
        
        Raio da Terra: 6371 km
        """
        R = 6371  # Raio em km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (
            math.sin(delta_lat / 2) ** 2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def georadius(
        self,
        lat_origem: float,
        lon_origem: float,
        raio_km: float,
        tipos_frota: List[TipoFrotaEnum],
    ) -> List[AtivoLogistico]:
        """
        Simula GEORADIUS do Redis: busca ativos dentro do raio e com tipos corretos.
        
        Returns:
            Ativos encontrados, já com distância calculada
        """
        resultado = []
        
        for ativo in self._ativos.values():
            # Verificar se tipo de frota é aceito
            if ativo.tipo_frota not in tipos_frota:
                continue
            
            # Calcular distância
            dist = self._calcular_distancia_haversine(
                lat_origem,
                lon_origem,
                ativo.geoloc_atual.latitude,
                ativo.geoloc_atual.longitude,
            )
            
            # Verificar se está no raio
            if dist <= raio_km:
                # Atualizar distância no objeto
                ativo_copia = ativo.model_copy()
                ativo_copia.distancia_km = dist
                resultado.append(ativo_copia)
        
        return resultado


class AgenteRastreador:
    """
    Agente Rastreador (Tracker): Responsável pela busca geo-espacial.
    
    Implementa busca de ativos logísticos próximos usando:
    - Geo-spatial indexing (Redis Geospatial ou Haversine)
    - Filtros por tipo de frota e capacidade
    - Ranking por eficiência geo-espacial
    - Latência alvo: <10ms
    """
    
    def __init__(
        self,
        timeout_seconds: float = 0.05,  # 50ms para ter margem
        max_candidatos: int = 100,
    ) -> None:
        """
        Inicializa agente rastreador.
        
        Args:
            timeout_seconds: Timeout máximo em segundos
            max_candidatos: Máximo de candidatos a retornar
        """
        self.timeout_seconds = timeout_seconds
        self.max_candidatos = max_candidatos
        self._logger = logging.getLogger(__name__)
        self.redis_geo = SimuladorRedisGeospatial()
    
    def processar(
        self,
        requisicao: RequisicaoCarga,
    ) -> ResultadoRastreamento:
        """
        Processa requisição e realiza rastreamento geo-espacial.
        
        Etapas:
        1. Redis GEORADIUS por raio da origem
        2. Filtrar por tipos de frota aceitos
        3. Filtrar por capacidade mínima
        4. Calcular score de eficiência para cada ativo
        5. Rankear e retornar top-k
        
        Args:
            requisicao: Requisição de carga validada
            
        Returns:
            Resultado com ativos candidatos ordenados
            
        Raises:
            RetrieverError: Se houver erro no rastreamento
        """
        tempo_inicio = time.time()
        
        try:
            self._logger.info(
                f"[RASTREADOR] Rastreando ativos para carga: {requisicao.id_carga}"
            )
            
            # 1. Redis GEORADIUS: Buscar ativos no raio
            ativos_no_raio = self.redis_geo.georadius(
                lat_origem=requisicao.origem.latitude,
                lon_origem=requisicao.origem.longitude,
                raio_km=requisicao.raio_busca_km,
                tipos_frota=requisicao.tipos_frota_aceitos,
            )
            
            if not ativos_no_raio:
                self._logger.warning(
                    f"[RASTREADOR] ⚠ Nenhum ativo encontrado no raio de {requisicao.raio_busca_km}km"
                )
                ativos_no_raio = []
            
            # 2. Filtrar por capacidade mínima
            ativos_validos = [
                a for a in ativos_no_raio
                if a.capacidade_kg >= requisicao.peso_kg
            ]
            
            # 3. Calcular score de eficiência para cada ativo
            ativos_com_score = []
            for ativo in ativos_validos:
                score_eficiencia = self._calcular_score_eficiencia(ativo, requisicao)
                ativo.eficiencia_score = score_eficiencia
                ativos_com_score.append(ativo)
            
            # 4. Rankear por eficiência (descendente)
            ativos_rankeados = sorted(
                ativos_com_score,
                key=lambda a: a.eficiencia_score or 0.0,
                reverse=True,
            )
            
            # 5. Limitar ao top-k solicitado
            candidatos = ativos_rankeados[:requisicao.top_k_despacho]
            
            tempo_rastreamento = (time.time() - tempo_inicio) * 1000  # em ms
            
            self._logger.info(
                f"[RASTREADOR] ✓ Rastreados {len(candidatos)} ativos em {tempo_rastreamento:.2f}ms"
            )
            
            return ResultadoRastreamento(
                id_carga=requisicao.id_carga,
                ativos_candidatos=candidatos,
                metodo_busca="redis_geospatial",
                tempo_rastreamento_ms=tempo_rastreamento,
                raio_busca_utilizado_km=requisicao.raio_busca_km,
            )
            
        except Exception as e:
            self._logger.error(f"[RASTREADOR] Erro no rastreamento: {str(e)}")
            raise RetrieverError(
                f"Erro durante rastreamento geo-espacial: {str(e)}"
            ) from e
    
    def _calcular_score_eficiencia(
        self,
        ativo: AtivoLogistico,
        requisicao: RequisicaoCarga,
    ) -> float:
        """
        Calcula score de eficiência do ativo para a carga.
        
        Fórmula (Logística):
        Eficiencia = (1 / Distancia_km) × SLA_Score × Margem_Contribuicao_Base
        
        Onde:
        - 1/Distancia: Quanto mais próximo, melhor
        - SLA_Score: Histórico SLA do motorista (0-1)
        - Margem_Contribuicao_Base: Estimativa inicial baseada em custos
        
        Args:
            ativo: Ativo logístico
            requisicao: Requisição de carga
            
        Returns:
            Score de eficiência (quanto maior, melhor)
        """
        if not ativo.distancia_km or ativo.distancia_km == 0:
            distancia_factor = 1.0
        else:
            distancia_factor = 1.0 / ativo.distancia_km
        
        # SLA Score: usar histórico direto (0-1)
        sla_score = ativo.historico_sla
        
        # Estimativa de margem baseada em custos
        custo_viagem_estimado = ativo.custo_km_base * (ativo.distancia_km or 50)
        margem_base = max(0.0, (requisicao.target_price_frete - custo_viagem_estimado) / requisicao.target_price_frete)
        margem_score = max(0.3, margem_base)  # Minimum 0.3
        
        # Score de eficiência
        score_eficiencia = (distancia_factor * 0.5) + (sla_score * 0.3) + (margem_score * 0.2)
        
        return score_eficiencia
