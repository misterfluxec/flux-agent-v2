import React, { useState, useRef } from 'react';
import { User, Upload, Check, Bot, Sparkles, BrainCircuit } from 'lucide-react';
import { toast } from 'sonner';
import { api } from '@/lib/api';

interface AvatarSelectorProps {
  currentAvatar: string | null;
  onAvatarChange: (newUrl: string) => void;
  agentId: string;
}

const PRESET_AVATARS = [
  { id: 'minimalist', icon: Bot, label: 'Minimalista', color: 'bg-blue-500/20 text-blue-400' },
  { id: 'friendly', icon: Sparkles, label: 'Amigable', color: 'bg-amber-500/20 text-amber-400' },
  { id: 'intelligent', icon: BrainCircuit, label: 'Inteligente', color: 'bg-purple-500/20 text-purple-400' },
];

export function AvatarSelector({ currentAvatar, onAvatarChange, agentId }: AvatarSelectorProps) {
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    const toastId = toast.loading('Subiendo avatar personalizado...');
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const res = await api.post(`/agents/${agentId}/avatar`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      onAvatarChange(res.data.avatar_url);
      toast.success('Avatar actualizado', { id: toastId });
    } catch (err) {
      toast.error('Error al subir avatar', { id: toastId });
    } finally {
      setIsUploading(false);
    }
  };

  const handlePresetSelect = async (presetId: string) => {
    // Por ahora simulamos los presets como rutas estáticas o simplemente informamos
    toast.info(`Estilo "${presetId}" aplicado (Simulado)`);
    // En el futuro esto podría actualizar una opción de estilo en el backend
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col items-center gap-6">
        <div className="relative group">
          <div className="w-32 h-32 rounded-3xl overflow-hidden border-4 border-white/10 dark:border-slate-800 bg-slate-100 dark:bg-slate-900 flex items-center justify-center transition-all group-hover:border-indigo-500/50 shadow-xl">
            {currentAvatar ? (
              <img 
                src={currentAvatar.startsWith('/') ? `${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:9000'}${currentAvatar}` : currentAvatar} 
                alt="Avatar" 
                className="w-full h-full object-cover" 
              />
            ) : (
              <User className="w-12 h-12 text-slate-400" />
            )}
            
            {isUploading && (
              <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
                <div className="w-8 h-8 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin" />
              </div>
            )}
          </div>
          
          <button 
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="absolute -bottom-2 -right-2 p-3 bg-indigo-600 hover:bg-indigo-500 rounded-2xl shadow-2xl border-4 border-white dark:border-slate-900 transition-all hover:scale-110 active:scale-95"
            title="Subir imagen"
          >
            <Upload className="w-5 h-5 text-white" />
          </button>
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleUpload} 
            className="hidden" 
            accept="image/*" 
          />
        </div>

        <div className="text-center">
          <h4 className="text-lg font-bold text-slate-900 dark:text-white mb-1">Avatar del Agente</h4>
          <p className="text-xs text-slate-500 dark:text-slate-400 max-w-[200px]">
            Personaliza la apariencia visual de tu asistente.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {PRESET_AVATARS.map((preset) => (
          <button
            key={preset.id}
            onClick={() => handlePresetSelect(preset.id)}
            className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50 hover:bg-indigo-500/5 hover:border-indigo-500/30 transition-all text-center group"
          >
            <div className={`w-10 h-10 rounded-xl ${preset.color} flex items-center justify-center mx-auto mb-2 group-hover:scale-110 transition-transform`}>
              <preset.icon className="w-5 h-5" />
            </div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">{preset.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
