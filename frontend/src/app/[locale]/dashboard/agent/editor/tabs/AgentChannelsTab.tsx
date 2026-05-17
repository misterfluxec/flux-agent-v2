"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { MessageSquare, Smartphone, Globe, Plug } from "lucide-react";

interface AgentChannelsTabProps {
  agentId: string;
}

export function AgentChannelsTab({ agentId }: AgentChannelsTabProps) {
  // TODO: Conectar a GET /channels para mostrar status real
  const channels = [
    { id: "web_chat", name: "Web Chat", icon: Globe, enabled: true, status: "active" },
    { id: "whatsapp", name: "WhatsApp Cloud", icon: Smartphone, enabled: false, status: "pending" },
    { id: "telegram", name: "Telegram", icon: MessageSquare, enabled: false, status: "inactive" },
  ];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Plug className="h-5 w-5" />
            Canales de Comunicación
          </CardTitle>
          <CardDescription>
            Activa los channels por los que tu agente puede interactuar con clientes
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {channels.map((channel) => (
            <div 
              key={channel.id}
              className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <channel.icon className="h-5 w-5 text-muted-foreground" />
                <div>
                  <Label className="font-medium">{channel.name}</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant={
                      channel.status === "active" ? "default" : 
                      channel.status === "pending" ? "secondary" : "outline"
                    } className="text-xs">
                      {channel.status}
                    </Badge>
                    {channel.status === "pending" && (
                      <span className="text-xs text-muted-foreground">
                        Configuración pendiente
                      </span>
                    )}
                  </div>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <Switch 
                  checked={channel.enabled}
                  // TODO: Conectar a API para guardar status
                  onCheckedChange={(checked) => {
                    console.log(`Toggle ${channel.id}: ${checked}`);
                  }}
                  disabled={channel.status !== "active"}
                />
                {channel.status === "pending" && (
                  <Button variant="outline" size="sm">
                    Configurar
                  </Button>
                )}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <AlertProTip />
    </div>
  );
}

function AlertProTip() {
  return (
    <div className="bg-amber-50 border border-amber-200 p-4 rounded-lg">
      <p className="text-sm text-amber-800">
        <strong>💡 Tip profesional:</strong> Activa un canal a la vez para probar 
        el rendimiento de tu agente antes de escalar a múltiples plataformas.
      </p>
    </div>
  );
}
