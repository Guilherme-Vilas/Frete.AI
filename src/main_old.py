"""
Ponto de entrada e exemplos de uso do Pipeline de Recomendação Mobiis.

Demonstra como utilizar o sistema multi-agentes para recomendação
com validação de diversidade e ética.

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
    ConfiguracaoRecomendacao,
)
from pipeline import PipelineRecomendacao, ConfiguracaoPipeline
from schemas import RespostaFinal, HistoricoUsuario
from exceptions import RAGException


def exemplo_basico() -> None:
    """
    Exemplo básico de uso do pipeline de recomendação.
    """
    # Configurar logging
    ConfiguradorLogging.configurar(
        nivel="INFO",
        arquivo="recomendacao.log",
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("Pipeline de Recomendação Multi-Agentes Mobiis")
    logger.info("Sistema: Candidate Generation + Diversity & Ethics Auditor")
    logger.info("=" * 80)
    
    # Tentar configurar observabilidade
    if ConfiguradorObservabilidade.configurar_langsmith():
        logger.info("✓ LangSmith habilitado para observabilidade")
    
    if ConfiguradorObservabilidade.configurar_kafka():
        logger.info("✓ Kafka configurado para stream em tempo real")
    
    if ConfiguradorObservabilidade.configurar_redis_feature_store():
        logger.info("✓ Redis Feature Store configurado")
    
    # Logar configurações
    Constantes.log_configuracoes()
    
    # Criar pipeline com configuração padrão
    config = ConfiguracaoPipeline(
        max_tentativas_retry=2,
        timeout_segundos=30.0,
        threshold_confianca_checker=0.8,
    )
    
    pipeline = PipelineRecomendacao(configuracao=config)
    
    # Exemplos de usuários e históricos
    usuarios_exemplo = [
        {
            "usuario_id": "USER-001",
            "historico": HistoricoUsuario(
                usuario_id="USER-001",
                produtos_visualizados=["SKU-ELEC-001", "SKU-LIVR-001"],
                produtos_comprados=["SKU-ELEC-001"],
                categorias_preferidas=["Eletrônicos", "Livros"],
            ),
            "top_k": 10,
        },
        {
            "usuario_id": "USER-002",
            "historico": HistoricoUsuario(
                usuario_id="USER-002",
                produtos_visualizados=["SKU-CASA-001"],
                produtos_comprados=[],
                categorias_preferidas=["Casa Inteligente"],
            ),
            "top_k": 8,
        },
        {
            "usuario_id": "USER-003",
            "historico": None,  # Novo usuário, sem histórico
            "top_k": 10,
        },
    ]
    
    logger.info(f"\nExecutando recomendações para {len(usuarios_exemplo)} usuários...\n")
    
    for idx, usuario_config in enumerate(usuarios_exemplo, 1):
        logger.info(f"{'=' * 80}")
        logger.info(f"Recomendação {idx}/{len(usuarios_exemplo)}")
        logger.info(f"{'=' * 80}")
        
        try:
            usuario_id = usuario_config["usuario_id"]
            historico = usuario_config["historico"]
            top_k = usuario_config["top_k"]
            
            logger.info(f"Usuário: {usuario_id}")
            logger.info(f"Top-K: {top_k}")
            if historico:
                logger.info(f"Produtos Visualizados: {len(historico.produtos_visualizados)}")
                logger.info(f"Categorias Preferidas: {historico.categorias_preferidas}\n")
            else:
                logger.info("Status: Novo usuário (cold start)\n")
            
            # Executar pipeline
            tempo_inicio = time.time()
            resultado = pipeline.executar(usuario_id, historico, top_k)
            tempo_total = (time.time() - tempo_inicio) * 1000  # ms
            
            # Verificar latência
            if tempo_total > ConfiguracaoRecomendacao.LATENCIA_CRITICO_MS:
                logger.error(f"⚠️  LATÊNCIA CRÍTICA: {tempo_total:.2f}ms (alvo: <{ConfiguracaoRecomendacao.LATENCIA_TARGET_MS}ms)")
            elif tempo_total > ConfiguracaoRecomendacao.LATENCIA_WARNING_MS:
                logger.warning(f"⚠️  Latência elevada: {tempo_total:.2f}ms")
            else:
                logger.info(f"✓ Latência OK: {tempo_total:.2f}ms")
            
            # Exibir resultado
            exibir_resultado(resultado, logger, tempo_total)
            
        except RAGException as e:
            logger.error(f"✗ Erro no pipeline: {e.mensagem}")
            logger.error(f"  Código: {e.codigo_erro}")
            if e.detalhes:
                logger.error(f"  Detalhes: {e.detalhes}")
        except Exception as e:
            logger.error(f"✗ Erro inesperado: {str(e)}")
        
        logger.info("\n")


def exibir_resultado(resultado: RespostaFinal, logger: logging.Logger, latencia_ms: float) -> None:
    """
    Exibe resultado formatado da execução.
    
    Args:
        resultado: RespostaFinal do pipeline
        logger: Logger para output
        latencia_ms: Latência total em millisegundos
    """
    logger.info("✓ Pipeline executado com sucesso\n")
    
    logger.info("-" * 80)
    logger.info("RECOMENDAÇÕES GERADAS")
    logger.info("-" * 80)
    logger.info(f"Total de Produtos: {len(resultado.produtos)}\n")
    
    for idx, produto in enumerate(resultado.produtos, 1):
        logger.info(f"{idx}. {produto.nome}")
        logger.info(f"   SKU: {produto.id}")
        logger.info(f"   Categoria: {produto.categoria}")
        logger.info(f"   Preço: R$ {produto.preco:.2f}")
        logger.info(f"   Similaridade: {produto.similaridade_score:.2%}")
        if produto.tags:
            logger.info(f"   Tags: {', '.join(produto.tags)}")
        logger.info("")
    
    logger.info("-" * 80)
    logger.info("MÉTRICAS DE QUALIDADE")
    logger.info("-" * 80)
    logger.info(f"Relevância: {resultado.relevancia.value.upper()}\n")
    
    logger.info(f"NDCG@10: {resultado.ndcg_at_k:.3f} (alvo: ≥0.70)")
    logger.info(f"Diversidade Categorias: {resultado.diversidade_categorias:.1%}")
    logger.info(f"Serendipidade: {resultado.percentual_serendipidade:.1%} (alvo: 20%)")
    logger.info(f"\nLatência Total: {latencia_ms:.2f}ms (alvo: <{ConfiguracaoRecomendacao.LATENCIA_TARGET_MS}ms)")
    
    logger.info(f"\nID Execução: {resultado.id_execucao}")
    
    logger.info("-" * 80 + "\n")


def exemplo_com_metricas() -> None:
    """
    Exemplo demonstrando log detalhado de métricas.
    
    # TECH LEAD NOTE: Em produção, essas métricas seriam enviadas
    # para Prometheus/Grafana para monitoramento em tempo real.
    """
    ConfiguradorLogging.configurar(nivel="INFO")
    logger = logging.getLogger(__name__)
    
    logger.info("Exemplo: Rastreamento de Métricas\n")
    logger.info("Métricas enviadas:")
    logger.info("  - mobiis.latencia_candidate_gen_ms (histogram)")
    logger.info("  - mobiis.latencia_diversity_audit_ms (histogram)")
    logger.info("  - mobiis.ndcg_at_10 (gauge)")
    logger.info("  - mobiis.diversidade_categorias (gauge)")
    logger.info("  - mobiis.serendipidade (gauge)")
    logger.info("  - mobiis.recomendacoes_total (counter)")
    logger.info("  - mobiis.recomendacoes_rejeitadas (counter)\n")
    
    logger.info("Eventos publicados em Kafka:")
    logger.info("  - Topic: mobiis.recommendations.generated")
    logger.info("    Payload: {usuario_id, num_candidatos, latencia_ms}")
    logger.info("  - Topic: mobiis.recommendations.audited")
    logger.info("    Payload: {usuario_id, ndcg_at_k, diversidade, serendipidade}\n")


def exemplo_cold_start() -> None:
    """
    Exemplo demonstrando recomendação para usuário novo (cold start).
    
    # TECH LEAD NOTE: Estratégia de cold start:
    # 1. Sem histórico: usar produtos populares + exploração
    # 2. Primeira compra: usar atributos de produtos já comprados
    # 3. Feedback explícito: usar preferências informadas
    """
    ConfiguradorLogging.configurar(nivel="INFO")
    logger = logging.getLogger(__name__)
    
    logger.info("Exemplo: Cold Start (Novo Usuário)\n")
    logger.info("Estratégia:")
    logger.info("  1. Produtos populares (baseado em trending)")
    logger.info("  2. Mix de categorias (diversidade forçada)")
    logger.info("  3. Aleatoriedade controlada (serendipidade 30%)\n")
    
    logger.info("Abordagem:")
    logger.info("  - Sem histórico: usar trending + content-based genérico")
    logger.info("  - Com 1ª compra: usar similaridade com aquele item")
    logger.info("  - Com feedback: reestimar preferências\n")


if __name__ == "__main__":
    # Executar exemplo principal
    exemplo_basico()
    
    # Exemplos adicionais
    # exemplo_com_metricas()
    # exemplo_cold_start()



def exemplo_integracao_api() -> None:
    """
    Exemplo de integração como API REST.
    
    # TODO: Implementar com FastAPI
    # TODO: Adicionar autenticação OAuth2
    # TODO: Adicionar rate limiting
    # TODO: Adicionar CORS para ambiente seguro
    """
    exemplo_fastapi = '''
# main.py - API REST do Pipeline RAG
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pipeline import PipelineRAG

app = FastAPI(
    title="API RAG Governamental",
    description="Pipeline RAG para ambientes regulados",
    version="1.0.0"
)

pipeline = PipelineRAG()

class PerguntaRequest(BaseModel):
    pergunta: str
    contexto: Optional[str] = None

class RespostaAPI(BaseModel):
    resposta: str
    confianca: str
    id_execucao: str

@app.post("/api/v1/consulta")
async def consultar(request: PerguntaRequest) -> RespostaAPI:
    """Consulta o pipeline RAG."""
    try:
        resultado = pipeline.executar(request.pergunta)
        return RespostaAPI(
            resposta=resultado.resposta,
            confianca=resultado.grau_confianca.value,
            id_execucao=resultado.id_execucao
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Executar: uvicorn main:app --reload
'''
    
    ConfiguradorLogging.configurar()
    logger = logging.getLogger(__name__)
    logger.info("Exemplo de integração API REST:")
    logger.info(exemplo_fastapi)


if __name__ == "__main__":
    # Executar exemplo básico
    exemplo_basico()
    
    # Executar testes de erro
    # exemplo_com_erro()
    
    # Exemplo de integração
    # exemplo_integracao_api()
