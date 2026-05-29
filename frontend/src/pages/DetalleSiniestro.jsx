import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, RefreshCw, Send, AlertCircle } from 'lucide-react';

import { siniestrosAPI } from '../api/client';
import SemaforoIndicador from '../components/SemaforoIndicador';
import ScoreBar from '../components/ScoreBar';

function DetalleSiniestro() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [siniestro, setSiniestro] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [scoring, setScoring] = useState(false);

  // Chat
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  // Cargar detalle
  useEffect(() => {
    loadSiniestro();
  }, [id]);

  const loadSiniestro = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await siniestrosAPI.get(id);
      setSiniestro(response.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleScore = async () => {
    setScoring(true);
    try {
      const response = await siniestrosAPI.score(id);
      setSiniestro((prev) => ({
        ...prev,
        score_riesgo: response.data.score_final,
        semaforo_alerta: response.data.semaforo,
        explicacion_riesgo: response.data.explicacion,
        ml_proba: response.data.ml_proba,
        score_reglas: response.data.score_reglas,
        ml_alerta: response.data.ml_alerta,
      }));
    } catch (err) {
      setError(`Error scoring: ${err.message}`);
    } finally {
      setScoring(false);
    }
  };

  const handleChatSend = async () => {
    if (!chatInput.trim()) return;

    // Agregar mensaje del usuario
    const newMessages = [
      ...chatMessages,
      { role: 'user', content: chatInput },
    ];
    setChatMessages(newMessages);
    setChatInput('');
    setChatLoading(true);

    try {
      const response = await siniestrosAPI.chat(id, newMessages);
      // Agregar respuesta del asistente
      setChatMessages((prev) => [
        ...prev,
        { role: 'assistant', content: response.data.reply },
      ]);
    } catch (err) {
      setChatMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Error: ${err.message}` },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center text-slate-600">Cargando...</div>
      </div>
    );
  }

  if (!siniestro) {
    return (
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center text-slate-600">Siniestro no encontrado</div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <button
          onClick={() => navigate('/')}
          className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
        >
          <ArrowLeft size={24} />
        </button>
        <div>
          <h1 className="text-3xl font-bold text-slate-900">{siniestro.codigo_siniestro}</h1>
          <p className="text-slate-600">ID: {siniestro.id_siniestro}</p>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex gap-3 mb-6">
          <AlertCircle className="text-red-600 flex-shrink-0" />
          <div className="text-red-800">{error}</div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Columna Izquierda - Info Principal */}
        <div className="lg:col-span-2 space-y-6">
          {/* Resumen */}
          <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
            <h2 className="text-lg font-semibold mb-4">Información General</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-slate-600">Cobertura</p>
                <p className="font-semibold text-slate-900">{siniestro.cobertura}</p>
              </div>
              <div>
                <p className="text-sm text-slate-600">Sucursal</p>
                <p className="font-semibold text-slate-900">{siniestro.sucursal}</p>
              </div>
              <div>
                <p className="text-sm text-slate-600">Monto Reclamado</p>
                <p className="font-semibold text-slate-900">${siniestro.monto_reclamado.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-sm text-slate-600">Estado</p>
                <p className="font-semibold text-slate-900">{siniestro.estado_tramite}</p>
              </div>
            </div>
          </div>

          {/* Score y Análisis */}
          <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold">Análisis de Riesgo</h2>
              <button
                onClick={handleScore}
                disabled={scoring}
                className="btn btn-secondary flex items-center gap-2"
              >
                <RefreshCw size={16} />
                {scoring ? 'Calculando...' : 'Recalcular'}
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-slate-600">Score General</p>
                  <SemaforoIndicador semaforo={siniestro.semaforo_alerta} />
                </div>
                <ScoreBar score={siniestro.score_riesgo} />
              </div>

              <div className="pt-4 border-t border-slate-200">
                <h3 className="font-semibold text-sm mb-3">Desglose de Puntuación</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-slate-50 p-3 rounded-lg">
                    <p className="text-xs text-slate-600 mb-1">Reglas (hasta 70)</p>
                    <p className="text-xl font-bold">{siniestro.score_reglas || 0}</p>
                  </div>
                  <div className="bg-slate-50 p-3 rounded-lg">
                    <p className="text-xs text-slate-600 mb-1">ML Probabilidad</p>
                    <p className="text-xl font-bold">{(siniestro.ml_proba * 100).toFixed(1)}%</p>
                  </div>
                  <div className="bg-slate-50 p-3 rounded-lg">
                    <p className="text-xs text-slate-600 mb-1">Alerta ML</p>
                    <p className="text-xl font-bold">{siniestro.ml_alerta ? '✓ SÍ' : '✗ NO'}</p>
                  </div>
                </div>
              </div>

              {siniestro.explicacion_riesgo && (
                <div className="pt-4 border-t border-slate-200">
                  <h3 className="font-semibold text-sm mb-2">Explicación</h3>
                  <p className="text-sm text-slate-700 bg-slate-50 p-3 rounded-lg leading-relaxed">
                    {siniestro.explicacion_riesgo}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Narrativa */}
          {siniestro.descripcion_narrativa && (
            <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
              <h2 className="text-lg font-semibold mb-4">Descripción del Siniestro</h2>
              <p className="text-slate-700 leading-relaxed">{siniestro.descripcion_narrativa}</p>
            </div>
          )}
        </div>

        {/* Columna Derecha - Chat */}
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6 flex flex-col h-fit">
          <h2 className="text-lg font-semibold mb-4">Asistente A.U.R.A</h2>

          {/* Chat Messages */}
          <div className="flex-1 space-y-3 mb-4 max-h-96 overflow-y-auto">
            {chatMessages.length === 0 && (
              <div className="text-center text-slate-400 text-sm">
                Haz una pregunta sobre este siniestro...
              </div>
            )}

            {chatMessages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-xs px-3 py-2 rounded-lg text-sm ${
                    msg.role === 'user'
                      ? 'bg-blue-500 text-white'
                      : 'bg-slate-100 text-slate-900'
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}

            {chatLoading && (
              <div className="flex justify-start">
                <div className="bg-slate-100 text-slate-900 px-3 py-2 rounded-lg text-sm">
                  Pensando...
                </div>
              </div>
            )}
          </div>

          {/* Chat Input */}
          <div className="flex gap-2">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleChatSend()}
              placeholder="Pregunta..."
              disabled={chatLoading}
              className="flex-1 px-3 py-2 border border-slate-300 rounded-lg text-sm"
            />
            <button
              onClick={handleChatSend}
              disabled={chatLoading || !chatInput.trim()}
              className="btn btn-primary"
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DetalleSiniestro;
