const fs = require('fs');
const path = require('path');

const locales = ['es', 'en', 'pt'];
const dummyData = {
  faq: {
    faq: {
      badge: "Preguntas Frecuentes",
      title_1: "Resolvemos tus",
      title_2: "Dudas",
      items: [
        { q: "¿Qué es FluxAgent?", a: "Es una plataforma empresarial." }
      ]
    }
  },
  industries: {
    industries: {
      badge: "Casos de Uso",
      title_1: "Adaptado a tu",
      title_2: "Industria",
      items: [
        { name: "Retail", description: "Ventas automáticas", icon: "🛒" },
        { name: "Salud", description: "Agendamiento de citas", icon: "🏥" },
        { name: "Servicios", description: "Soporte 24/7", icon: "⚙️" },
        { name: "Inmobiliaria", description: "Calificación de leads", icon: "🏢" }
      ]
    }
  },
  how_it_works: {
    how_it_works: {
      badge: "Cómo funciona",
      title_1: "Simple en 3",
      title_2: "Pasos",
      items: [
        { step: "1", title: "Conecta", description: "Conecta tu canal de WhatsApp" },
        { step: "2", title: "Entrena", description: "Sube tu catálogo de productos" },
        { step: "3", title: "Vende", description: "Recibe clientes en piloto automático" }
      ]
    }
  },
  smart_infra: {
    smart_infra: {
      badge: "IA bajo tu control",
      title_1: "Privacidad y",
      title_2: "Potencia",
      subtitle: "Modelos privados y control total de tu información",
      points: [
        "Soberanía de datos garantizada",
        "Modelos open source optimizados",
        "Modo de privacidad activo"
      ]
    }
  }
};

locales.forEach(loc => {
  const dir = path.join('frontend', 'src', 'messages', loc, 'landing');
  Object.keys(dummyData).forEach(fileKey => {
    const filePath = path.join(dir, `${fileKey}.json`);
    if (!fs.existsSync(filePath)) {
      fs.writeFileSync(filePath, JSON.stringify(dummyData[fileKey], null, 2), 'utf-8');
    }
  });
});
console.log("Archivos JSON faltantes creados.");
