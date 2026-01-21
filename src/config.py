"""
Configuração e utilitários para o pipeline de Recomendação Mobiis.

Centraliza gerenciamento de configurações, logging, métricas e integração
com ferramentas de observabilidade e infraestrutura (Feature Store, Kafka).
"""

import logging
import sys
import os
from typing import Optional
from dotenv import load_dotenv


# Carregar variáveis de ambiente
load_dotenv()


class ConfiguradorLogging:
    """Configura logging estruturado para o pipeline de recomendação."""
    
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @staticmethod
    def configurar(
        nivel: str = "INFO",
        arquivo: Optional[str] = None,
    ) -> None:
        """
        Configura logging para todo o aplicativo.
        
        Args:
            nivel: Nível de logging (DEBUG, INFO, WARNING, ERROR)
            arquivo: Arquivo para salvar logs (opcional)
        """
        nivel_enum = getattr(logging, nivel.upper(), logging.INFO)
        
        # Handler console
        handler_console = logging.StreamHandler(sys.stdout)
        handler_console.setLevel(nivel_enum)
        formatter = logging.Formatter(ConfiguradorLogging.LOG_FORMAT)
        handler_console.setFormatter(formatter)
        
        # Configurar logger raiz
        logger_raiz = logging.getLogger()
        logger_raiz.setLevel(nivel_enum)
        logger_raiz.addHandler(handler_console)
        
        # Handler arquivo (se especificado)
        if arquivo:
            handler_arquivo = logging.FileHandler(arquivo)
            handler_arquivo.setLevel(nivel_enum)
            handler_arquivo.setFormatter(formatter)
            logger_raiz.addHandler(handler_arquivo)
    
    @staticmethod
    def criar_logger(nome: str) -> logging.Logger:
        """
        Cria logger para um módulo específico.
        
        Args:
            nome: Nome do módulo (__name__)
            
        Returns:
            Logger configurado
        """
        return logging.getLogger(nome)


class ConfiguradorObservabilidade:
    """
    Configura integração com LangSmith e OpenTelemetry para observabilidade.
    
    # TECH LEAD NOTE: Infraestrutura de observabilidade para Mobiis:
    # - LangSmith para rastreamento de agentes
    # - OpenTelemetry para métricas distribuídas (P50/P95/P99)
    # - Prometheus para coleta de métricas
    # - Grafana para visualização
    # - Jaeger para distributed tracing
    """
    
    @staticmethod
    def configurar_langsmith() -> bool:
        """
        Configura LangSmith para rastreamento de execuções.
        
        # TECH LEAD NOTE: Em produção, usar traces customizados
        # para acompanhar latência de cada etapa (Candidate Gen, Diversity Audit)
        
        Returns:
            True se configurado com sucesso
        """
        api_key = os.getenv("LANGSMITH_API_KEY")
        projeto = os.getenv("LANGSMITH_PROJECT", "mobiis-recomendacao")
        ativar = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
        
        if not ativar:
            logging.info("LangSmith desativado")
            return False
        
        if not api_key:
            logging.warning("LANGSMITH_API_KEY não configurada")
            return False
        
        try:
            os.environ["LANGSMITH_API_KEY"] = api_key
            os.environ["LANGSMITH_PROJECT"] = projeto
            os.environ["LANGSMITH_TRACING"] = "true"
            
            logging.info(f"LangSmith configurado: projeto={projeto}")
            return True
            
        except Exception as e:
            logging.error(f"Erro ao configurar LangSmith: {str(e)}")
            return False
    
    @staticmethod
    def configurar_kafka() -> Optional[str]:
        """
        Configura integração com Kafka para stream em tempo real.
        
        # TECH LEAD NOTE: Arquitetura Kafka para Mobiis:
        # - Topic: mobiis.recommendations.generated
        #   Evento: Candidates gerados com timestamp e latência
        # - Topic: mobiis.recommendations.audited
        #   Evento: Recomendações após auditoria de diversidade
        # - Consumer Group: recomendacao-service
        #   Subscribers: Analytics, Real-time Dashboard, A/B Testing
        
        Returns:
            URL do broker Kafka ou None
        """
        kafka_url = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
        if not kafka_url:
            logging.warning("KAFKA_BOOTSTRAP_SERVERS não configurada")
            return None
        
        logging.info(f"Kafka configurado: {kafka_url}")
        return kafka_url
    
    @staticmethod
    def configurar_redis_feature_store() -> Optional[str]:
        """
        Configura Redis como Feature Store para cache.
        
        # TECH LEAD NOTE: Redis Feature Store para Mobiis:
        # - user:{user_id}:history → Histórico e preferências
        # - product:{sku}:embedding → Cache de embeddings de produtos
        # - session:{session_id}:candidates → Cache de candidatos gerados
        # - Política: TTL 1h para histórico, 24h para embeddings
        
        Returns:
            URL do Redis ou None
        """
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            logging.warning("REDIS_URL não configurada")
            return None
        
        logging.info(f"Redis Feature Store configurado: {redis_url}")
        return redis_url


