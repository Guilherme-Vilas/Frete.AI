# 🚛 Engine de Despacho de Cargas de Alta Performance - Estilo Mobiis/Fretefy

![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)
![Latência](https://img.shields.io/badge/latência-P99%20%3C100ms-green.svg)
![Status](https://img.shields.io/badge/status-Production--Ready-brightgreen.svg)

Este sistema implementa um **Motor de Inteligência Logística** para a orquestração automatizada de ativos rodoviários em tempo real. Diferente de algoritmos de recomendação genéricos, esta solução foi projetada como uma **Engenharia de Decisão**, focada em maximizar a **Margem de Contribuição (P&L)** e garantir **Compliance de Risco**.

## 🎯 Visão Estratégica
O objetivo central é transformar o despacho de cargas — muitas vezes manual e lento — em uma operação instantânea, lucrativa e auditável. O sistema resolve o problema da "vaga ociosa" e do "vício de malha" através de agentes especializados que operam em milissegundos.

## 🏗️ Arquitetura do Sistema

O pipeline é orquestrado por dois componentes críticos que se equilibram entre performance e segurança:

### 1. **The Tracker (Rastreador Geo-Espacial)**
Responsável pela localização e priorização de ativos.
* **Busca Geo-Espacial:** Implementação inspirada em **Redis Geospatial** para localizar veículos próximos à origem da carga em menos de 10ms.
* **Ranking de Eficiência:** Utiliza uma função de custo/benefício que pondera distância, histórico de SLA do motorista e custo base do quilômetro.

### 2. **The Guard Dog (Auditor de P&L e Risco)**
A camada de governança que protege o resultado financeiro da operação.
* **Bloqueio de Seguro (GR):** Validação automática e rígida do Gerenciamento de Risco. Se o seguro está vencido, o ativo é descartado do ranking imediatamente, eliminando sinistros sem cobertura.
* **Exploração de Malha (15%):** Algoritmo de serendipidade que aloca 15% das cargas para novos motoristas. Isso evita que a operação fique refém de poucas transportadoras, mantendo o frete competitivo no longo prazo.
* **NDCG@Target_Price:** Métrica customizada para avaliar a aderência do despacho ao preço-alvo do embarcador, otimizando o lucro incremental.

## 📊 Performance & Engenharia
* **Latência:** Desenvolvido para atingir um P99 de **< 100ms** em produção.
* **Observabilidade:** Instrumentado com logs detalhados e pronto para integração com **LangSmith** para rastreio de decisões de agentes.
* **Escalabilidade:** Estrutura preparada para integração com **Kafka** (eventos de despacho) e **Redis Feature Store**.

## 🛠️ Stack Técnica
* **Linguagem:** Python 3.11 com tipagem estática.
* **Validação:** Pydantic V2 para garantir contratos de dados robustos entre sistemas.
* **Orquestração:** LangGraph para fluxos de agentes inteligentes.

## 🚀 Como Executar o Protótipo
```bash
# 1. Prepare o ambiente
python3.11 -m venv venv
source venv/bin/activate

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Rode o despacho simulado
python src/main.py
