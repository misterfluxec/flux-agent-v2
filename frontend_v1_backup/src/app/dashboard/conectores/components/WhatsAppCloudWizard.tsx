import React, { useState } from 'react';
import { Shield, Key, Webhook, CheckCircle2, ChevronRight, ChevronLeft, Loader2, PlayCircle, ExternalLink, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

interface WhatsAppCloudWizardProps {
  onClose: () => void;
  onSuccess: (config: any) => void;
}

export default function WhatsAppCloudWizard({ onClose, onSuccess }: WhatsAppCloudWizardProps) {
  const [step, setStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    waba_id: '',
    phone_number_id: '',
    system_user_token: '',
    test_phone_number: ''
  });
  const [verificationResult, setVerificationResult] = useState<any>(null);

  const steps = [
    { title: 'Requisitos', icon: Shield, desc: 'Cuenta de Meta Business' },
    { title: 'Credenciales', icon: Key, desc: 'Tokens de acceso' },
    { title: 'Webhook', icon: Webhook, desc: 'Conexión bidireccional' },
    { title: 'Prueba', icon: PlayCircle, desc: 'Envío de mensaje' },
    { title: '¡Listo!', icon: CheckCircle2, desc: 'Integración completada' }
  ];

  const handleNext = async () => {
    if (step === 2) {
      // Verificar credenciales en el backend
      if (!formData.waba_id || !formData.system_user_token) {
        toast.error('Por favor, ingresa el WABA ID y el Token');
        return;
      }
      setIsLoading(true);
      try {
        const token = localStorage.getItem('flux_token');
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/channels/whatsapp_cloud/verify`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
          body: JSON.stringify({
            waba_id: formData.waba_id,
            system_user_token: formData.system_user_token
          })
        });
        const data = await res.json();
        if (res.ok) {
          setVerificationResult(data.data);
          toast.success('Cuenta verificada correctamente');
          setStep(3);
        } else {
          throw new Error(data.detail || 'Error verificando cuenta');
        }
      } catch (error: any) {
        toast.error(error.message);
      } finally {
        setIsLoading(false);
      }
    } else if (step === 3) {
      // Avanzar al paso de prueba
      if (!formData.phone_number_id) {
        toast.error('Por favor ingresa el Phone Number ID');
        return;
      }
      setStep(4);
    } else if (step === 4) {
      // Enviar mensaje de prueba
      if (!formData.test_phone_number) {
        toast.error('Ingresa un número para la prueba');
        return;
      }
      setIsLoading(true);
      try {
        const token = localStorage.getItem('flux_token');
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/channels/whatsapp_cloud/test`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
          body: JSON.stringify(formData)
        });
        const data = await res.json();
        if (res.ok) {
          toast.success('¡Mensaje de prueba enviado!');
          setStep(5);
        } else {
          throw new Error(data.detail || 'Error enviando prueba');
        }
      } catch (error: any) {
        toast.error(error.message);
      } finally {
        setIsLoading(false);
      }
    } else if (step === 5) {
      onSuccess(formData);
    } else {
      setStep(s => s + 1);
    }
  };

  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-card border border-border shadow-2xl rounded-2xl w-full max-w-4xl flex flex-col max-h-[90vh] animate-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="p-6 border-b border-border flex items-center justify-between bg-emerald-900/10 rounded-t-2xl">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center text-emerald-500">
              <Webhook className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold">WhatsApp Cloud API</h2>
              <p className="text-sm text-muted-foreground">Configuración oficial de Meta</p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>✕</Button>
        </div>

        {/* Layout Principal: Sidebar de Pasos + Contenido */}
        <div className="flex flex-1 overflow-hidden">
          
          {/* Sidebar de Progreso */}
          <div className="w-1/3 border-r border-border bg-secondary/20 p-6 hidden md:block overflow-y-auto">
            <div className="space-y-6">
              {steps.map((s, i) => {
                const isActive = step === i + 1;
                const isPast = step > i + 1;
                const Icon = s.icon;
                return (
                  <div key={i} className={`flex items-start gap-4 transition-opacity ${isActive || isPast ? 'opacity-100' : 'opacity-40'}`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 border-2 ${
                      isActive ? 'border-emerald-500 bg-emerald-500/20 text-emerald-500' :
                      isPast ? 'border-emerald-500 bg-emerald-500 text-white' :
                      'border-border text-muted-foreground'
                    }`}>
                      {isPast ? <CheckCircle2 className="w-5 h-5" /> : <span>{i + 1}</span>}
                    </div>
                    <div>
                      <h4 className={`font-semibold ${isActive ? 'text-emerald-500' : isPast ? 'text-foreground' : 'text-muted-foreground'}`}>
                        {s.title}
                      </h4>
                      <p className="text-xs text-muted-foreground mt-1">{s.desc}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Área de Contenido */}
          <div className="flex-1 flex flex-col overflow-y-auto bg-background p-8 relative">
            
            {step === 1 && (
              <div className="space-y-6 animate-fade-in">
                <h3 className="text-2xl font-bold">Antes de empezar</h3>
                <p className="text-muted-foreground">Para integrar la API oficial, necesitas tener lista tu cuenta de desarrollador en Meta.</p>
                
                <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-xl p-5 space-y-4">
                  <h4 className="font-semibold flex items-center gap-2 text-emerald-600">
                    <Shield className="w-5 h-5" /> Requisitos Previos
                  </h4>
                  <ul className="space-y-3 text-sm">
                    <li className="flex gap-2"><CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" /> Una cuenta de Facebook Developer.</li>
                    <li className="flex gap-2"><CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" /> Una App creada tipo "Business".</li>
                    <li className="flex gap-2"><CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" /> WhatsApp añadido como producto en la App.</li>
                    <li className="flex gap-2"><CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" /> Un Usuario del Sistema con permisos de <code className="bg-secondary px-1 py-0.5 rounded">whatsapp_business_messaging</code>.</li>
                  </ul>
                </div>
                
                <a href="https://developers.facebook.com/docs/whatsapp/cloud-api/get-started" target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 text-emerald-600 hover:underline text-sm font-medium">
                  Guía oficial de Meta <ExternalLink className="w-4 h-4" />
                </a>
              </div>
            )}

            {step === 2 && (
              <div className="space-y-6 animate-fade-in">
                <h3 className="text-2xl font-bold">Credenciales de Meta</h3>
                <p className="text-muted-foreground">Ingresa los identificadores de tu cuenta de WhatsApp Business (WABA).</p>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">WhatsApp Business Account ID (WABA ID)</label>
                    <input 
                      type="text" 
                      value={formData.waba_id} 
                      onChange={e => setFormData({...formData, waba_id: e.target.value})} 
                      placeholder="Ej: 123456789012345" 
                      className="w-full px-4 py-3 bg-secondary/50 rounded-xl border border-border outline-none focus:border-emerald-500 transition-colors" 
                    />
                    <p className="text-xs text-muted-foreground mt-1">Se encuentra en App Dashboard &gt; WhatsApp &gt; API Setup.</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">System User Access Token</label>
                    <textarea 
                      value={formData.system_user_token} 
                      onChange={e => setFormData({...formData, system_user_token: e.target.value})} 
                      placeholder="EAAGm0PX..." 
                      className="w-full px-4 py-3 bg-secondary/50 rounded-xl border border-border outline-none focus:border-emerald-500 transition-colors resize-none h-24" 
                    />
                    <p className="text-xs text-muted-foreground mt-1">El token permanente generado en Business Settings. Nunca expira.</p>
                  </div>
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="space-y-6 animate-fade-in">
                <h3 className="text-2xl font-bold">Configuración del Webhook</h3>
                <div className="bg-emerald-500/10 text-emerald-700 p-4 rounded-xl text-sm font-medium border border-emerald-500/20">
                  ✅ Cuenta verificada: {verificationResult?.name}
                </div>
                
                <p className="text-muted-foreground">Para que FluxAgent pueda recibir mensajes, debes configurar el Webhook en el panel de Meta con los siguientes datos:</p>
                
                <div className="space-y-4">
                  <div className="p-4 bg-secondary/30 rounded-xl border border-border relative group">
                    <label className="block text-xs font-medium text-muted-foreground mb-1">URL de Callback (Webhook)</label>
                    <code className="text-sm font-mono break-all text-emerald-600 dark:text-emerald-400">
                      https://api.labodegaec.com/api/v1/channels/whatsapp_cloud/webhook
                    </code>
                  </div>
                  <div className="p-4 bg-secondary/30 rounded-xl border border-border relative group">
                    <label className="block text-xs font-medium text-muted-foreground mb-1">Verify Token</label>
                    <code className="text-sm font-mono text-emerald-600 dark:text-emerald-400">
                      fluxagent_secret_token
                    </code>
                  </div>
                </div>

                <div className="pt-4 border-t border-border">
                  <label className="block text-sm font-medium mb-1">Phone Number ID</label>
                  <p className="text-xs text-muted-foreground mb-2">El ID específico del número desde el cual enviará mensajes el agente.</p>
                  <input 
                    type="text" 
                    value={formData.phone_number_id} 
                    onChange={e => setFormData({...formData, phone_number_id: e.target.value})} 
                    placeholder="Ej: 109876543210987" 
                    className="w-full px-4 py-3 bg-secondary/50 rounded-xl border border-border outline-none focus:border-emerald-500" 
                  />
                </div>
              </div>
            )}

            {step === 4 && (
              <div className="space-y-6 animate-fade-in">
                <h3 className="text-2xl font-bold">Prueba de Conexión</h3>
                <p className="text-muted-foreground">Vamos a enviar un mensaje de plantilla ("hello_world") a tu número para verificar que todo esté funcionando.</p>
                
                <div className="bg-secondary/30 rounded-xl p-6 border border-border">
                  <label className="block text-sm font-medium mb-2">Tu número de WhatsApp (con código de país)</label>
                  <input 
                    type="text" 
                    value={formData.test_phone_number} 
                    onChange={e => setFormData({...formData, test_phone_number: e.target.value})} 
                    placeholder="Ej: 5215512345678" 
                    className="w-full px-4 py-3 bg-background rounded-xl border border-border outline-none focus:border-emerald-500 text-lg" 
                  />
                  <p className="text-xs text-muted-foreground mt-2 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" /> Si es un número de prueba en Meta, asegúrate de haberlo registrado primero.
                  </p>
                </div>
              </div>
            )}

            {step === 5 && (
              <div className="space-y-6 text-center animate-fade-in flex flex-col items-center justify-center h-full pb-10">
                <div className="w-24 h-24 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-500 mb-4 animate-bounce">
                  <CheckCircle2 className="w-12 h-12" />
                </div>
                <h3 className="text-3xl font-bold text-emerald-500">¡Conexión Exitosa!</h3>
                <p className="text-muted-foreground max-w-md mx-auto">
                  La integración con WhatsApp Cloud API está lista. Tu agente de IA ahora podrá responder mensajes automáticamente por este canal.
                </p>
              </div>
            )}

          </div>
        </div>

        {/* Footer Navigation */}
        <div className="p-6 border-t border-border flex justify-between bg-secondary/10 rounded-b-2xl">
          <Button variant="ghost" onClick={() => step > 1 ? setStep(s => s - 1) : onClose()} className="rounded-xl">
            <ChevronLeft className="w-4 h-4 mr-2" /> {step === 1 ? 'Cancelar' : 'Atrás'}
          </Button>
          
          <Button 
            onClick={handleNext} 
            disabled={isLoading}
            className="rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white min-w-[120px]"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : (
              <>
                {step === 4 ? 'Enviar Prueba' : step === 5 ? 'Finalizar' : 'Siguiente'}
                {step < 5 && <ChevronRight className="w-4 h-4 ml-2" />}
              </>
            )}
          </Button>
        </div>

      </div>
    </div>
  );
}
