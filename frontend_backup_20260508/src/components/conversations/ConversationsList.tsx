import { Search, User, Bot, AlertCircle } from 'lucide-react';
import { Conversation } from '@/types/conversation';

interface Props {
  conversations: Conversation[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  search: string;
  onSearchChange: (v: string) => void;
  statusFilter: string;
  onStatusFilterChange: (v: string) => void;
}

export function ConversationsList({ conversations, selectedId, onSelect, search, onSearchChange, statusFilter, onStatusFilterChange }: Props) {
  const statuses = [
    { id: 'all', label: 'Todos' },
    { id: 'active', label: 'Resolviendo IA' },
    { id: 'waiting', label: 'Requiere Humano' },
  ];

  return (
    <div className="w-full md:w-80 lg:w-96 border-r border-border bg-card flex flex-col h-full shrink-0">
      <div className="p-4 border-b border-border space-y-4">
        <div className="flex items-center gap-2 bg-background rounded-lg px-3 py-2 border border-border focus-within:border-primary/50 transition-all shadow-sm">
          <Search className="w-4 h-4 text-muted-foreground" />
          <input 
            value={search} 
            onChange={e => onSearchChange(e.target.value)} 
            placeholder="Buscar mensaje o teléfono..." 
            className="bg-transparent outline-none text-sm w-full text-foreground" 
          />
        </div>
        <div className="flex gap-2 overflow-x-auto pb-1 no-scrollbar">
          {statuses.map(s => (
            <button 
              key={s.id} 
              onClick={() => onStatusFilterChange(s.id)} 
              className={`px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-all border ${
                statusFilter === s.id 
                ? 'bg-primary/10 border-primary/30 text-primary shadow-[0_0_10px_rgba(6,182,212,0.1)]' 
                : 'bg-background border-border text-muted-foreground hover:bg-white/5'
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto custom-scrollbar bg-background/50">
        {conversations.map(c => {
          const isHumanNeeded = c.status === 'waiting' || c.status === 'new';
          return (
            <button 
              key={c.id} 
              onClick={() => onSelect(c.id)} 
              className={`w-full p-4 border-b border-border/50 text-left hover:bg-card transition-colors flex gap-3 relative ${
                selectedId === c.id ? 'bg-card shadow-sm' : ''
              }`}
            >
              {selectedId === c.id && <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary rounded-r-md shadow-[0_0_10px_rgba(6,182,212,0.5)]" />}
              
              <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0 border border-primary/20 relative">
                <User className="w-5 h-5 text-primary" />
                {isHumanNeeded ? (
                  <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-destructive rounded-full border-2 border-background flex items-center justify-center">
                    <AlertCircle className="w-2.5 h-2.5 text-white" />
                  </div>
                ) : (
                  <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-background flex items-center justify-center">
                    <Bot className="w-2.5 h-2.5 text-white" />
                  </div>
                )}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex justify-between items-center mb-0.5">
                  <span className={`font-semibold text-sm truncate ${selectedId === c.id ? 'text-primary' : 'text-foreground'}`}>
                    {c.contactName || c.contactPhone}
                  </span>
                  <span className="text-[10px] text-muted-foreground whitespace-nowrap">
                    {new Date(c.lastMessageTime).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground truncate leading-relaxed">
                  {c.lastMessage}
                </p>
                <div className="flex items-center gap-2 mt-2">
                  <span className={`px-2 py-0.5 rounded-md text-[9px] font-bold uppercase tracking-wider ${
                    isHumanNeeded
                    ? 'bg-destructive/10 text-destructive border border-destructive/20 animate-pulse' 
                    : 'bg-primary/10 text-primary border border-primary/20'
                  }`}>
                    {isHumanNeeded ? 'Requiere Humano' : 'IA Atendiendo'}
                  </span>
                </div>
              </div>
            </button>
          );
        })}
        {conversations.length === 0 && (
          <div className="p-12 text-center text-muted-foreground">
            <div className="bg-card border border-border w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
               <Search className="w-5 h-5 text-muted-foreground/50" />
            </div>
            <p className="text-sm font-medium">No se encontraron leads.</p>
          </div>
        )}
      </div>
    </div>
  );
}
