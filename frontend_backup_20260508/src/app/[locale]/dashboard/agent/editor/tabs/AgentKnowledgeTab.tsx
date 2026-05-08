"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Database, FileText, Link as LinkIcon, Plus, Trash2, AlertCircle, Loader2 } from "lucide-react";
import Link from "next/link";
import { fetchKnowledge, deleteKnowledgeSource, clearBrain } from "@/lib/api";
import { toast } from "sonner";
import { SkeletonCard } from "@/components/ui/SkeletonCard";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"; // Assume this exists, if not I'll just use standard confirm() for now, but shadcn usually has it. Let's use confirm() to be safe and avoid missing components if AlertDialog isn't installed.

interface AgentKnowledgeTabProps {
  agentId: string;
}

export function AgentKnowledgeTab({ agentId }: AgentKnowledgeTabProps) {
  const queryClient = useQueryClient();

  const { data: knowledgeData, isLoading, isError } = useQuery({
    queryKey: ["agent-knowledge", agentId],
    queryFn: fetchKnowledge,
  });

  const deleteMutation = useMutation({
    mutationFn: deleteKnowledgeSource,
    onSuccess: () => {
      toast.success("Fuente eliminada correctamente.");
      queryClient.invalidateQueries({ queryKey: ["agent-knowledge"] });
    },
    onError: () => {
      toast.error("Error al eliminar la fuente.");
    },
  });

  const clearBrainMutation = useMutation({
    mutationFn: clearBrain,
    onSuccess: (data) => {
      toast.success(`Cerebro vaciado. Chunks eliminados: ${data.chunks_eliminados}`);
      queryClient.invalidateQueries({ queryKey: ["agent-knowledge"] });
    },
    onError: () => {
      toast.error("Error al vaciar el cerebro del agente.");
    },
  });

  const handleDeleteSource = (fuenteNombre: string) => {
    if (confirm(`¿Estás seguro de que deseas eliminar la fuente: ${fuenteNombre}?`)) {
      deleteMutation.mutate(fuenteNombre);
    }
  };

  const handleClearBrain = () => {
    if (confirm("🚨 ATENCIÓN: Esto eliminará TODO el conocimiento del agente. ¿Estás seguro?")) {
      clearBrainMutation.mutate();
    }
  };

  return (
    <div className="space-y-6">
      <AlertInfo />
      
      <div className="flex justify-end mb-4">
        <Button 
          variant="destructive" 
          onClick={handleClearBrain}
          disabled={clearBrainMutation.isPending || !knowledgeData?.fuentes?.length}
        >
          {clearBrainMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Trash2 className="mr-2 h-4 w-4" />}
          Vaciar Cerebro Completo
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Documentos RAG */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Documentos RAG
            </CardTitle>
            <CardDescription>Archivos que alimentan el conocimiento del agente</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            
            {isLoading ? (
              <SkeletonCard />
            ) : isError ? (
              <div className="text-red-500 text-sm">Error al cargar conocimiento.</div>
            ) : (
              <div className="space-y-3">
                {knowledgeData?.fuentes && knowledgeData.fuentes.length > 0 ? (
                  <ul className="divide-y rounded-md border">
                    {knowledgeData.fuentes.map((fuente) => (
                      <li key={fuente.fuente_nombre} className="flex items-center justify-between p-3 text-sm">
                        <div className="flex flex-col">
                          <span className="font-medium truncate max-w-[200px]" title={fuente.fuente_nombre}>
                            {fuente.fuente_nombre}
                          </span>
                          <span className="text-xs text-muted-foreground">{fuente.chunks} chunks</span>
                        </div>
                        <Button 
                          variant="ghost" 
                          size="icon" 
                          className="text-red-500 hover:text-red-700 hover:bg-red-50"
                          onClick={() => handleDeleteSource(fuente.fuente_nombre)}
                          disabled={deleteMutation.isPending}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-center py-6 text-muted-foreground">
                    <Database className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">No hay documentos indexados</p>
                  </div>
                )}
              </div>
            )}

            <Link href="/dashboard/data-ingestion" passHref className="block mt-4">
              <Button variant="outline" className="w-full">
                <Plus className="h-4 w-4 mr-2" />
                Ir al Asistente de Ingesta
              </Button>
            </Link>
          </CardContent>
        </Card>

        {/* Fuentes Externas */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <LinkIcon className="h-5 w-5" />
              Fuentes Externas
            </CardTitle>
            <CardDescription>Sincronización automática de sitios web y APIs</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">
                Conecta tu sitio web para que el agente aprenda automáticamente (Scraping).
              </p>
              <Link href="/dashboard/data-ingestion" passHref className="block">
                <Button variant="outline" className="w-full">
                  <Plus className="h-4 w-4 mr-2" />
                  Agregar URL externa
                </Button>
              </Link>
            </div>
            
            <div className="text-xs text-muted-foreground bg-muted p-3 rounded flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-blue-500 shrink-0" />
              <span>Tip: El Asistente de Ingesta te permite procesar múltiples URLs y sitemaps.</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function AlertInfo() {
  return (
    <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
      <p className="text-sm text-blue-800">
        <strong>Consejo:</strong> Cuantos más documentos relevantes agregues, 
        más preciso será tu agente. Prioriza contenido actualizado y específico 
        de tu negocio. Todo el conocimiento subido se inyectará automáticamente en las conversaciones del agente.
      </p>
    </div>
  );
}
