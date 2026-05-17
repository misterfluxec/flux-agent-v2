/**
 * Control de activación de vistas durante migraciones.
 * Se sincroniza con variables de entorno para despliegues progresivos.
 */
export const FEATURES = {
  /** 
   * Si es true, unifica CRM y Customers en una sola vista "CRM 360".
   * Ideal para simplificar la navegación cuando el pipeline y la base de clientes convergen.
   */
  ENABLE_UNIFIED_CRM: process.env.NEXT_PUBLIC_ENABLE_UNIFIED_CRM === 'true',
  
  /** 
   * Expone panel de SuperAdmin solo en entornos controlados.
   * Proporciona acceso a gestión de tenants, logs globales y facturación.
   */
  ENABLE_SUPERADMIN_UI: process.env.NEXT_PUBLIC_ENABLE_SUPERADMIN_UI === 'true',
  
  /** Habilita el nuevo motor de analíticas avanzadas */
  ENABLE_ADVANCED_ANALYTICS: process.env.NEXT_PUBLIC_ENABLE_ADVANCED_ANALYTICS === 'true',
} as const;
