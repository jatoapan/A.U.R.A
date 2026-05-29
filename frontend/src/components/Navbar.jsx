import React from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle } from 'lucide-react';

function Navbar() {
  return (
    <nav className="bg-white border-b border-slate-200 shadow-sm">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-xl font-bold text-blue-600">
          <AlertTriangle size={28} />
          A.U.R.A
        </Link>
        <p className="text-sm text-slate-600">Sistema de Detección de Fraude en Siniestros</p>
      </div>
    </nav>
  );
}

export default Navbar;
