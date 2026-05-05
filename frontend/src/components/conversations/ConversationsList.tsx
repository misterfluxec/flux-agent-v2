import { useTranslations } from 'next-intl';
import { Search, User } from 'lucide-react';
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
  const t = useTranslations('conversations');
  const statuses = ['all', 'new', 'active', 'waiting', 'closed'];

  return (
    <div className="w-full md:w-80 lg:w-96 border-r border-border bg-card flex flex-col h-full shrink-0">
      <div className="p-4 border-b border-border space-y-3">
        <div className="flex items-center gap-2 bg-muted/50 rounded-lg px-3 py-2 border border-transparent focus-within:border-primary/30 transition-all">
          <Search className="w-4 h-4 text-muted-foreground" />
          <input 
            value={search} 
            onChange={e => onSearchChange(e.target.value)} 
            placeholder={t('search')} 
            className="bg-transparent outline-none text-sm w-full" 
          />
        </div>
        <div className="flex gap-2 overflow-x-auto pb-1 no-scrollbar">
          {statuses.map(s => (
            <button 
              key={s} 
              onClick={() => onStatusFilterChange(s)} 
              className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-all ${
                statusFilter === s 
                ? 'bg-primary text-primary-foreground shadow-sm' 
                : 'bg-muted text-muted-foreground hover:bg-muted/80'
              }`}
            >
              {t(`status_${s}` as any)}
            </button>
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {conversations.map(c => (
          <button 
            key={c.id} 
            onClick={() => onSelect(c.id)} 
            className={`w-full p-4 border-b border-border text-left hover:bg-accent/30 transition-colors flex gap-3 relative ${
              selectedId === c.id ? 'bg-accent/50' : ''
            }`}
          >
            {selectedId === c.id && <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary" />}
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0 border border-primary/5">
              <User className="w-5 h-5 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex justify-between items-center mb-0.5">
                <span className="font-semibold text-sm truncate">{c.contactName}</span>
                <span className="text-[10px] text-muted-foreground whitespace-nowrap">
                  {new Date(c.lastMessageTime).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}
                </span>
              </div>
              <p className="text-xs text-muted-foreground truncate leading-relaxed">{c.lastMessage}</p>
              <div className="flex items-center gap-2 mt-2">
                <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider ${
                  c.unreadCount > 0 
                  ? 'bg-primary/20 text-primary animate-pulse' 
                  : 'bg-muted text-muted-foreground'
                }`}>
                  {c.unreadCount > 0 ? `${c.unreadCount} ${t('unread')}` : t('read')}
                </span>
                <div className="flex items-center gap-1">
                   <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                   <span className="text-[10px] text-muted-foreground font-medium">Score: {c.leadScore}</span>
                </div>
              </div>
            </div>
          </button>
        ))}
        {conversations.length === 0 && (
          <div className="p-12 text-center text-muted-foreground">
            <div className="bg-muted w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3 opacity-50">
               <Search className="w-6 h-6" />
            </div>
            <p className="text-sm font-medium">{t('empty')}</p>
          </div>
        )}
      </div>
    </div>
  );
}
