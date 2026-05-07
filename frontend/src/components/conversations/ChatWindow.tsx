
import { Send, Loader2, User, Phone, Info } from 'lucide-react';
import { Conversation } from '@/types/conversation';
import { useState, useRef, useEffect } from 'react';

interface Props {
  conversation: Conversation | null;
  onSend: (text: string) => void;
  isSending: boolean;
}

export function ChatWindow({ conversation, onSend, isSending }: Props) {
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [conversation?.messages, isSending]);

  const handleSend = () => { 
    if (input.trim() && !isSending) { 
      onSend(input); 
      setInput(''); 
    } 
  };

  if (!conversation) return (
    <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground bg-accent/5">
      <div className="bg-card p-8 rounded-2xl border border-border/50 text-center shadow-sm">
        <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
           <Info className="w-8 h-8 text-primary" />
        </div>
        <p className="text-base font-medium text-foreground">Ningún lead seleccionado</p>
        <p className="text-sm mt-1">Selecciona un lead para ver el historial.</p>
      </div>
    </div>
  );

  return (
    <div className="flex-1 flex flex-col bg-background h-full overflow-hidden border-r border-border">
      {/* Header */}
      <div className="h-16 border-b border-border flex items-center justify-between px-6 bg-card shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center border border-primary/5">
            <User className="w-4 h-4 text-primary" />
          </div>
          <div>
            <h3 className="font-semibold text-sm leading-none">{conversation.contactName}</h3>
            <p className="text-[11px] text-muted-foreground mt-1 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
              {conversation.contactPhone || 'Sin número'}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button className="p-2.5 hover:bg-accent rounded-full transition-colors border border-transparent hover:border-border">
            <Phone className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] bg-fixed opacity-[0.03] dark:invert pointer-events-none" />
      <div className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar relative z-10">
        <div className="flex justify-center mb-6">
           <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60 bg-muted px-2 py-0.5 rounded-full">
             Conversación Iniciada
           </span>
        </div>
        {conversation.messages.map(msg => (
          <div key={msg.id} className={`flex ${msg.role === 'agent' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
            <div className={`max-w-[75%] group relative ${msg.role === 'agent' ? 'order-1' : 'order-2'}`}>
              <div className={`rounded-2xl px-4 py-2.5 text-sm shadow-sm ${
                msg.role === 'agent' 
                ? 'bg-primary text-primary-foreground rounded-br-none' 
                : 'bg-card border border-border rounded-bl-none'
              }`}>
                <p className="leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                <div className={`text-[9px] font-medium mt-1.5 flex items-center gap-1 ${
                  msg.role === 'agent' ? 'text-primary-foreground/70' : 'text-muted-foreground'
                }`}>
                  {new Date(msg.timestamp).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}
                </div>
              </div>
            </div>
          </div>
        ))}
        {isSending && (
          <div className="flex justify-end animate-pulse">
            <div className="bg-primary/10 border border-primary/20 text-primary px-4 py-2 rounded-2xl rounded-br-none text-xs font-medium flex items-center gap-2">
              <Loader2 className="w-3.5 h-3.5 animate-spin" /> Escribiendo...
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-4 border-t border-border bg-card">
        <div className="flex gap-2 items-end">
          <div className="flex-1 relative">
            <textarea 
              value={input} 
              onChange={e => setInput(e.target.value)} 
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Escribe un mensaje para intervenir..." 
              className="w-full bg-muted/40 border border-border rounded-xl px-4 py-3 text-sm outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all resize-none max-h-32 min-h-[46px]"
              rows={1}
            />
          </div>
          <button 
            onClick={handleSend} 
            disabled={!input.trim() || isSending} 
            className="bg-primary text-primary-foreground p-3 rounded-xl hover:bg-primary/90 disabled:opacity-50 transition-all shadow-md active:scale-95 shrink-0"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
