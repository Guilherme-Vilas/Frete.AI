"""
API FastAPI para o Sistema de Despacho Mobiis
Integra o frontend Next.js com o pipeline Python de análise de cargas
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import logging
from datetime import datetime
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pipeline import PipelineDespacho, ConfiguracaoPipeline
from schemas import RequisicaoCarga, GeoLocalizacao, TipoFrotaEnum
from config import ConfiguradorLogging

# Configurar logging
ConfiguradorLogging.configurar(
    nivel="INFO",
    arquivo="api.log",
)
logger = logging.getLogger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title="Frete.AI - Engine de Despacho",
    description="API para análise e despacho inteligente de cargas",
    version="1.0.0"
)

# Configurar CORS para aceitar requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://192.168.3.19:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de Request/Response
class CargaRequest(BaseModel):
    origem: str = Field(..., description="Origem da carga (ex: São Paulo, SP)")
    destino: str = Field(..., description="Destino da carga (ex: Rio de Janeiro, RJ)")
    peso: float = Field(..., gt=0, description="Peso em kg")
    valor: float = Field(..., gt=0, description="Valor do frete em R$")
    tipo_freta: Optional[str] = Field("Truck", description="Tipo de frota")

class CargaResponse(BaseModel):
    id: str
    origem: str
    destino: str
    peso: str
    valor: str
    status: str
    analise: Optional[dict] = None
    motorista_recomendado: Optional[str] = None
    margem: Optional[str] = None
    ranking_score: Optional[float] = None

class SaudeResponse(BaseModel):
    status: str
    timestamp: str
    versao: str

# Inicializar pipeline
pipeline = PipelineDespacho(ConfiguracaoPipeline())
contador_cargas = 0

@app.on_event("startup")
async def startup():
    logger.info("✓ API iniciada com sucesso")
    logger.info(f"CORS configurado para: localhost:3000, localhost:3001")

@app.get("/", response_model=SaudeResponse)
async def raiz():
    """Health check da API"""
    return {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "versao": "1.0.0"
    }

@app.get("/saude", response_model=SaudeResponse)
async def saude():
    """Status da API e pipeline"""
    return {
        "status": "operacional",
        "timestamp": datetime.now().isoformat(),
        "versao": "1.0.0"
    }

@app.post("/cargas/analisar", response_model=CargaResponse)
async def analisar_carga(carga: CargaRequest) -> CargaResponse:
    """
    Analisa uma carga usando o pipeline de despacho.
    
    - **origem**: Origem da carga
    - **destino**: Destino da carga
    - **peso**: Peso em kg
    - **valor**: Valor do frete em R$
    - **tipo_freta**: Tipo de frota (Truck, Carreta, Bitrem)
    
    Retorna: Análise completa da carga com recomendações
    """
    try:
        global contador_cargas
        contador_cargas += 1
        
        logger.info(f"Analisando carga #{contador_cargas}: {carga.origem} → {carga.destino}")
        
        # Preparar requisição para o pipeline
        requisicao = RequisicaoCarga(
            id_carga=f"CARGA-2026-{str(contador_cargas).zfill(3)}",
            origem=carga.origem,
            destino=carga.destino,
            peso_kg=carga.peso,
            target_price=carga.valor,
            tipo_freta=carga.tipo_freta or "Truck"
        )
        
        # Executar pipeline
        resultado = pipeline.executar(requisicao)
        
        logger.info(f"✓ Carga analisada: {resultado.decisao_final}")
        
        # Mapear status
        status_map = {
            "APROVADA": "Aprovada",
            "REJEITADA": "Rejeitada",
            "PENDENTE": "Pendente"
        }
        
        status = status_map.get(resultado.decisao_final, "Pendente")
        
        # Extrair informações de margem
        margem_str = "0%"
        if hasattr(resultado, 'score_margem'):
            margem_str = f"{resultado.score_margem:.1f}%"
        
        return CargaResponse(
            id=requisicao.id_carga,
            origem=carga.origem,
            destino=carga.destino,
            peso=f"{carga.peso} kg",
            valor=f"R$ {carga.valor:.2f}",
            status=status,
            analise={
                "decisao": resultado.decisao_final,
                "tempo_processamento_ms": resultado.tempo_processamento_ms,
                "motorista_recomendado": getattr(resultado, 'motorista_recomendado', 'Não disponível'),
                "detalhes_p_l": getattr(resultado, 'detalhes_pl', {}),
            },
            motorista_recomendado=getattr(resultado, 'motorista_recomendado', None),
            margem=margem_str,
            ranking_score=getattr(resultado, 'score_ranking', None)
        )
        
    except Exception as e:
        logger.error(f"Erro ao analisar carga: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar carga: {str(e)}"
        )

@app.post("/cargas", response_model=CargaResponse)
async def criar_carga(carga: CargaRequest) -> CargaResponse:
    """
    Cria e analisa uma nova carga.
    Atalho para /cargas/analisar
    """
    return await analisar_carga(carga)

@app.get("/info")
async def info():
    """Informações sobre a API e o pipeline"""
    return {
        "nome": "Frete.AI - Engine de Despacho de Cargas",
        "versao": "1.0.0",
        "descricao": "Sistema inteligente de despacho com análise de P&L, validação de GR e exploração de malha",
        "modulos": {
            "rastreador": "Busca geo-espacial com Redis Geospatial",
            "auditor": "Validação de P&L, margem e risco",
            "explorador": "Exploração de malha para novos motoristas"
        },
        "endpoints": {
            "saude": "GET /saude",
            "analisar_carga": "POST /cargas/analisar",
            "criar_carga": "POST /cargas",
            "info": "GET /info"
        }
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Iniciando servidor FastAPI...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True
    )
