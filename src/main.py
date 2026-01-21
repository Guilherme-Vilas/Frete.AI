"""
Ponto de entrada e exemplos de uso do Pipeline de Despacho Mobiis.

Demonstra como utilizar o sistema multi-agentes para despacho de cargas
com validação de GR, P&L e exploração de malha.

# TECH LEAD NOTE: Em produção, integrar com FastAPI ou similar
# para expor como REST API com documentação Swagger automática.
# Implementar rate limiting, autenticação e logging estruturado.
"""

import logging
import time
from typing import Optional

from config import (
    ConfiguradorLogging,
    ConfiguradorObservabilidade,
    UtilsValidacao,
    Constantes,
)
from pipeline import PipelineDespacho, ConfiguracaoPipeline
from schemas import (
    RespostaDespacho,
    RequisicaoCarga,
    GeoLocalizacao,
    TipoFrotaEnum,
)
from exceptions import RAGException
from datetime import datetime


def exemplo_basico() -> None:
    """
    Exemplo básico de uso do pipeline de despacho logístico.
    """
    # Configurar logging
    ConfiguradorLogging.configurar(
        nivel="INFO",
        arquivo="despacho.log",
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("Pipeline de Despacho Multi-Agentes Mobiis")
    logger.info("Sistema: Rastreador (Geo-Espacial) + Auditor P&L/Risco")
    logger.info("=" * 80)
    
    # Tentar configurar observabilidade
    if ConfiguradorObservabilidade.configurar_langsmith():
        logger.info("✓ LangSmith habilitado para observabilidade")
    
    if ConfiguradorObservabilidade.configurar_kafka():
        logger.info("✓ Kafka configurado para stream em tempo real")
    
    if ConfiguradorObservabilidade.configurar_redis_feature_store():
        logger.info("✓ Redis Geospatial configurado")
    
    # Logar configurações
    Constantes.log_configuracoes()
    
    # Criar pipeline com configuração padrão
    config = ConfiguracaoPipeline(
        max_tentativas_retry=3,
        timeout_segundos=0.1,
        margem_minima_viavel=0.70,
        cota_explorador_malha=0.15,
        dias_novo_motorista=30,
    )
    
    pipeline = PipelineDespacho(configuracao=config)
    
    # Exemplos de cargas e requisições de despacho
    cargas_exemplo = [
        {
            "id_carga": "CARGA-2026-001",
            "origem": GeoLocalizacao(
                latitude=-23.5505,
                longitude=-46.6333,
                zona_logistica="SP-Capital"
            ),
            "destino": GeoLocalizacao(
                latitude=-19.9191,
                longitude=-43.9386,
                zona_logistica="RJ-Rio"
            ),
            "peso_kg": 18000,
            "tipos_frota_aceitos": [TipoFrotaEnum.BITREM, TipoFrotaEnum.CARRETA],
            "target_price_frete": 3500.00,
            "sla_entrega_horas": 12,
            "raio_busca_km": 150,
            "top_k_despacho": 10,
        },
        {
            "id_carga": "CARGA-2026-002",
            "origem": GeoLocalizacao(
                latitude=-23.5505,
                longitude=-46.6333,
                zona_logistica="SP-Capital"
            ),
            "destino": GeoLocalizacao(
                latitude=-22.9068,
                longitude=-43.1729,
                zona_logistica="RJ-RioNiteroi"
            ),
            "peso_kg": 12000,
            "tipos_frota_aceitos": [TipoFrotaEnum.TRUCK, TipoFrotaEnum.CARRETA],
            "target_price_frete": 2500.00,
            "sla_entrega_horas": 8,
            "raio_busca_km": 120,
            "top_k_despacho": 8,
        },
        {
            "id_carga": "CARGA-2026-003",
            "origem": GeoLocalizacao(
                latitude=-23.5505,
                longitude=-46.6333,
                zona_logistica="SP-Capital"
            ),
            "destino": GeoLocalizacao(
                latitude=-23.1929,
                longitude=-45.8617,
                zona_logistica="SP-Litoral"
            ),
            "peso_kg": 15000,
            "tipos_frota_aceitos": [TipoFrotaEnum.BITREM],
            "target_price_frete": 2800.00,
            "sla_entrega_horas": 6,
            "raio_busca_km": 100,
            "top_k_despacho": 5,
        },
    ]
    
    logger.info(f"\nExecutando despachos para {len(cargas_exemplo)} cargas...\n")
    
    for idx, carga_config in enumerate(cargas_exemplo, 1):
        logger.info(f"{'=' * 80}")
        logger.info(f"Despacho {idx}/{len(cargas_exemplo)}")
        logger.info(f"{'=' * 80}")
        
        try:
            # Criar requisição de carga
            requisicao = RequisicaoCarga(**carga_config)
            
            logger.info(f"Carga: {requisicao.id_carga}")
            logger.info(f"Peso: {requisicao.peso_kg}kg")
            logger.info(f"Target Frete: R${requisicao.target_price_frete:.2f}")
            logger.info(f"SLA: {requisicao.sla_entrega_horas}h")
            logger.info(f"Raio busca: {requisicao.raio_busca_km}km\n")
            
            # Executar despacho
            tempo_execucao_inicio = time.time()
            resposta: RespostaDespacho = pipeline.executar(requisicao)
            tempo_execucao = time.time() - tempo_execucao_inicio
            
            # Log de resultado
            logger.info(f"\n{'─' * 80}")
            logger.info(f"RESULTADO DO DESPACHO")
            logger.info(f"{'─' * 80}")
            logger.info(f"Status: {resposta.status_despacho.value.upper()}")
            logger.info(f"Ativo: {resposta.ativo_despachado.id_placa}")
            logger.info(f"Motorista: {resposta.ativo_despachado.motorista_nome}")
            logger.info(f"Valor Frete: R${resposta.valor_frete_final:.2f}")
            logger.info(f"Margem: {resposta.margem_contribuicao:.2%}")
            logger.info(f"Novo Motorista: {resposta.metadata.get('novo_motorista', False)}")
            if resposta.metadata.get('ndcg_target_price'):
                logger.info(f"NDCG@Target_Price: {resposta.metadata.get('ndcg_target_price'):.3f}")
            if resposta.metadata.get('motivo_bloqueio'):
                logger.info(f"Motivo Bloqueio: {resposta.metadata.get('motivo_bloqueio')}")
            logger.info(f"Latência Total: {resposta.latencia_total_ms:.2f}ms")
            logger.info(f"Tempo Execução Python: {tempo_execucao*1000:.2f}ms")
            logger.info(f"ID Execução: {resposta.id_execucao}")
            logger.info(f"{'─' * 80}\n")
            
        except RAGException as e:
            logger.error(f"Erro RAG: {str(e)}\n")
        except Exception as e:
            logger.error(f"Erro ao executar despacho: {str(e)}\n")
    
    logger.info(f"\n{'=' * 80}")
    logger.info("Pipeline de Despacho concluído!")
    logger.info(f"{'=' * 80}")


if __name__ == "__main__":
    exemplo_basico()
