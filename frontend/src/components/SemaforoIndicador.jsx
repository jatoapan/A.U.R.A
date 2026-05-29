import React from 'react';

function SemaforoIndicador({ semaforo }) {
  const config = {
    VERDE: {
      bg: 'bg-green-100',
      text: 'text-green-800',
      badge: 'badge-success',
    },
    AMARILLO: {
      bg: 'bg-yellow-100',
      text: 'text-yellow-800',
      badge: 'badge-warning',
    },
    ROJO: {
      bg: 'bg-red-100',
      text: 'text-red-800',
      badge: 'badge-danger',
    },
  };

  const cfg = config[semaforo] || config.VERDE;

  return (
    <div className={`${cfg.badge} px-3 py-1`}>
      {semaforo}
    </div>
  );
}

export default SemaforoIndicador;
