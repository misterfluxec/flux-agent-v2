'use client';

import React from 'react';
import { FileText, Globe, Database } from 'lucide-react';

interface SourceOption {
  id: string;
  title: string;
  desc: string;
  icon: React.ElementType;
  disabled?: boolean;
}

export default function StepSourceSelector({ wizard }: { wizard: any }) {
  const { form } = wizard;
  const currentSource = form.watch('sourceType');

  const options: SourceOption[] = [
    { id: 'file', title: 'Archivo Estructurado', desc: 'Sube archivos CSV, Excel, PDF o TXT', icon: FileText },
    { id: 'web', title: 'Scraping Web', desc: 'Extrae contenido de una URL o Sitemap', icon: Globe },
    { id: 'database', title: 'Conexión a Base de Datos', desc: 'Conecta MySQL o PostgreSQL', icon: Database }
  ];

  return (
    <div className="flex-1 flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div className="space-y-2">
        <h3 className="text-xl font-medium text-foreground">Selecciona la fuente de datos</h3>
        <p className="text-sm text-muted-foreground">
          Elige desde dónde quieres que el agente extraiga su conocimiento inicial.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-1">
        {options.map((opt) => {
          const isSelected = currentSource === opt.id;
          const Icon = opt.icon;
          
          return (
            <div 
              key={opt.id}
              onClick={() => form.setValue('sourceType', opt.id)}
              className={`p-4 border rounded-xl flex items-start gap-4 transition-all duration-200 cursor-pointer hover:border-primary/50 bg-surface
                ${isSelected ? 'border-primary ring-1 ring-primary bg-primary/5' : 'border-border'}
              `}
            >
              <div className={`p-3 rounded-lg ${isSelected ? 'bg-primary text-primary-foreground' : 'bg-surface-2 text-muted-foreground'}`}>
                <Icon size={24} />
              </div>
              <div className="flex-1">
                <h4 className={`font-medium ${isSelected ? 'text-primary' : 'text-foreground'}`}>
                  {opt.title}
                </h4>
                <p className="text-sm text-muted-foreground mt-1">{opt.desc}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
