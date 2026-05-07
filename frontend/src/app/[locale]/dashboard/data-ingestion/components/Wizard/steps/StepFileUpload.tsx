'use client';

import React, { useRef } from 'react';
import { UploadCloud, Link as LinkIcon, AlertCircle } from 'lucide-react';

export default function StepFileUpload({ wizard }: { wizard: any }) {
  const { form } = wizard;
  const sourceType = form.watch('sourceType');
  const fileRef = useRef<HTMLInputElement>(null);

  const [isDragging, setIsDragging] = React.useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      form.setValue('file', e.target.files[0], { shouldValidate: true });
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      form.setValue('file', e.dataTransfer.files[0], { shouldValidate: true });
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (bytes === undefined || bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const currentFile = form.watch('file');
  const fileError = form.formState.errors.file;
  const urlError = form.formState.errors.url;

  return (
    <div className="flex-1 flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div className="space-y-2">
        <h3 className="text-xl font-medium text-foreground">
          {sourceType === 'file' ? 'Cargar Archivo' : 'URL de Origen'}
        </h3>
        <p className="text-sm text-muted-foreground">
          {sourceType === 'file' 
            ? 'Sube tu catálogo en formato CSV o Excel para alimentar al agente.' 
            : 'Ingresa la URL pública de donde el agente extraerá la información.'}
        </p>
      </div>

      {sourceType === 'file' && (
        <div className="space-y-4">
          <div 
            onClick={() => fileRef.current?.click()}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center gap-4 cursor-pointer transition-colors
              ${isDragging ? 'border-primary bg-primary/5' : fileError ? 'border-error bg-error/5' : 'border-border hover:border-primary/50 bg-surface-2'}
            `}
          >
            <input 
              type="file" 
              ref={fileRef} 
              className="hidden" 
              accept=".csv,.xlsx,.xls,.pdf,.txt"
              onChange={handleFileChange} 
            />
            <div className={`p-4 rounded-full shadow-sm transition-colors ${isDragging ? 'bg-primary/20 text-primary' : 'bg-surface text-primary'}`}>
              <UploadCloud size={32} />
            </div>
            <div className="text-center">
              <p className="font-medium text-foreground">
                {currentFile ? currentFile.name : (isDragging ? 'Suelta el archivo aquí' : 'Haz clic o arrastra un archivo aquí')}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                {currentFile ? formatFileSize(currentFile.size) : 'Soporta .csv, .xlsx, .pdf, .txt hasta 50MB'}
              </p>
            </div>
          </div>
          {fileError && (
            <p className="text-sm text-error flex items-center gap-2">
              <AlertCircle size={14} /> {fileError.message?.toString()}
            </p>
          )}
        </div>
      )}

      {sourceType === 'web' && (
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">URL del sitio o sitemap</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <LinkIcon size={18} className="text-muted-foreground" />
              </div>
              <input
                {...form.register('url')}
                type="url"
                placeholder="https://tutienda.com"
                className={`w-full bg-surface-2 border rounded-md py-2 pl-10 pr-4 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all
                  ${urlError ? 'border-error focus:ring-error' : 'border-border'}
                `}
              />
            </div>
            {urlError && (
              <p className="text-sm text-error flex items-center gap-2">
                <AlertCircle size={14} /> {urlError.message?.toString()}
              </p>
            )}
            <p className="text-xs text-muted-foreground">
              El agente visitará esta URL y las páginas enlazadas (profundidad 2) para extraer texto y tablas.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
