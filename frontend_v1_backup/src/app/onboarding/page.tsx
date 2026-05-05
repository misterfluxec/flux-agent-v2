"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Bot, Building, CheckCircle2, ChevronLeft, UploadCloud, Link as LinkIcon, MessageSquare } from "lucide-react";
import { Card } from "@/components/ui/card";

type Step = 1 | 2 | 3;

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>(1);
  const [loading, setLoading] = useState(false);

  // Form Data
  const [empresa, setEmpresa] = useState("");
  const [industria, setIndustria] = useState("");
  const [tono, setTono] = useState<"profesional" | "amigable" | "creativo">("profesional");

  const handleNext = () => {
    if (step < 3) setStep((s) => (s + 1) as Step);
    else handleFinish();
  };

  const handleBack = () => {
    if (step > 1) setStep((s) => (s - 1) as Step);
  };

  const handleFinish = async () => {
    setLoading(true);
    // Simular guardado de configuración inicial en la API
    localStorage.setItem("flux_empresa", empresa || "Mi Empresa");
    await new Promise((r) => setTimeout(r, 1500));
    router.push("/dashboard");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-[#0a0a0a] p-4 font-sans">
      
      {/* Fondo decorativo sutil (Typebot style) */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-100 via-slate-50 to-slate-50 dark:from-indigo-900/20 dark:via-[#0a0a0a] dark:to-[#0a0a0a] -z-10" />

      <div className="w-full max-w-2xl animate-entry">
        
        {/* Progress Bar & Header */}
        <div className="mb-8 text-center space-y-4">
          <div className="flex items-center justify-center gap-2 mb-6">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className={`h-1.5 rounded-full transition-all duration-300 ${
                  i === step ? "w-8 bg-indigo-600" : i < step ? "w-8 bg-indigo-200 dark:bg-indigo-900" : "w-4 bg-slate-200 dark:bg-slate-800"
                }`}
              />
            ))}
          </div>
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-indigo-50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 mb-2">
            {step === 1 && <Building size={24} />}
            {step === 2 && <Bot size={24} />}
            {step === 3 && <CheckCircle2 size={24} />}
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">
            {step === 1 && "Bienvenido a VentaCore"}
            {step === 2 && "Personaliza tu Agente"}
            {step === 3 && "Sube tu primer conocimiento"}
          </h1>
          <p className="text-slate-500 dark:text-slate-400 max-w-md mx-auto text-sm sm:text-base">
            {step === 1 && "Vamos a configurar tu entorno de trabajo para que el agente entienda tu negocio."}
            {step === 2 && "Define cómo quieres que se comunique la Inteligencia Artificial con tus clientes."}
            {step === 3 && "La IA necesita saber qué vender. (Puedes saltar este paso y hacerlo después)."}
          </p>
        </div>

        {/* Card Content */}
        <Card className="border-slate-200 dark:border-slate-800 shadow-xl dark:shadow-2xl dark:shadow-indigo-900/10 bg-white/70 dark:bg-slate-900/50 backdrop-blur-xl rounded-2xl overflow-hidden p-6 sm:p-10">
          
          {/* STEP 1 */}
          {step === 1 && (
            <div className="space-y-6 animate-entry">
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                  ¿Cuál es el nombre de tu empresa o marca?
                </label>
                <input
                  type="text"
                  placeholder="Ej. Zapatería El Sol, Tech Solutions..."
                  value={empresa}
                  onChange={(e) => setEmpresa(e.target.value)}
                  className="w-full h-12 px-4 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300 flex items-center justify-between">
                  <span>¿A qué industria pertenece?</span>
                  <span className="text-xs font-normal text-slate-400">Ayuda a la IA a dar mejor contexto</span>
                </label>
                <select
                  value={industria}
                  onChange={(e) => setIndustria(e.target.value)}
                  className="w-full h-12 px-4 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 appearance-none"
                >
                  <option value="" disabled>Selecciona una opción...</option>
                  <option value="ecommerce">Tienda Online / E-commerce</option>
                  <option value="servicios">Servicios Profesionales</option>
                  <option value="restaurante">Restaurante / Comida</option>
                  <option value="inmobiliaria">Inmobiliaria</option>
                  <option value="salud">Salud y Bienestar</option>
                  <option value="otro">Otro</option>
                </select>
              </div>
            </div>
          )}

          {/* STEP 2 */}
          {step === 2 && (
            <div className="space-y-6 animate-entry">
              <div className="grid gap-4">
                <button
                  onClick={() => setTono("profesional")}
                  className={`p-4 rounded-xl border-2 text-left transition-all ${
                    tono === "profesional" 
                      ? "border-indigo-600 bg-indigo-50/50 dark:bg-indigo-500/10 dark:border-indigo-500" 
                      : "border-slate-200 dark:border-slate-800 hover:border-indigo-200 dark:hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400"><Building size={18} /></div>
                    <span className="font-semibold text-slate-900 dark:text-white">Tono Profesional</span>
                  </div>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Formal, directo y corporativo. Ideal para seguros, clínicas, estudios legales.</p>
                  <div className="mt-3 p-3 bg-white dark:bg-slate-950 rounded-lg text-xs italic text-slate-600 dark:text-slate-400 border border-slate-100 dark:border-slate-800">
                    "Buen día. Gracias por comunicarse con nosotros. ¿En qué podemos ayudarle hoy?"
                  </div>
                </button>

                <button
                  onClick={() => setTono("amigable")}
                  className={`p-4 rounded-xl border-2 text-left transition-all ${
                    tono === "amigable" 
                      ? "border-indigo-600 bg-indigo-50/50 dark:bg-indigo-500/10 dark:border-indigo-500" 
                      : "border-slate-200 dark:border-slate-800 hover:border-indigo-200 dark:hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400"><MessageSquare size={18} /></div>
                    <span className="font-semibold text-slate-900 dark:text-white">Tono Amigable y Empático</span>
                  </div>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Cercano, cálido y servicial. Perfecto para e-commerce, tiendas de ropa, restaurantes.</p>
                  <div className="mt-3 p-3 bg-white dark:bg-slate-950 rounded-lg text-xs italic text-slate-600 dark:text-slate-400 border border-slate-100 dark:border-slate-800">
                    "¡Hola! 👋 Qué gusto saludarte. Cuéntame, ¿qué estás buscando para que pueda ayudarte?"
                  </div>
                </button>
              </div>
            </div>
          )}

          {/* STEP 3 */}
          {step === 3 && (
            <div className="space-y-6 animate-entry text-center">
              <div className="p-8 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-2xl bg-slate-50/50 dark:bg-slate-900/20">
                <div className="flex justify-center mb-4">
                  <div className="p-4 bg-white dark:bg-slate-950 rounded-full shadow-sm border border-slate-100 dark:border-slate-800">
                    <UploadCloud size={32} className="text-slate-400" />
                  </div>
                </div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">Sube tu catálogo</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 mb-6 max-w-sm mx-auto">
                  Arrastra un PDF o archivo Excel con los detalles de tus productos o servicios, para que la IA sepa exactamente qué responder.
                </p>
                <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
                  <button className="flex items-center justify-center gap-2 px-5 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-sm font-semibold rounded-xl hover:bg-slate-50 dark:hover:bg-slate-700/50 transition w-full sm:w-auto">
                    <UploadCloud size={16} /> Subir archivo
                  </button>
                  <span className="text-xs text-slate-400">o</span>
                  <button className="flex items-center justify-center gap-2 px-5 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-sm font-semibold rounded-xl hover:bg-slate-50 dark:hover:bg-slate-700/50 transition w-full sm:w-auto">
                    <LinkIcon size={16} /> Pegar URL de tu Web
                  </button>
                </div>
              </div>
            </div>
          )}

        </Card>

        {/* Footer Actions */}
        <div className="mt-8 flex items-center justify-between animate-entry">
          <button
            onClick={handleBack}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold text-slate-500 hover:text-slate-900 dark:hover:text-white transition ${
              step === 1 ? "opacity-0 pointer-events-none" : "opacity-100"
            }`}
          >
            <ChevronLeft size={16} /> Atrás
          </button>
          
          <button
            onClick={handleNext}
            disabled={loading || (step === 1 && !empresa)}
            className="flex items-center gap-2 px-6 py-2.5 bg-indigo-600 text-white text-sm font-semibold rounded-xl hover:bg-indigo-700 transition shadow-md hover:shadow-lg hover:-translate-y-0.5 disabled:opacity-50 disabled:pointer-events-none disabled:transform-none"
          >
            {loading ? "Preparando Dashboard..." : step === 3 ? "Ir al Dashboard" : "Continuar"}
            {!loading && step < 3 && <ArrowRight size={16} />}
          </button>
        </div>

      </div>
    </div>
  );
}
