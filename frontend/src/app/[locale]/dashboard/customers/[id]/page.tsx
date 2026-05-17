'use client';

import { useQuery } from '@tanstack/react-query';
import { customersApi } from '@/services/api/customers';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Loader2, Mail, Phone, ShoppingBag, Clock, Activity, MessageSquare, AlertCircle, ChevronLeft } from 'lucide-react';
import { useParams, useRouter } from 'next/navigation';
import { useLocale } from 'next-intl';
import { Button } from '@/components/ui/button';
import { useState } from 'react';

export default function Customer360Page() {
  const params = useParams();
  const router = useRouter();
  const locale = useLocale();
  const customerId = params.id as string;
  const [activeTab, setActiveTab] = useState<'activity' | 'chat'>('activity');

  const { data: profile, isLoading: isProfileLoading } = useQuery({
    queryKey: ['customer', customerId],
    queryFn: () => customersApi.getCustomer360(customerId)
  });

  const { data: timelineData, isLoading: isTimelineLoading } = useQuery({
    queryKey: ['customer-timeline', customerId],
    queryFn: () => customersApi.getCustomerTimeline(customerId)
  });

  if (isProfileLoading || isTimelineLoading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!profile) return <div>Cliente no encontrado</div>;

  const getEventIcon = (type: string) => {
    if (type.includes('order')) return <ShoppingBag className="h-4 w-4 text-blue-500" />;
    if (type.includes('payment')) return <Activity className="h-4 w-4 text-green-500" />;
    if (type.includes('message')) return <MessageSquare className="h-4 w-4 text-purple-500" />;
    return <Clock className="h-4 w-4 text-gray-500" />;
  };

  const formatEventMessage = (event: any) => {
    switch (event.type) {
      case 'order.created': return `Realizó la sort_order #${event.payload?.order_id?.split('-')[0]} por $${event.payload?.total_amount}`;
      case 'payment.confirmed': return `Pago confirmado para la sort_order #${event.payload?.order_id?.split('-')[0]}`;
      case 'message.received': return `Envió un mensaje vía ${event.payload?.channel || 'chat'}`;
      default: return event.type;
    }
  };

  const initials = profile.first_name ? profile.first_name[0] : (profile.email ? profile.email[0].toUpperCase() : 'U');

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.push(`/${locale}/dashboard/customers`)}>
          <ChevronLeft className="h-5 w-5" />
        </Button>
        <h1 className="text-3xl font-bold tracking-tight">Perfil 360</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Columna Izquierda: Identidad y Privacidad */}
        <div className="space-y-6">
          <Card>
            <CardHeader className="text-center pb-2">
              <div className="flex justify-center mb-4">
                <Avatar className="h-24 w-24 border-4 border-background shadow-sm">
                  <AvatarFallback className="text-2xl bg-primary/10 text-primary">{initials}</AvatarFallback>
                </Avatar>
              </div>
              <CardTitle className="text-2xl">{profile.first_name} {profile.last_name}</CardTitle>
              <CardDescription>
                <Badge variant={profile.metrics.health_state === 'healthy' ? 'default' : 'secondary'} className="mt-2">
                  {profile.metrics.health_state}
                </Badge>
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 pt-4">
              <div className="flex items-center gap-3 text-sm">
                <Mail className="h-4 w-4 text-muted-foreground" />
                <span>{profile.email || 'Sin correo'}</span>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <Phone className="h-4 w-4 text-muted-foreground" />
                <span>{profile.phone || 'Sin teléfono'}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-muted-foreground" />
                Preferencias (GDPR)
              </CardTitle>
            </CardHeader>
                <div className="space-y-4 p-6">
                  <div className="flex items-center justify-between p-3 bg-slate-900 rounded-lg border border-slate-800">
                    <div>
                      <p className="text-sm font-medium text-white flex items-center gap-2">
                        <MessageSquare className="h-4 w-4 text-emerald-400" /> Transaccional
                      </p>
                      <p className="text-xs text-slate-400">Notificaciones de órdenes, envíos y soporte</p>
                    </div>
                    <Switch 
                      checked={profile.preferences?.transactional_consent ?? true} 
                      onCheckedChange={() => {}}
                    />
                  </div>
                  <div className="flex items-center justify-between p-3 bg-slate-900 rounded-lg border border-slate-800">
                    <div>
                      <p className="text-sm font-medium text-white flex items-center gap-2">
                        <Mail className="h-4 w-4 text-cyan-400" /> Marketing
                      </p>
                      <p className="text-xs text-slate-400">Newsletters, promociones y encuestas</p>
                    </div>
                    <Switch 
                      checked={profile.preferences?.marketing_automation_consent ?? false} 
                      onCheckedChange={() => {}}
                    />
                  </div>
                </div>
          </Card>
        </div>

        {/* Columna Central: Activity Stream */}
        <div className="md:col-span-2 space-y-6">
          <div className="grid grid-cols-3 gap-4">
            <Card>
              <CardContent className="p-4 flex flex-col items-center justify-center text-center">
                <p className="text-sm font-medium text-muted-foreground mb-1">LTV Total</p>
                <p className="text-2xl font-bold">${profile.metrics.ltv.toFixed(2)}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 flex flex-col items-center justify-center text-center">
                <p className="text-sm font-medium text-muted-foreground mb-1">Órdenes</p>
                <p className="text-2xl font-bold">{profile.metrics.order_count}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 flex flex-col items-center justify-center text-center">
                <p className="text-sm font-medium text-muted-foreground mb-1">Riesgo Churn</p>
                <p className="text-2xl font-bold">{(profile.metrics.churn_score * 100).toFixed(0)}%</p>
              </CardContent>
            </Card>
          </div>

          <Card className="h-[600px] flex flex-col">
            <CardHeader className="pb-3 border-b border-border/50">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">Registro del Cliente</CardTitle>
                  <CardDescription>Eventos y conversaciones</CardDescription>
                </div>
                <div className="flex bg-slate-900 rounded-lg p-1 border border-slate-800">
                  <button 
                    onClick={() => setActiveTab('activity')}
                    className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${activeTab === 'activity' ? 'bg-slate-800 text-white shadow-sm' : 'text-slate-400 hover:text-white'}`}
                  >
                    Actividad
                  </button>
                  <button 
                    onClick={() => setActiveTab('chat')}
                    className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${activeTab === 'chat' ? 'bg-purple-900/50 text-purple-300 shadow-sm' : 'text-slate-400 hover:text-white'}`}
                  >
                    Chat IA
                  </button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="flex-1 overflow-auto p-0">
              {activeTab === 'activity' ? (
                <div className="p-6 relative space-y-8 before:absolute before:inset-0 before:ml-[44px] before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-800 before:to-transparent">
                  {timelineData?.events.map((event) => (
                  <div key={event.id} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                    <div className="flex items-center justify-center w-10 h-10 rounded-full border-4 border-background bg-slate-100 text-slate-500 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                      {getEventIcon(event.type)}
                    </div>
                    <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-card p-4 rounded-xl border shadow-sm">
                      <div className="flex items-center justify-between mb-1">
                        <h3 className="font-semibold text-sm capitalize">{event.type.replace('.', ' ')}</h3>
                        <time className="text-xs text-muted-foreground">
                          {new Date(event.timestamp).toLocaleDateString()} {new Date(event.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        </time>
                      </div>
                      <p className="text-sm text-muted-foreground">{formatEventMessage(event)}</p>
                    </div>
                  </div>
                ))}
                {timelineData?.events.length === 0 && (
                  <div className="text-center py-10 text-muted-foreground">
                    No hay actividad registrada para este cliente.
                  </div>
                )}
              </div>
              ) : (
                <div className="p-6 space-y-4 bg-black/20 h-full">
                  <div className="bg-purple-500/10 border border-purple-500/20 text-purple-300 p-3 rounded-xl text-xs flex items-center gap-2">
                    <MessageSquare className="w-4 h-4" /> Log de conversaciones con el Agente IA de Ventas (Solo Lectura)
                  </div>
                  
                  {timelineData?.events.filter((e: any) => e.type.includes('message')).length === 0 ? (
                    <div className="text-center py-10 text-muted-foreground">
                      No hay conversaciones registradas.
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {/* Simulating chat bubbles from timeline data */}
                      {timelineData?.events.filter((e: any) => e.type.includes('message')).map((event: any, idx: number) => {
                        const isUser = event.payload?.direction === 'inbound' || !event.payload?.direction;
                        return (
                          <div key={idx} className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
                            <div className={`max-w-[80%] p-3 rounded-2xl text-sm ${
                              isUser 
                                ? 'bg-slate-800 text-white rounded-br-sm' 
                                : 'bg-purple-900/40 border border-purple-500/30 text-purple-100 rounded-bl-sm'
                            }`}>
                              {event.payload?.text || formatEventMessage(event)}
                            </div>
                            <span className="text-[10px] text-slate-500 mt-1 px-1">
                              {new Date(event.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                            </span>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
