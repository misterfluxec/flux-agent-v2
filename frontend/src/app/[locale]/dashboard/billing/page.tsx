'use client';
import { BillingDashboard } from '@/components/billing/BillingDashboard';
import { Subscription, UsageMetrics } from '@/types/billing';
import { useState } from 'react';

// Datos simulados para CX. Reemplazar con fetch real a /api/tenant/billing
const MOCK_SUBSCRIPTION: Subscription = {
  status: 'active',
  currentPeriodEnd: '2026-06-05T00:00:00Z',
  cancelAtPeriodEnd: false,
  stripeCustomerId: 'cus_demo123',
  stripeSubscriptionId: 'sub_demo123'
};

const MOCK_USAGE: UsageMetrics = {
  messagesUsed: 420, messagesLimit: 500,
  agentsUsed: 1, agentsLimit: 1,
  storageUsedGB: 1.2, storageLimitGB: 2,
  percentUsed: 84
};

export default function BillingPage() {
  const [planId, setPlanId] = useState('starter');

  const handleUpgrade = (newPlanId: string) => {
    // Aquí llamarías a createCheckoutSession(newPlanId)
    alert(`Redirigiendo a Stripe para plan: ${newPlanId}`);
  };

  const handleManageBilling = () => {
    // Aquí llamarías a createPortalSession()
    alert('Abriendo portal de facturación de Stripe');
  };

  return (
    <div className="p-4 md:p-8 animate-in fade-in duration-700 overflow-y-auto max-h-screen custom-scrollbar">
      <BillingDashboard 
        subscription={MOCK_SUBSCRIPTION} 
        usage={MOCK_USAGE} 
        currentPlanId={planId} 
        onUpgrade={handleUpgrade} 
        onManageBilling={handleManageBilling} 
      />
    </div>
  );
}
