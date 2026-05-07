'use client';

import React, { useState } from 'react';
import { Search, ThumbsUp, ThumbsDown, Loader2 } from 'lucide-react';

export default function StepValidation({ wizard, tenantId }: { wizard: any, tenantId: string }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setHasSearched(true);
    
    try {
      const apiUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:9000';
      const token = localStorage.getItem('flux_token');
      
      const res = await fetch(`${apiUrl}/api/v1/ingest/test-search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
          'X-Tenant-ID': tenantId
        },
        body: JSON.stringify({ query, match_count: 3 })
      });

      if (!res.ok) throw new Error('Error en búsqueda');
      const data = await res.json();
      
      // Manejar el placeholder del backend o resultados reales
      if (data.message) {
        setResults([{ content: data.message, similarity: 1 }]);
      } else {
        setResults(data.results || []);
      }
    } catch (error) {
      console.error(error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div className="space-y-2 text-center">
        <h3 className="text-xl font-medium text-foreground">Verifica el Conocimiento</h3>
        <p className="text-sm text-muted-foreground max-w-md mx-auto">
          Haz una pregunta de prueba para verificar que el agente recupera correctamente la información que acabas de subir.
        </p>
      </div>

      <form onSubmit={handleSearch} className="relative max-w-xl mx-auto w-full">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search size={18} className="text-muted-foreground" />
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ej: ¿Cuál es el precio del producto X?"
          className="w-full bg-surface-2 border border-border rounded-full py-3 pl-10 pr-24 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary shadow-sm"
        />
        <button 
          type="submit" 
          disabled={loading || !query.trim()}
          className="absolute right-1.5 top-1.5 bottom-1.5 px-4 bg-primary text-primary-foreground rounded-full text-sm font-medium hover:bg-primary-hover disabled:opacity-50 transition-colors flex items-center gap-2"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : 'Probar'}
        </button>
      </form>

      {hasSearched && (
        <div className="mt-6 space-y-4 max-w-2xl mx-auto w-full">
          <h4 className="text-sm font-medium text-muted-foreground border-b border-border pb-2">
            Resultados Recuperados (RAG)
          </h4>
          
          {loading ? (
            <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
              <Loader2 size={24} className="animate-spin mb-2" />
              <p className="text-sm">Buscando similitudes...</p>
            </div>
          ) : results.length > 0 ? (
            <div className="space-y-3">
              {results.map((res, idx) => (
                <div key={idx} className="bg-surface-2 border border-border p-4 rounded-lg text-sm relative group">
                  <div className="text-foreground whitespace-pre-wrap">{res.content}</div>
                  <div className="mt-3 flex items-center justify-between">
                    <span className="text-xs text-muted-foreground bg-surface px-2 py-1 rounded-md border border-border">
                      Similitud: {(res.similarity * 100).toFixed(1)}%
                    </span>
                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button className="p-1.5 hover:bg-surface rounded-md text-muted-foreground hover:text-success transition-colors" title="Buen resultado">
                        <ThumbsUp size={14} />
                      </button>
                      <button className="p-1.5 hover:bg-surface rounded-md text-muted-foreground hover:text-error transition-colors" title="Mal resultado">
                        <ThumbsDown size={14} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground bg-surface-2 rounded-lg border border-border border-dashed">
              <p className="text-sm">No se encontraron fragmentos relevantes para esta consulta.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
