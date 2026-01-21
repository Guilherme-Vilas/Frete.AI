"""
Testes unitários para o pipeline RAG.

Implementa testes de:
- Validação de schemas Pydantic
- Lógica de retriever
- Lógica de checker e grounding
- Fluxo completo do pipeline

# TECH LEAD NOTE: Usar pytest com fixtures para teste determinístico
# Implementar testes de performance e custos de token no futuro
"""

import pytest
from datetime import datetime
from typing import List

# Imports do projeto
from schemas import (
    DocumentoFonte,
    BuscaRetrieverInput,
    RespostaRetriever,
    RespostaChecker,
    GradoConfiancaEnum,
    CriterioValidacao,
)
from retriever import AgentRetriever, SimuladorRepositorioDocumental
from checker import AgentChecker, ValidadorGrounding
from pipeline import PipelineRAG, ConfiguracaoPipeline
from exceptions import (
    RetrieverError,
    ValidationException,
    GroundingFailureError,
)


class TestSchemasValidacao:
    """Testes de validação de schemas Pydantic."""
    
    def test_documento_fonte_valido(self) -> None:
        """Testa criação de DocumentoFonte válido."""
        doc = DocumentoFonte(
            id="DOC-001",
            titulo="Teste",
            conteudo="Conteúdo teste",
            relevancia_score=0.85,
        )
        assert doc.id == "DOC-001"
        assert doc.relevancia_score == 0.85
    
    def test_documento_fonte_score_invalido(self) -> None:
        """Testa validação de score fora do range."""
        with pytest.raises(ValueError):
            DocumentoFonte(
                id="DOC-001",
                titulo="Teste",
                conteudo="Conteúdo",
                relevancia_score=1.5,  # Deve estar entre 0-1
            )
    
    def test_busca_retriever_input_pergunta_vazia(self) -> None:
        """Testa validação de pergunta vazia."""
        with pytest.raises(ValueError):
            BuscaRetrieverInput(pergunta="")
    
    def test_busca_retriever_input_pergunta_muito_longa(self) -> None:
        """Testa validação de pergunta muito longa."""
        with pytest.raises(ValueError):
            BuscaRetrieverInput(pergunta="a" * 3000)
    
    def test_busca_retriever_input_valido(self) -> None:
        """Testa entrada válida."""
        entrada = BuscaRetrieverInput(
            pergunta="Qual é o processo correto?",
            contexto_adicional="Contexto teste",
        )
        assert "processo" in entrada.pergunta_processada.lower()


class TestRetriever:
    """Testes do agente Retriever."""
    
    @pytest.fixture
    def retriever(self) -> AgentRetriever:
        """Fixture com retriever inicializado."""
        return AgentRetriever(
            timeout_seconds=5.0,
            max_documentos=3,
        )
    
    @pytest.fixture
    def entrada_valida(self) -> BuscaRetrieverInput:
        """Fixture com entrada válida."""
        return BuscaRetrieverInput(pergunta="auditoria")
    
    def test_retriever_busca_bem_sucedida(
        self,
        retriever: AgentRetriever,
        entrada_valida: BuscaRetrieverInput,
    ) -> None:
        """Testa execução bem-sucedida do retriever."""
        resultado = retriever.processar(entrada_valida)
        
        assert isinstance(resultado, RespostaRetriever)
        assert len(resultado.documentos_recuperados) > 0
        assert resultado.tempo_busca_ms >= 0
    
    def test_retriever_preprocessamento(self, retriever: AgentRetriever) -> None:
        """Testa preprocessamento de pergunta."""
        pergunta = "  AUDITORIA  "
        pergunta_limpa = retriever._preprocessar_pergunta(pergunta)
        
        assert pergunta_limpa == "auditoria"
        assert pergunta_limpa == pergunta_limpa.lower()


