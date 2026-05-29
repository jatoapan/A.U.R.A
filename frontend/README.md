# A.U.R.A Frontend

Frontend React con Vite para el sistema de detección de fraude en siniestros.

## Instalación

```bash
cd frontend
npm install
npm run dev
```

## Build para producción

```bash
npm run build
npm run preview
```

## Estructura

```
src/
├── pages/           # Páginas (ListadoSiniestros, DetalleSiniestro)
├── components/      # Componentes reutilizables
├── api/            # Cliente HTTP (axios)
├── App.jsx         # App principal
└── index.css       # Tailwind + estilos globales
```

## Variables de entorno

Crear `.env` en la raíz del frontend:

```env
REACT_APP_API_URL=http://localhost:8000
```

## API esperada

El backend debe estar corriendo en `http://localhost:8000` con los endpoints:

- `GET /health` - Health check
- `GET /siniestros` - Listar siniestros
- `GET /siniestros/{id}` - Detalle
- `POST /siniestros/{id}/score` - Calcular score
- `POST /siniestros/score-all` - Batch scoring
- `POST /siniestros/{id}/chat` - Chat
