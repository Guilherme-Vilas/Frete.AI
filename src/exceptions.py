"""
Definição de exceções customizadas para o pipeline RAG.

Exceções específicas permitem tratamento granular de erros e
melhor observabilidade em ambiente regulado.
"""

from typing import Optional, Dict, Any


class RAGException(Exception):
    """Exceção base para todas as exceções do pipeline RAG."""
    
    def __init__(
        self,
        mensagem: str,
        codigo_erro: Optional[str] = None,
        detalhes: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.mensagem = mensagem
        self.codigo_erro = codigo_erro or self.__class__.__name__
        self.detalhes = detalhes or {}
        super().__init__(self.mensagem)


class RetrieverError(RAGException):
    """Erro durante execução do agente Retriever."""
    pass


class CheckerError(RAGException):
    """Erro durante execução do agente Checker."""
    pass


class ValidationException(RAGException):
    """Erro de validação de dados."""
    pass


class TimeoutError(RAGException):
    """Timeout durante operação."""
    pass


class GroundingFailureError(RAGException):
    """Falha na validação de grounding."""
    pass


class PipelineExecutionError(RAGException):
    """Erro geral na execução do pipeline."""
    pass
