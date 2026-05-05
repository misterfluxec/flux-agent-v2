import { FileSpreadsheet, Globe, Database, ShoppingBag, HardDrive, Cloud } from 'lucide-react';
import { SourceType } from '@/app/dashboard/centro-de-datos/types';

const SOURCES: { id: SourceType; label: string; icon: any; desc: string }[] = [
  { id: 'sheets', label: 'Google Sheets', icon: FileSpreadsheet, desc: 'Sync en tiempo real con Drive' },
  { id: 'office', label: 'Microsoft Excel', icon: Cloud, desc: 'OneDrive / SharePoint' },
  { id: 'local', label: 'Archivos Locales', icon: HardDrive, desc: 'CSV, Excel, PDF, TXT' },
  { id: 'database', label: 'Base de Datos', icon: Database, desc: 'PostgreSQL, MySQL, MongoDB' },
  { id: 'ecommerce', label: 'Tienda Virtual', icon: ShoppingBag, desc: 'Shopify, WooCommerce' },
  { id: 'web', label: 'Scraping Web', icon: Globe, desc: 'URL o Sitemap XML' }
];

export function StepSource({ onSelect }: { onSelect: (s: SourceType) => void }) {
  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">Selecciona la fuente de datos</h2>
        <p className="text-gray-400 text-sm mt-2">Elige desde dónde el agente extraerá su conocimiento inicial. Conecta tus datos de forma segura.</p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {SOURCES.map(src => (
          <button 
            key={src.id} 
            onClick={() => onSelect(src.id)}
            className="group relative flex items-start gap-4 p-5 rounded-2xl border border-gray-800/60 bg-black/40 backdrop-blur-md hover:border-indigo-500/50 hover:shadow-[0_0_20px_rgba(99,102,241,0.15)] transition-all duration-300 text-left overflow-hidden"
          >
            {/* Glow on hover */}
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/0 to-indigo-500/5 group-hover:opacity-100 opacity-0 transition-opacity duration-300" />
            
            <div className="relative z-10 p-3 bg-gray-800/80 rounded-xl group-hover:bg-indigo-500/20 group-hover:shadow-[0_0_15px_rgba(99,102,241,0.3)] transition-all duration-300">
              <src.icon className="w-6 h-6 text-gray-400 group-hover:text-indigo-400 transition-colors" />
            </div>
            
            <div className="relative z-10">
              <h3 className="font-semibold text-white group-hover:text-indigo-300 transition-colors">{src.label}</h3>
              <p className="text-xs text-gray-500 mt-1 leading-relaxed">{src.desc}</p>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
