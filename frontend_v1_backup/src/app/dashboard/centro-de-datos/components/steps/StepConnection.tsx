import { StepLocalUpload } from './StepLocalUpload';
import { StepRemoteConnection } from './StepRemoteConnection';
import { InfoCard } from '@/components/ui/InfoCard';

const SOURCE_INFO: Record<string, { title: string; desc: string; tip: string }> = {
  local: {
    title: 'Carga desde tu computador',
    desc: 'Sube tu inventario en CSV, Excel (.xlsx/.xls), PDF o TXT. Nuestro sistema analizará la estructura, detectará columnas automáticamente y convertirá tu catálogo en conocimiento vectorial para el agente.',
    tip: '💡 Asegúrate de que la primera fila contenga los nombres de las columnas (ej: Nombre, Precio, Stock).'
  },
  sheets: {
    title: 'Conexión con Google Sheets',
    desc: 'Sincroniza tu hoja de cálculo de Google Drive en tiempo real. El agente aprenderá directamente de tu fuente oficial sin duplicar datos.',
    tip: '🔒 Solo se solicita permiso de lectura. Tus credenciales se cifran y nunca se almacenan en texto plano.'
  },
  office: {
    title: 'Conexión con Microsoft Excel / OneDrive',
    desc: 'Vincula archivos .xlsx de tu nube corporativa. Ideal para empresas que gestionan inventarios en entornos Microsoft 365.',
    tip: '📁 Se requiere cuenta Microsoft activa con permisos de lectura en el archivo seleccionado.'
  },
  database: {
    title: 'Conexión a Base de Datos',
    desc: 'Conecta directamente a PostgreSQL, MySQL o MongoDB. El agente consultará tu base de datos en vivo para respuestas precisas.',
    tip: '🛡️ Usa credenciales de solo lectura. Recomendamos crear un usuario dedicado para Yanua.'
  }
};

export function StepConnection({ 
  sourceType, 
  onDataLoaded, 
  onBack 
}: { 
  sourceType: string; 
  onDataLoaded: (data: { headers: string[]; rows: any[] }) => void; 
  onBack: () => void;
}) {
  const info = SOURCE_INFO[sourceType] || SOURCE_INFO.local;

  return (
    <div className="space-y-6">
      <InfoCard title={info.title} description={info.desc} tip={info.tip} />
      
      {sourceType === 'local' ? (
        <StepLocalUpload onDataLoaded={onDataLoaded} onBack={onBack} />
      ) : (
        <StepRemoteConnection sourceType={sourceType} onDataLoaded={onDataLoaded} onBack={onBack} />
      )}
    </div>
  );
}
