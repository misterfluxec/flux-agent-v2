export default function WhatsAppCloudWizard({ onClose, onSuccess }: { onClose: () => void, onSuccess: (config: any) => void }) {
  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-black/40 backdrop-blur-xl border border-white/5 shadow-xl rounded-[24px] w-full max-w-lg p-8">
        <h2 className="text-xl font-bold text-white mb-4">Configurar WhatsApp Cloud API</h2>
        <p className="text-white/50 mb-6">Conecta tu cuenta de Meta Business para empezar a recibir mensajes.</p>
        
        {/* Mock Wizard Content */}
        <div className="space-y-4 mb-8">
          <div className="p-4 bg-white/5 rounded-xl border border-white/5">
            <p className="text-sm text-white/80">Paso 1: Inicia sesión en Facebook</p>
          </div>
          <div className="p-4 bg-white/5 rounded-xl border border-white/5 opacity-50">
            <p className="text-sm text-white/80">Paso 2: Selecciona tu número</p>
          </div>
          <div className="p-4 bg-white/5 rounded-xl border border-white/5 opacity-50">
            <p className="text-sm text-white/80">Paso 3: Verifica el Webhook</p>
          </div>
        </div>

        <div className="flex justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-white transition-colors">
            Cancelar
          </button>
          <button 
            onClick={() => onSuccess({ phoneNumber: '+1234567890', token: 'mock_token_123' })}
            className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white transition-colors font-bold shadow-[0_0_15px_rgba(6,182,212,0.3)]"
          >
            Simular Conexión
          </button>
        </div>
      </div>
    </div>
  );
}
