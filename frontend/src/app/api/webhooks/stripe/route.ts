import { headers } from 'next/headers';
import { stripe } from '@/lib/stripe';
import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  const body = await req.text();
  const headersList = await headers();
  const signature = headersList.get('Stripe-Signature');

  if (!signature) {
    return NextResponse.json({ error: 'Missing signature' }, { status: 400 });
  }

  let event;
  try {
    event = stripe.webhooks.constructEvent(
      body, 
      signature, 
      process.env.STRIPE_WEBHOOK_SECRET || 'whsec_mock'
    );
  } catch (err: any) {
    console.error('Webhook signature verification failed:', err.message);
    return NextResponse.json({ error: 'Invalid signature' }, { status: 400 });
  }

  switch (event.type) {
    case 'checkout.session.completed': {
      const session = event.data.object as any;
      console.log('✅ Suscripción creada para tenant:', session.metadata?.tenantId);
      break;
    }
    case 'invoice.payment_failed': {
      const invoice = event.data.object as any;
      console.log('❌ Pago fallido para cliente:', invoice.customer_email);
      break;
    }
    case 'customer.subscription.updated': {
      const sub = event.data.object as any;
      console.log('🔄 Suscripción actualizada:', sub.id);
      break;
    }
  }

  return NextResponse.json({ received: true });
}
