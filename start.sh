#!/bin/bash
# Script para arrancar A.U.R.A (Backend + Frontend) en desarrollo

echo "🚀 A.U.R.A - Iniciando sistema completo..."
echo ""

# Colores para terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Validar requisitos
echo "📋 Verificando requisitos..."

if ! command -v python &> /dev/null; then
    echo -e "${RED}✗ Python no encontrado${NC}"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js no encontrado${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python OK${NC}"
echo -e "${GREEN}✓ Node.js OK${NC}"
echo ""

# Paso 1: Entrenar modelos (si no existen)
echo "📊 Verificando modelos ML..."
if [ ! -f "data/processed/fraud_lr.joblib" ]; then
    echo -e "${YELLOW}⚠️ Modelos no encontrados, entrenando...${NC}"
    echo "Ejecuta en una terminal:"
    echo "  python scripts/export_supabase_to_csv.py"
    echo "  python scripts/train_fraud_model.py"
    echo ""
    echo "Después vuelve aquí y presiona Enter..."
    read
else
    echo -e "${GREEN}✓ Modelos encontrados${NC}"
fi
echo ""

# Paso 2: Backend
echo "🔧 Preparando Backend..."
echo "Abre una terminal Y ejecuta:"
echo -e "${YELLOW}uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000${NC}"
echo ""
echo "Presiona Enter cuando veas 'Uvicorn running on http://0.0.0.0:8000'..."
read
echo ""

# Paso 3: Frontend
echo "⚛️  Preparando Frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Instalando dependencias npm...${NC}"
    npm install
fi

echo -e "${GREEN}✓ Frontend listo${NC}"
echo ""

echo "🎉 ¡LISTO PARA ARRANCAR!"
echo ""
echo "Abre UNA NUEVA TERMINAL en la carpeta 'frontend' y ejecuta:"
echo -e "${YELLOW}npm run dev${NC}"
echo ""
echo "Luego abre: http://localhost:3000"
echo ""
echo "Backend:   http://localhost:8000"
echo "Backend API Docs: http://localhost:8000/docs"
echo ""