class ConfiguradorOpenAI:
    """Configura client OpenAI para futuro com LLMs."""
    
    @staticmethod
    def obter_api_key() -> str:
        """
        Obtém API key do OpenAI.
        
        Args:
            None
            
        Returns:
            API key
            
        Raises:
            ValueError: Se API key não estiver configurada
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logging.warning("OPENAI_API_KEY não configurada")
            return ""
        return api_key


class UtilsValidacao:
    """Utilitários para validação de entrada."""
    
    @staticmethod
    def validar_usuario_id(usuario_id: str) -> None:
        """
        Valida ID do usuário.
        
        Args:
            usuario_id: ID do usuário a validar
            
        Raises:
            ValueError: Se ID inválido
        """
        if not usuario_id or len(usuario_id.strip()) == 0:
            raise ValueError("Usuario ID não pode ser vazio")
        
        if len(usuario_id) > 256:
            raise ValueError("Usuario ID muito longo (máx: 256 caracteres)")
        
        # Validar formato (deve ser alphanummérico com _ - permitidos)
        if not all(c.isalnum() or c in "_-" for c in usuario_id):
            raise ValueError("Usuario ID contém caracteres inválidos")


# Configurações de Recomendação
class ConfiguracaoRecomendacao:
    """Configurações específicas do motor de recomendação."""
    
    # Candidate Generation
    TOP_K_PADRAO = 10
    TOP_K_MINIMO = 5
    TOP_K_MAXIMO = 100
    
    THRESHOLD_SIMILARIDADE = 0.5
    THRESHOLD_SERENDIPIDADE_MINIMA = 0.15  # 15%
    ALVO_SERENDIPIDADE = 0.20  # 20% é o alvo
    THRESHOLD_SERENDIPIDADE_MAXIMA = 0.25  # 25%
    
    # Diversidade & Ethics Audit
    THRESHOLD_CONFIANCA_GLOBAL = 0.8
    THRESHOLD_VIES_MAXIMO = 0.5  # Max 50% de uma categoria
    THRESHOLD_COBERTURA_PRECO_MINIMO = 2  # Mínimo 2 faixas
    
    # Performance
    LATENCIA_TARGET_MS = 150  # Alvo: <150ms
    LATENCIA_WARNING_MS = 120  # Alerta: >120ms
    LATENCIA_CRITICO_MS = 130  # Crítico: >130ms


# Prompts em Português Brasileiro
class PromptsMobiis:
    """Prompts para sistema Mobiis."""
    
    DESCRICAO_CANDIDATE_GENERATOR = """
    Sistema de Candidate Generation para Recomendação Mobiis.
    
    Responsabilidades:
    - Analisar histórico do usuário (visualizações, compras)
    - Calcular similaridade Content-Based com histórico
    - Gerar candidatos rankeados por relevância
    - Incluir fator de serendipidade (exploração)
    
    Alvo de latência: <150ms para geração de 10 candidatos.
    """
    
    DESCRICAO_DIVERSITY_AUDITOR = """
    Auditor de Diversidade e Ética para Recomendações Mobiis.
    
    Critérios de Validação:
    1. Viés de Categoria: Evitar concentração >50% em uma categoria
    2. Serendipidade: Garantir 20% de exploração (±5%)
    3. Cobertura de Preço: Mínimo 2 faixas de preço diferentes
    
    Métricas Calculadas:
    - NDCG@k: Qualidade do ranking
    - Diversidade de Categorias: Cobertura (0-1)
    - Taxa de Serendipidade: % de produtos exploratórios
    
    Alvo: Todas as recomendações devem passar na auditoria.
    """


# Constantes e Configurações
class Constantes:
    """Constantes do aplicativo Mobiis."""
    
    # Limites de timeout (em segundos)
    TIMEOUT_CANDIDATE_GEN = 10.0  # Candidate Generation
    TIMEOUT_DIVERSITY_AUDIT = 5.0  # Diversity Audit
    TIMEOUT_TOTAL = 30.0  # Total do pipeline
    
    # Limites de produtos
    MAX_CANDIDATOS = 100
    TOP_K_PADRAO = 10
    
    # Thresholds de métrica
    NDCG_MINIMO = 0.7  # NDCG@10 deve ser ≥0.7
    DIVERSIDADE_MINIMA = 0.4  # Mínimo 40% de diversidade
    
    # Configuração de ambiente
    AMBIENTE = os.getenv("AMBIENTE", "development")
    DEBUG_MODE = AMBIENTE != "production"
    
    # Feature Store e Kafka
    USAR_REDIS_CACHE = os.getenv("USAR_REDIS_CACHE", "true").lower() == "true"
    USAR_KAFKA_STREAM = os.getenv("USAR_KAFKA_STREAM", "false").lower() == "true"
    
    # TECH LEAD NOTE: Configurações de integração em produção:
    # - Redis: Cache de embeddings e histórico (TTL: 1h)
    # - Kafka: Stream de eventos de recomendação
    # - Elasticsearch: Busca de produtos por atributos
    # - PostgreSQL + pgvector: Storage de embeddings
    
    @staticmethod
    def log_configuracoes() -> None:
        """Log de configurações ativas."""
        logger = logging.getLogger(__name__)
        logger.info(f"Ambiente: {Constantes.AMBIENTE}")
        logger.info(f"Debug: {Constantes.DEBUG_MODE}")
        logger.info(f"Redis Cache: {Constantes.USAR_REDIS_CACHE}")
        logger.info(f"Kafka Stream: {Constantes.USAR_KAFKA_STREAM}")
        logger.info(f"Latência Target: {ConfiguracaoRecomendacao.LATENCIA_TARGET_MS}ms")

