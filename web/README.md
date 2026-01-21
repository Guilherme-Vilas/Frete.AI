# Frete.ai - Interface Web

Interface moderna e responsiva para o engine de despacho de cargas **Frete.ai**.

## 🎨 Design & Features

- **Tema**: Gradiente azul + branco
- **Framework**: Next.js 15 + React 19
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Responsivo**: Mobile-first design

## 📦 Instalação

```bash
# Instalar dependências
npm install

# Desenvolvimento
npm run dev

# Build para produção
npm run build

# Iniciar produção
npm start
```

## 🚀 Acesso

- **Dev**: http://localhost:3000
- **Dashboard**: Home page com estatísticas em tempo real
- **Cargas**: Gerenciamento de cargas/despachos
- **Motoristas**: Rede de motoristas e performance
- **Histórico**: Timeline completo de operações

## 📁 Estrutura

```
web/
├── app/                 # Páginas (Next.js App Router)
│   ├── layout.tsx      # Layout global
│   ├── page.tsx        # Home (Dashboard)
│   ├── cargas/         # Página de cargas
│   ├── motoristas/     # Página de motoristas
│   └── historico/      # Página de histórico
├── components/         # Componentes React reutilizáveis
│   ├── Navigation.tsx
│   ├── Dashboard.tsx
│   ├── StatCard.tsx
│   └── DispatchCard.tsx
├── public/            # Assets estáticos
└── globals.css        # Estilos globais
```

## 🎯 Cores

- **Primária**: Azul (#0284c7 - #0369a1)
- **Secundária**: Branco (#ffffff)
- **Destaque**: Gradiente azul 135°
- **Sucesso**: Verde (#10b981)
- **Erro**: Vermelho (#ef4444)

## ✨ Componentes Principais

### StatCard
Card de estatística com ícone e mudança percentual.

### DispatchCard
Card de despacho com origem, destino, motorista e status.

### Navigation
Barra de navegação sticky com menu responsivo.

## 🔗 Integração API

Para conectar com a API backend:

```typescript
// Exemplo
const response = await fetch('http://localhost:8000/despachos');
const data = await response.json();
```

## 📱 Responsividade

- **Mobile**: < 640px (1 coluna)
- **Tablet**: 640px - 1024px (2 colunas)
- **Desktop**: > 1024px (3+ colunas)

## 🚀 Deploy

Pronto para deploy em:
- Vercel
- Netlify
- AWS
- Docker

```bash
# Docker
docker build -t frete-ai-web .
docker run -p 3000:3000 frete-ai-web
```

## 📝 Licença

Parte do projeto Frete.ai - 2026
