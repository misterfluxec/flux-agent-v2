"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import {
  Bot,
  LayoutDashboard,
  MessageSquare,
  Settings,
  Target,
  BarChart3,
  Plug,
  LogOut,
  Zap
} from "lucide-react";

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };

    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  const runCommand = (command: () => void) => {
    setOpen(false);
    command();
  };

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Escribe un comando o busca..." />
      <CommandList>
        <CommandEmpty>No hay resultados.</CommandEmpty>
        
        <CommandGroup heading="Navegación Rápida">
          <CommandItem onSelect={() => runCommand(() => router.push("/dashboard"))}>
            <LayoutDashboard className="mr-2 h-4 w-4" />
            <span>Inicio (Torre de Control)</span>
          </CommandItem>
          <CommandItem onSelect={() => runCommand(() => router.push("/dashboard/conversations"))}>
            <MessageSquare className="mr-2 h-4 w-4" />
            <span>Conversaciones</span>
          </CommandItem>
          <CommandItem onSelect={() => runCommand(() => router.push("/dashboard/yanua"))}>
            <Bot className="mr-2 h-4 w-4" />
            <span>Yanua AI</span>
          </CommandItem>
          <CommandItem onSelect={() => runCommand(() => router.push("/dashboard/analytics"))}>
            <BarChart3 className="mr-2 h-4 w-4" />
            <span>Analytics</span>
          </CommandItem>
        </CommandGroup>
        
        <CommandSeparator />
        
        <CommandGroup heading="Acciones Inteligentes">
          <CommandItem onSelect={() => runCommand(() => alert("Aumentar límite invocado"))}>
            <Zap className="mr-2 h-4 w-4 text-amber-500" />
            <span className="text-amber-500">Aumentar límite de tokens</span>
          </CommandItem>
          <CommandItem onSelect={() => runCommand(() => router.push("/dashboard/connectors"))}>
            <Plug className="mr-2 h-4 w-4" />
            <span>Verificar Canales</span>
          </CommandItem>
          <CommandItem onSelect={() => runCommand(() => router.push("/dashboard/automations"))}>
            <Target className="mr-2 h-4 w-4" />
            <span>Crear Regla de Automatización</span>
          </CommandItem>
        </CommandGroup>
        
        <CommandSeparator />
        
        <CommandGroup heading="Sistema">
          <CommandItem onSelect={() => runCommand(() => router.push("/dashboard/settings"))}>
            <Settings className="mr-2 h-4 w-4" />
            <span>Configuración Avanzada</span>
          </CommandItem>
          <CommandItem onSelect={() => runCommand(() => {
            localStorage.removeItem('flux_token');
            router.push('/login');
          })}>
            <LogOut className="mr-2 h-4 w-4 text-red-500" />
            <span className="text-red-500">Cerrar Sesión</span>
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