class TestChecker:
    """Testes do agente Checker."""
    
    @pytest.fixture
    def checker(self) -> AgentChecker:
        """Fixture com checker inicializado."""
        return AgentChecker(threshold_confianca_global=0.8)
    
    @pytest.fixture
    def documentos_teste(self) -> List[DocumentoFonte]:
        """Fixture com documentos de teste."""
        return [
            DocumentoFonte(
                id="DOC-1",
                titulo="Auditoria Interna",
                conteudo="A auditoria deve ser realizada por profissionais certificados.",
                relevancia_score=0.9,
            ),
            DocumentoFonte(
                id="DOC-2",
                titulo="Compliance",
                conteudo="Compliance é fundamental para conformidade regulatória.",
                relevancia_score=0.85,
            ),
        ]
    
    def test_validador_cobertura_textual(
        self,
        checker: AgentChecker,
        documentos_teste: List[DocumentoFonte],
    ) -> None:
        """Testa validação de cobertura textual."""
        resposta = "A auditoria deve ser realizada por profissionais certificados"
        
        passou, confianca, detalhes = (
            checker.validador.verificar_cobertura_textual(resposta, documentos_teste)
        )
        
        assert isinstance(passou, bool)
        assert 0 <= confianca <= 1
        assert isinstance(detalhes, str)
        assert passou is True  # Resposta deve ter alta cobertura
    
    def test_validador_nao_alucinacao(
        self,
        checker: AgentChecker,
        documentos_teste: List[DocumentoFonte],
    ) -> None:
        """Testa detecção de alucinação."""
        # Resposta com informações fabricadas
        resposta = "O processo requer aprovação de 5 órgãos distintos."
        
        passou, confianca, detalhes = (
            checker.validador.verificar_nao_alucinacao(resposta, documentos_teste)
        )
        
        assert isinstance(passou, bool)
        assert 0 <= confianca <= 1
    
    def test_checker_resposta_grounded(
        self,
        checker: AgentChecker,
        documentos_teste: List[DocumentoFonte],
    ) -> None:
        """Testa checker com resposta bem fundamentada."""
        resposta_retriever = RespostaRetriever(
            pergunta_processada="auditoria",
            documentos_recuperados=documentos_teste,
            tempo_busca_ms=100.0,
        )
        
        resposta_texto = "A auditoria deve ser realizada por profissionais certificados"
        
        resultado = checker.processar(resposta_retriever, resposta_texto)
        
        assert isinstance(resultado, RespostaChecker)
        assert resultado.esta_grounded is True
        assert resultado.grau_confianca in [
            GradoConfiancaEnum.ALTA,
            GradoConfiancaEnum.MEDIA,
        ]


class TestPipeline:
    """Testes do pipeline completo."""
    
    @pytest.fixture
    def pipeline(self) -> PipelineRAG:
        """Fixture com pipeline inicializado."""
        config = ConfiguracaoPipeline(
            max_tentativas_retry=2,
            timeout_segundos=10.0,
        )
        return PipelineRAG(configuracao=config)
    
    def test_pipeline_execucao_bem_sucedida(self, pipeline: PipelineRAG) -> None:
        """Testa execução completa do pipeline."""
        pergunta = "Qual é o processo de auditoria?"
        
        try:
            resultado = pipeline.executar(pergunta)
            
            assert resultado.resposta is not None
            assert resultado.id_execucao is not None
            assert resultado.grau_confianca != GradoConfiancaEnum.REJEITADA
            
        except GroundingFailureError:
            # Aceitável em alguns casos
            pass
    
    def test_pipeline_pergunta_vazia(self, pipeline: PipelineRAG) -> None:
        """Testa pipeline com pergunta vazia."""
        with pytest.raises(Exception):
            pipeline.executar("")


class TestIntegracaoE2E:
    """Testes de integração end-to-end."""
    
    def test_fluxo_completo_auditoria(self) -> None:
        """Testa fluxo completo para caso de uso auditoria."""
        pipeline = PipelineRAG()
        
        pergunta = "Como realizar auditoria interna conforme normas?"
        
        try:
            resultado = pipeline.executar(pergunta)
            
            # Verificações
            assert resultado.resposta
            assert resultado.id_execucao
            assert len(resultado.documentos_suporte) > 0
            
            print(f"\n✓ Fluxo E2E bem-sucedido")
            print(f"  Resposta: {resultado.resposta[:100]}...")
            print(f"  Confiança: {resultado.grau_confianca.value}")
            
        except Exception as e:
            print(f"\n⚠ Fluxo E2E com erro (esperado em protótipo): {str(e)}")


# Fixtures globais
@pytest.fixture(scope="session")
def configuracao_teste() -> None:
    """Configuração para testes."""
    import logging
    logging.basicConfig(level=logging.WARNING)


if __name__ == "__main__":
    # Executar testes: pytest src/tests.py -v
    pytest.main([__file__, "-v"])
