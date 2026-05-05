import { useState, useRef } from 'react';
import { UploadCloud, FileText, AlertCircle, Loader2, CheckCircle } from 'lucide-react';
import { api } from '@/lib/api';

const ALLOWED_TYPES = ['text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/pdf', 'text/plain'];
const MAX_SIZE_MB = 50;

export function StepLocalUpload({ onDataLoaded, onBack }: { onDataLoaded: (data: any) => void; onBack: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'parsing' | 'success' | 'error'>('idle');
  const [error, setError] = useState<string>('');
  const [preview, setPreview] = useState<{ headers: string[]; rows: any[] } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (selected: File) => {
    if (!ALLOWED_TYPES.includes(selected.type) && !selected.name.match(/\.(csv|xlsx|xls|pdf|txt)$/i)) {
      setError('Formato no soportado. Usa CSV, Excel, PDF o TXT.');
      return;
    }
    if (selected.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`El archivo es muy grande. Máximo ${MAX_SIZE_MB}MB.`);
      return;
    }
    setFile(selected);
    setError('');
    setStatus('idle');
  };

  const handleUpload = async () => {
    if (!file) return;
    setStatus('uploading');
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const res = await api.post('/upload/parse', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      const data = res.data;
      setPreview({
        headers: data.headers,
        rows: data.preview_rows
      });
      setStatus('success');
    } catch (err: any) {
      setStatus('error');
      setError(err.response?.data?.detail || 'Error al procesar el archivo. Verifica el formato.');
    }
  };

  const handleContinue = () => {
    if (preview) onDataLoaded(preview);
  };

  return (
    <div className="space-y-5">
      {/* Zona de Carga */}
      <div 
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition ${
          status === 'success' ? 'border-green-500/50 bg-green-500/5' : 'border-gray-700 hover:border-blue-500/50 hover:bg-blue-500/5'
        }`}
      >
        <input 
          ref={fileInputRef} 
          type="file" 
          className="hidden" 
          accept=".csv,.xlsx,.xls,.pdf,.txt"
          onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
        />
        
        {status === 'idle' && !file && (
          <div className="space-y-3">
            <UploadCloud className="w-10 h-10 text-gray-500 mx-auto" />
            <p className="text-sm font-medium text-gray-300">Arrastra tu archivo aquí o haz clic para seleccionar</p>
            <p className="text-xs text-gray-500">CSV, Excel, PDF o TXT • Máx {MAX_SIZE_MB}MB</p>
          </div>
        )}

        {file && status !== 'success' && (
          <div className="space-y-3">
            <FileText className="w-8 h-8 text-blue-400 mx-auto" />
            <p className="text-sm font-medium text-white truncate max-w-xs mx-auto">{file.name}</p>
            <p className="text-xs text-gray-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
            <button 
              onClick={(e) => { e.stopPropagation(); handleUpload(); }}
              disabled={status === 'uploading' || status === 'parsing'}
              className="mt-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 text-white text-sm font-medium rounded-lg transition flex items-center gap-2 mx-auto"
            >
              {status === 'uploading' || status === 'parsing' ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Procesando...</>
              ) : 'Analizar Estructura'}
            </button>
          </div>
        )}

        {status === 'success' && preview && (
          <div className="space-y-3">
            <CheckCircle className="w-8 h-8 text-green-400 mx-auto" />
            <p className="text-sm font-medium text-green-400">Archivo analizado correctamente</p>
            <p className="text-xs text-gray-500">{preview.rows.length} filas detectadas • {preview.headers.length} columnas</p>
          </div>
        )}
      </div>

      {error && (
        <div className="flex items-start gap-2 text-red-400 bg-red-500/10 p-3 rounded-lg text-xs border border-red-500/20">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          {error}
        </div>
      )}

      {/* Preview de Datos */}
      {status === 'success' && preview && (
        <div className="bg-[#111111] rounded-xl border border-gray-800 overflow-hidden">
          <div className="px-4 py-3 bg-gray-800/50 border-b border-gray-800">
            <p className="text-xs font-medium text-gray-400">Vista previa de estructura</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="bg-gray-900/50">
                <tr>{preview.headers.map(h => <th key={h} className="px-4 py-2 text-left font-medium text-gray-400">{h}</th>)}</tr>
              </thead>
              <tbody>
                {preview.rows.map((row, i) => (
                  <tr key={i} className="border-t border-gray-800">
                    {preview.headers.map(h => <td key={h} className="px-4 py-2 text-gray-300">{row[h]}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Navegación */}
      <div className="flex justify-end gap-3 pt-4 border-t border-gray-800">
        <button onClick={onBack} className="px-4 py-2 text-sm text-gray-400 hover:text-white transition">Atrás</button>
        <button 
          onClick={handleContinue} 
          disabled={status !== 'success'}
          className="px-6 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 disabled:text-gray-600 disabled:cursor-not-allowed rounded-lg text-sm font-medium transition"
        >
          Continuar al Mapeo
        </button>
      </div>
    </div>
  );
}
