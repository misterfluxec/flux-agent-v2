// Aplica límites antes de procesar mensajes o crear agentes
export function enforceLimits(tenant: any, action: 'send_message' | 'create_agent' | 'upload_file') {
  const { plan, usage } = tenant;
  const limits = plan.limits;

  if (action === 'send_message' && usage.messagesUsed >= limits.messagesPerMonth) {
    throw new Error('Límite de mensajes alcanzado. Actualiza tu plan o espera al próximo ciclo.');
  }
  if (action === 'create_agent' && usage.agentsUsed >= limits.agents) {
    throw new Error('Límite de agentes alcanzado. Actualiza tu plan.');
  }
  if (action === 'upload_file' && usage.storageUsedGB >= limits.storageGB) {
    throw new Error('Espacio de almacenamiento lleno. Actualiza tu plan o elimina archivos.');
  }
}
