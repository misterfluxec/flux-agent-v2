export type PlanTier = 'starter' | 'pro' | 'enterprise';
export type SubscriptionStatus = 'active' | 'past_due' | 'canceled' | 'trialing';

export interface Plan {
  id: PlanTier;
  name: string;
  price: number;
  currency: string;
  interval: 'month' | 'year';
  features: string[];
  limits: {
    messagesPerMonth: number;
    agents: number;
    connectors: number;
    storageGB: number;
    prioritySupport: boolean;
  };
  stripePriceId: string;
}

export interface Subscription {
  status: SubscriptionStatus;
  currentPeriodEnd: string;
  cancelAtPeriodEnd: boolean;
  stripeCustomerId: string;
  stripeSubscriptionId: string;
}

export interface UsageMetrics {
  messagesUsed: number;
  messagesLimit: number;
  agentsUsed: number;
  agentsLimit: number;
  storageUsedGB: number;
  storageLimitGB: number;
  percentUsed: number;
}

export const PLANS: Plan[] = [
  {
    id: 'starter', name: 'Starter', price: 29, currency: 'USD', interval: 'month',
    features: ['1 Agente', '500 mensajes/mes', 'WhatsApp + Telegram', 'Soporte por email'],
    limits: { messagesPerMonth: 500, agents: 1, connectors: 2, storageGB: 2, prioritySupport: false },
    stripePriceId: 'price_starter_monthly'
  },
  {
    id: 'pro', name: 'Pro', price: 79, currency: 'USD', interval: 'month',
    features: ['3 Agentes', '5,000 mensajes/mes', 'WhatsApp Oficial + CRM', 'Soporte prioritario'],
    limits: { messagesPerMonth: 5000, agents: 3, connectors: 5, storageGB: 10, prioritySupport: true },
    stripePriceId: 'price_pro_monthly'
  },
  {
    id: 'enterprise', name: 'Enterprise', price: 199, currency: 'USD', interval: 'month',
    features: ['Agentes ilimitados', 'Mensajes ilimitados', 'API dedicada + SLA 99.9%', 'Gerente de cuenta'],
    limits: { messagesPerMonth: 999999, agents: 999, connectors: 999, storageGB: 100, prioritySupport: true },
    stripePriceId: 'price_enterprise_monthly'
  }
];
