import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AlertCircle } from 'lucide-react';

import Navbar from './components/Navbar';
import ListadoSiniestros from './pages/ListadoSiniestros';
import DetalleSiniestro from './pages/DetalleSiniestro';
import { siniestrosAPI } from './api/client';

import './index.css';

function App() {
  const [apiReady, setApiReady] = useState(false);
  const [apiError, setApiError] = useState(null);

  useEffect(() => {
    // Verificar que el backend esté listo
    const checkAPI = async () => {
      try {
        const response = await siniestrosAPI.health();
        setApiReady(response.data.models_loaded);
        if (!response.data.models_loaded) {
          setApiError('⚠️ Modelos no cargados. Ejecuta: python scripts/train_fraud_model.py');
        }
      } catch (error) {
        setApiError('❌ No se puede conectar con el backend en http://localhost:8000');
        console.error(error);
      }
    };

    checkAPI();
  }, []);

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-50">
        <Navbar />

        {!apiReady && (
          <div className="mx-auto max-w-2xl mt-8 p-4">
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex gap-3">
              <AlertCircle className="text-yellow-600 flex-shrink-0" />
              <div className="text-yellow-800">
                <p className="font-semibold">API Backend no disponible</p>
                <p className="text-sm mt-1">{apiError}</p>
                <p className="text-sm mt-2">
                  Pasos:
                  <br />
                  1. Terminal: <code className="bg-yellow-100 px-2 py-1">python scripts/train_fraud_model.py</code>
                  <br />
                  2. Luego: <code className="bg-yellow-100 px-2 py-1">uvicorn src.api.main:app --reload --port 8000</code>
                </p>
              </div>
            </div>
          </div>
        )}

        {apiReady && (
          <Routes>
            <Route path="/" element={<ListadoSiniestros />} />
            <Route path="/siniestro/:id" element={<DetalleSiniestro />} />
          </Routes>
        )}
      </div>
    </BrowserRouter>
  );
}

export default App;
