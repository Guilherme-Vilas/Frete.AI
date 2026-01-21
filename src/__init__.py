"""
Arquivo __init__.py para o pacote src.

Exporta componentes principais para uso fácil.
"""

from schemas import (
    DocumentoFonte,
    BuscaRetrieverInput,
    RespostaRetriever,
    RespostaChecker,
    EstadoPipeline,
    RespostaFinal,
    ErroValidacao,
    GradoConfiancaEnum,
)

from retriever import AgentRetriever, SimuladorRepositorioDocumental
from checker import AgentChecker, ValidadorGrounding
from pipeline import PipelineRAG, ConfiguracaoPipeline
from config import (
    ConfiguradorLogging,
    ConfiguradorObservabilidade,
    UtilsValidacao,
    PromptsPT,
    Constantes,
)
from exceptions import (
    RAGException,
    RetrieverError,
    CheckerError,
    ValidationException,
    TimeoutError,
    GroundingFailureError,
    PipelineExecutionError,
)

__version__ = "1.0.0"
__author__ = "Equipe de Sistemas Governamentais"

__all__ = [
    # Schemas
    "DocumentoFonte",
    "BuscaRetrieverInput",
    "RespostaRetriever",
    "RespostaChecker",
    "EstadoPipeline",
    "RespostaFinal",
    "ErroValidacao",
    "GradoConfiancaEnum",
    # Agentes
    "AgentRetriever",
    "AgentChecker",
    # Pipeline
    "PipelineRAG",
    "ConfiguracaoPipeline",
    # Configuração
    "ConfiguradorLogging",
    "ConfiguradorObservabilidade",
    "UtilsValidacao",
    "PromptsPT",
    "Constantes",
    # Exceções
    "RAGException",
    "RetrieverError",
    "CheckerError",
    "ValidationException",
    "TimeoutError",
    "GroundingFailureError",
    "PipelineExecutionError",
]
