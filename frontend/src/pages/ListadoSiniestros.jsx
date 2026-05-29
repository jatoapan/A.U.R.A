import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Search, Filter, RefreshCw, AlertCircle } from 'lucide-react';

import { siniestrosAPI } from '../api/client';
import SemaforoIndicador from '../components/SemaforoIndicador';
import ScoreBar from '../components/ScoreBar';

function ListadoSiniestros() {
  const [siniestros, setSiniestros] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filtros
  const [filters, setFilters] = useState({
    semaforo: '',
    min_score: '',
    cobertura: '',
    limit: 50,
    offset: 0,
  });

  // Scoring en progreso
  const [scoreAllLoading, setScoreAllLoading] = useState(false);
  const [scoreAllSuccess, setScoreAllSuccess] = useState(false);

  // Cargar siniestros
  useEffect(() => {
    loadSiniestros();
  }, [filters]);

  const loadSiniestros = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        limit: filters.limit,
        offset: filters.offset,
      };
      if (filters.semaforo) params.semaforo = filters.semaforo;
      if (filters.min_score) params.min_score = parseInt(filters.min_score);
      if (filters.cobertura) params.cobertura = filters.cobertura;

      const response = await siniestrosAPI.list(params);
      setSiniestros(response.data.items);
      setTotal(response.data.total);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters((prev) => ({
      ...prev,
      [name]: value,
      offset: 0, // Reset pagination
    }));
  };

  const handleScoreAll = async () => {
    setScoreAllLoading(true);
    try {
      const response = await siniestrosAPI.scoreAll();
      setScoreAllSuccess(true);
      // Recargar lista
      await loadSiniestros();
      setTimeout(() => setScoreAllSuccess(false), 5000);
    } catch (err) {
      setError(`Error en scoring batch: ${err.message}`);
    } finally {
      setScoreAllLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900">Siniestros</h1>
        <p className="text-slate-600 mt-2">Análisis de riesgo de fraude</p>
      </div>

      {/* Alertas */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex gap-3 mb-6">
          <AlertCircle className="text-red-600 flex-shrink-0" />
          <div className="text-red-800">{error}</div>
        </div>
      )}

      {scoreAllSuccess && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex gap-3 mb-6">
          <AlertCircle className="text-green-600 flex-shrink-0" />
          <div className="text-green-800">✓ Scoring completado exitosamente</div>
        </div>
      )}

      {/* Filtros */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Filter size={20} />
          <h2 className="font-semibold">Filtros</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Semáforo</label>
            <select
              name="semaforo"
              value={filters.semaforo}
              onChange={handleFilterChange}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
            >
              <option value="">Todos</option>
              <option value="VERDE">VERDE</option>
              <option value="AMARILLO">AMARILLO</option>
              <option value="ROJO">ROJO</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Score mínimo</label>
            <input
              type="number"
              name="min_score"
              min="0"
              max="100"
              value={filters.min_score}
              onChange={handleFilterChange}
              placeholder="0"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Cobertura</label>
            <select
              name="cobertura"
              value={filters.cobertura}
              onChange={handleFilterChange}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
            >
              <option value="">Todas</option>
              <option value="CHOQUE">CHOQUE</option>
              <option value="ROBO">ROBO</option>
              <option value="DAÑOS">DAÑOS</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={handleScoreAll}
              disabled={scoreAllLoading}
              className="btn btn-primary w-full flex items-center justify-center gap-2"
            >
              <RefreshCw size={16} />
              {scoreAllLoading ? 'Procesando...' : 'Recalcular todo'}
            </button>
          </div>
        </div>
      </div>

      {/* Tabla */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-600">Cargando...</div>
        ) : siniestros.length === 0 ? (
          <div className="p-12 text-center text-slate-600">No hay siniestros que coincidan con los filtros</div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50">
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 uppercase">Código</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 uppercase">Cobertura</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 uppercase">Monto</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 uppercase">Score</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 uppercase">Semáforo</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 uppercase">Acción</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {siniestros.map((sin) => (
                    <tr key={sin.id_siniestro} className="hover:bg-slate-50 transition-colors">
                      <td className="px-6 py-4 text-sm font-medium text-slate-900">{sin.codigo_siniestro}</td>
                      <td className="px-6 py-4 text-sm text-slate-600">{sin.cobertura}</td>
                      <td className="px-6 py-4 text-sm text-slate-600">${sin.monto_reclamado.toLocaleString()}</td>
                      <td className="px-6 py-4 text-sm">
                        <div className="flex items-center gap-2">
                          <div className="w-24">
                            <ScoreBar score={sin.score_riesgo} />
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <SemaforoIndicador semaforo={sin.semaforo_alerta} />
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <Link
                          to={`/siniestro/${sin.id_siniestro}`}
                          className="text-blue-600 hover:text-blue-800 font-medium"
                        >
                          Ver detalle →
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination info */}
            <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 text-sm text-slate-600">
              Mostrando {filters.offset + 1}-
              {Math.min(filters.offset + filters.limit, total)} de {total} siniestros
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default ListadoSiniestros;
