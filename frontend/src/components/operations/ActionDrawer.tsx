import React, { useState } from 'react';
import { TimelineEvent } from '@/types/operations';
import { usePriorityQueue } from '@/hooks/usePriorityQueue';
import { X, Check, Clock, UserPlus, Tag } from 'lucide-react';

interface Props {
  event: TimelineEvent;
  onClose: () => void;
}

export function ActionDrawer({ event, onClose }: Props) {
  const { acknowledgeEvent, assignEvent, isMutating } = usePriorityQueue();
  const [snoozeMinutes, setSnoozeMinutes] = useState(60);

  const handleAck = async (state: 'acknowledged' | 'snoozed' | 'resolved') => {
    await acknowledgeEvent({ eventId: event.id, state, snooze_minutes: state === 'snoozed' ? snoozeMinutes : undefined });
    onClose();
  };

  const handleAssign = async () => {
    // Para simplificar, asignamos al usuario actual usando claim (en el backend, si pasamos nuestro ID es claim, si pasamos vacío o no lo pasamos hace auto-claim dependiendo de cómo lo mandamos, o lo dejamos como 'claim' si lo pasamos explícito. Vamos a pasar un string "me" que la api o el backend deberían resolver, pero por ahora solo llamamos al endpoint).
    // Asumimos que el backend toma el token y sabe quién es. Si pasamos assigned_to con nuestro ID hace claim. Si no pasamos nada pero está en el body, quizás no hace nada. 
    // Usaremos assignEvent con assigned_team: "soporte" por ejemplo.
    await assignEvent({ eventId: event.id, assigned_team: "operations" });
    onClose();
  };

  return (
    <div className="fixed inset-y-0 right-0 w-80 bg-slate-900 border-l border-white/10 shadow-2xl p-4 flex flex-col z-50 animate-in slide-in-from-right duration-200">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-sm font-semibold text-white">Acciones Operacionales</h3>
        <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
          <X size={18} />
        </button>
      </div>

      <div className="mb-6">
        <p className="text-xs text-slate-400 mb-1">Evento seleccionado</p>
        <p className="text-sm text-slate-200 font-medium">{event.summary}</p>
        <p className="text-[10px] text-slate-500 font-mono mt-1">{event.id}</p>
      </div>

      <div className="flex-1 space-y-4">
        {/* Acknowledge */}
        <div className="space-y-2">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Estado (ACK)</p>
          <div className="flex flex-col gap-2">
            <button 
              onClick={() => handleAck('acknowledged')}
              disabled={isMutating}
              className="flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm rounded border border-white/5 transition-colors"
            >
              <Check size={14} className="text-emerald-400" /> Marcar Acknowledged
            </button>
            <button 
              onClick={() => handleAck('resolved')}
              disabled={isMutating}
              className="flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm rounded border border-white/5 transition-colors"
            >
              <Check size={14} className="text-emerald-500" /> Marcar Resuelto
            </button>
            <div className="flex gap-2">
              <button 
                onClick={() => handleAck('snoozed')}
                disabled={isMutating}
                className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm rounded border border-white/5 transition-colors"
              >
                <Clock size={14} className="text-amber-400" /> Snooze
              </button>
              <select 
                value={snoozeMinutes} 
                onChange={(e) => setSnoozeMinutes(Number(e.target.value))}
                className="w-20 bg-slate-950 border border-white/10 rounded px-2 text-sm text-slate-300 outline-none focus:border-cyan-500"
              >
                <option value={15}>15m</option>
                <option value={60}>1h</option>
                <option value={240}>4h</option>
                <option value={1440}>1d</option>
              </select>
            </div>
          </div>
        </div>

        {/* Assignment */}
        <div className="space-y-2 pt-2">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Asignación</p>
          <button 
            onClick={handleAssign}
            disabled={isMutating}
            className="w-full flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm rounded border border-white/5 transition-colors"
          >
            <UserPlus size={14} className="text-cyan-400" /> Asignar a equipo Ops
          </button>
        </div>

      </div>

      <div className="mt-auto pt-4 border-t border-white/10">
        <button 
          onClick={onClose}
          className="w-full py-2 bg-white/5 hover:bg-white/10 text-slate-300 text-sm rounded transition-colors"
        >
          Cancelar
        </button>
      </div>
    </div>
  );
}
