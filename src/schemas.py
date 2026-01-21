"""
Modelos de dados com validação Pydantic para o Engine de Despacho de Cargas Mobiis.

Nota Técnica: A validação estruturada é crítica em sistemas de logística
para garantir integridade dos dados de despacho e auditabilidade P&L.
Cada modelo representa um contrato entre componentes do pipeline de rastreamento e auditoria.

# TECH LEAD NOTE: Redis Geospatial para latência <10ms. Kafka para event streaming
# de despachos em tempo real. OpenTelemetry para métricas de P99 latência.
# Integrar com Feature Store (Redis) para cache de ativos logísticos.
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class StatusGestaRiscoEnum(str, Enum):
    """Status de Gerenciamento de Risco (Seguro/GR)."""
    VIGENTE = "vigente"
    VENCIDO = "vencido"
    PENDENTE = "pendente"
    BLOQUEADO = "bloqueado"


class TipoFrotaEnum(str, Enum):
    """Tipos de frota disponíveis."""
    BITREM = "bitrem"
    CARRETA = "carreta"
    TRUCK = "truck"
    VEICULO_LEVE = "veiculo_leve"


class StatusDespachoEnum(str, Enum):
    """Status do despacho de carga."""
    APROVADO = "aprovado"
    BLOQUEADO_GR = "bloqueado_gr"
    BLOQUEADO_MARGEM = "bloqueado_margem"
    EXPLORADOR_MALHA = "explorador_malha"
    REJEITADO = "rejeitado"


class GeoLocalizacao(BaseModel):
    """Geolocalização com timestamp (para Redis Geospatial)."""
    
    latitude: float = Field(..., ge=-90, le=90, description="Latitude (-90 a 90)")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude (-180 a 180)")
    timestamp_atualizacao: datetime = Field(
        default_factory=datetime.utcnow,
        description="Último update de GPS"
    )
    zona_logistica: Optional[str] = Field(
        None,
        description="Zona logística (SP-Capital, SP-Interior, RJ, etc)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "latitude": -23.5505,
                "longitude": -46.6333,
                "timestamp_atualizacao": "2026-01-21T15:30:00.000Z",
                "zona_logistica": "SP-Capital"
            }
        }


class AtivoLogistico(BaseModel):
    """Representa um ativo logístico (veículo/motorista) candidato para despacho."""
    
    id_placa: str = Field(..., description="Placa do veículo (ex: ABC-1234)")
    tipo_frota: TipoFrotaEnum = Field(..., description="Tipo de frota")
    motorista_id: str = Field(..., description="ID do motorista (CPF)")
    motorista_nome: str = Field(..., description="Nome do motorista")
    
    # Geolocalização e disponibilidade
    geoloc_atual: GeoLocalizacao = Field(..., description="Localização atual do ativo")
    status_gerenciamento_risco: StatusGestaRiscoEnum = Field(
        ...,
        description="Status do GR (Seguro): vigente/vencido/bloqueado"
    )
    data_vencimento_gr: date = Field(
        ...,
        description="Data de vencimento do Gerenciamento de Risco"
    )
    
    # Performance e histórico SLA
    historico_sla: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Taxa de SLA cumprido (0-1)"
    )
    num_entregas_completas: int = Field(
        default=0,
        description="Número de entregas completadas"
    )
    
    # Custos operacionais
    custo_km_base: float = Field(
        ...,
        gt=0,
        description="Custo operacional por km em R$"
    )
    dias_cadastro: int = Field(
        default=0,
        description="Dias desde cadastro no sistema (para malha exploratória)"
    )
    
    # Capacidade
    capacidade_kg: float = Field(
        default=25000,
        description="Capacidade máxima de carga em kg"
    )
    tipos_frota_aceitos: List[TipoFrotaEnum] = Field(
        default_factory=list,
        description="Tipos de carga que aceita"
    )
    
    # Score de eficiência (calculado dinamicamente)
    eficiencia_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Score de eficiência calculado pelo Rastreador"
    )
    distancia_km: Optional[float] = Field(
        None,
        description="Distância até a origem da carga (calculado)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id_placa": "ABC-1234",
                "tipo_frota": "bitrem",
                "motorista_id": "123.456.789-00",
                "motorista_nome": "João Silva",
                "geoloc_atual": {
                    "latitude": -23.5505,
                    "longitude": -46.6333,
                    "zona_logistica": "SP-Capital"
                },
                "status_gerenciamento_risco": "vigente",
                "data_vencimento_gr": "2026-06-30",
                "historico_sla": 0.95,
                "custo_km_base": 30.50,
                "dias_cadastro": 450
            }
        }


class RequisicaoCarga(BaseModel):
    """Requisição de despacho de carga."""
    
    id_carga: str = Field(..., description="ID único da carga")
    origem: GeoLocalizacao = Field(..., description="Localização de origem")
    destino: GeoLocalizacao = Field(..., description="Localização de destino")
    
    # Características da carga
    peso_kg: float = Field(..., gt=0, description="Peso da carga em kg")
    dimensoes_descricao: Optional[str] = Field(None, description="Descrição de dimensões")
    tipos_frota_aceitos: List[TipoFrotaEnum] = Field(
        ...,
        description="Tipos de frota que podem transportar"
    )
    
    # Precificação e SLA
    target_price_frete: float = Field(..., gt=0, description="Valor alvo do frete em R$")
    sla_entrega_horas: int = Field(..., gt=0, description="Prazo SLA em horas")
    
    # Restrições de busca
    raio_busca_km: float = Field(
        default=150,
        gt=0,
        description="Raio de busca geospatial em km"
    )
    top_k_despacho: int = Field(
        default=10,
        ge=1,
        description="Top-K candidatos a considerar"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id_carga": "CARGA-2026-001",
                "origem": {
                    "latitude": -23.5505,
                    "longitude": -46.6333,
                    "zona_logistica": "SP-Capital"
                },
                "destino": {
                    "latitude": -19.9191,
                    "longitude": -43.9386,
                    "zona_logistica": "RJ-Rio"
                },
                "peso_kg": 18000,
                "tipos_frota_aceitos": ["bitrem", "carreta"],
                "target_price_frete": 3500.00,
                "sla_entrega_horas": 12,
                "raio_busca_km": 150,
                "top_k_despacho": 10
            }
        }
    
    @validator("id_carga")
    def id_carga_valido(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("ID da carga não pode ser vazio")
        return v.strip()




class ResultadoRastreamento(BaseModel):
    """Output do agente Rastreador (Tracker) com candidatos geospatiais."""
    
    id_carga: str = Field(..., description="ID da carga")
    ativos_candidatos: List[AtivoLogistico] = Field(
        ...,
        description="Lista de ativos logísticos candidatos (ordenados por eficiência)"
    )
    metodo_busca: str = Field(
        default="redis_geospatial",
        description="Método usado: redis_geospatial, fallback_cache, etc"
    )
    tempo_rastreamento_ms: float = Field(
        ...,
        ge=0,
        description="Tempo de rastreamento em millisegundos (alvo: <10ms)"
    )
    raio_busca_utilizado_km: float = Field(
        ...,
        description="Raio de busca utilizado em km"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id_carga": "CARGA-2026-001",
                "ativos_candidatos": [],
                "metodo_busca": "redis_geospatial",
                "tempo_rastreamento_ms": 8.5,
                "raio_busca_utilizado_km": 150
            }
        }


class CriterioValidacaoLogistica(BaseModel):
    """Critério individual de validação do Auditor P&L/Risco."""
    
    nome: str = Field(..., description="Nome do critério (GR, Margem, Malha, etc)")
    descricao: str = Field(..., description="Descrição do critério")
    passou: bool = Field(..., description="Resultado do critério")
    detalhes: Optional[str] = Field(None, description="Detalhes adicionais")
    confianca: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Nível de confiança da validação"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "nome": "Validação GR",
                "descricao": "Verifica se seguro está vigente",
                "passou": True,
                "detalhes": "GR vigente até 2026-06-30",
                "confianca": 1.0
            }
        }


class ResultadoAuditoria(BaseModel):
    """Output do Auditor P&L e Risco com decisão de despacho."""
    
    ativo_selecionado: AtivoLogistico = Field(
        ...,
        description="Ativo logístico selecionado para despacho"
    )
    status_despacho: StatusDespachoEnum = Field(
        ...,
        description="Status final: aprovado, bloqueado_gr, bloqueado_margem, etc"
    )
    criterios_validacao: List[CriterioValidacaoLogistica] = Field(
        ...,
        description="Critérios individuais validados"
    )
    
    # Métricas P&L
    valor_target_frete: float = Field(..., description="Valor alvo do frete")
    custo_variavel_estimado: float = Field(
        ...,
        gt=0,
        description="Custo variável estimado para a rota"
    )
    margem_contribuicao_reais: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Margem de contribuição em % (real calculada)"
    )
    margem_minima_viavel: float = Field(
        default=0.70,
        description="Margem mínima viável para aprovação"
    )
    
    # NDCG customizado para logística
    ndcg_target_price: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="NDCG customizado: aderência ao target price"
    )
    
    # Indicadores especiais
    esta_em_explorador_malha: bool = Field(
        default=False,
        description="Se aprovado via exploração de malha (15% novos)"
    )
    motivo_bloqueio: Optional[str] = Field(
        None,
        description="Motivo se foi bloqueado"
    )
    
    # Metadata e timestamps
    timestamp_auditoria: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp da auditoria"
    )
    tempo_auditoria_ms: float = Field(
        ...,
        ge=0,
        description="Tempo de auditoria em millisegundos (alvo: <20ms)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "ativo_selecionado": {},
                "status_despacho": "aprovado",
                "criterios_validacao": [],
                "valor_target_frete": 3500.00,
                "custo_variavel_estimado": 619.50,
                "margem_contribuicao_reais": 0.824,
                "ndcg_target_price": 0.964,
                "tempo_auditoria_ms": 12.7
            }
        }


class EstadoPipeline(BaseModel):
    """Estado da execução do pipeline de despacho Mobiis."""
    
    id_execucao: str = Field(..., description="ID único da execução")
    etapa: str = Field(
        ...,
        description="Etapa atual (rastreamento, auditoria, despacho_realizado, bloqueado)"
    )
    id_carga: str = Field(..., description="ID da carga")
    requisicao_carga: RequisicaoCarga = Field(..., description="Requisição de carga original")
    
    resultado_rastreamento: Optional[ResultadoRastreamento] = Field(
        None,
        description="Resultado da busca geospatial (Rastreador)"
    )
    resultado_auditoria: Optional[ResultadoAuditoria] = Field(
        None,
        description="Resultado da auditoria P&L (Auditor)"
    )
    
    tentativas_restantes: int = Field(
        default=3,
        ge=0,
        description="Tentativas restantes de retry"
    )
    historico_tentativas: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Histórico de tentativas anteriores"
    )
    
    tempo_inicio: datetime = Field(
        default_factory=datetime.utcnow,
        description="Tempo de início da execução"
    )
    tempo_fim: Optional[datetime] = Field(
        None,
        description="Tempo de término da execução"
    )
    
    # Rastreamento de latência
    latencia_total_ms: Optional[float] = Field(
        None,
        description="Latência total em millisegundos (alvo P99: <100ms)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id_execucao": "exec-despacho-2026-001",
                "etapa": "despacho_realizado",
                "id_carga": "CARGA-2026-001",
                "latencia_total_ms": 25.3
            }
        }


class RespostaDespacho(BaseModel):
    """Resposta final retornada ao sistema com despacho realizado."""
    
    id_carga: str = Field(..., description="ID da carga")
    ativo_despachado: AtivoLogistico = Field(
        ...,
        description="Ativo selecionado para o despacho"
    )
    valor_frete_final: float = Field(..., description="Valor final do frete em R$")
    margem_contribuicao: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Margem de contribuição (%)"
    )
    status_despacho: StatusDespachoEnum = Field(..., description="Status final do despacho")
    
    # Metadata e auditoria
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadados adicionais"
    )
    id_execucao: str = Field(..., description="ID da execução para auditoria")
    latencia_total_ms: float = Field(..., ge=0, description="Latência total em ms")
    
    # Tópicos Kafka para integração
    kafka_topic_publicado: str = Field(
        default="mobiis.despachos.aprovados",
        description="Tópico Kafka onde foi publicado"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id_carga": "CARGA-2026-001",
                "ativo_despachado": {},
                "valor_frete_final": 3500.00,
                "margem_contribuicao": 0.824,
                "status_despacho": "aprovado",
                "id_execucao": "exec-despacho-2026-001",
                "latencia_total_ms": 25.3
            }
        }


class ErroValidacao(BaseModel):
    """Modelo para erros durante validação."""
    
    codigo_erro: str = Field(..., description="Código do erro")
    mensagem: str = Field(..., description="Mensagem de erro legível")
    detalhes: Optional[Dict[str, Any]] = Field(
        None,
        description="Detalhes técnicos do erro"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp do erro"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "codigo_erro": "INVALID_CARGO_ID",
                "mensagem": "ID da carga não é válido",
                "detalhes": {"id_carga": "invalid"},
                "timestamp": "2026-01-21T15:30:00.000Z"
            }
        }
