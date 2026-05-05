'use client';

import { useTranslations } from 'next-intl';
import { useTheme } from 'next-themes';
import { Menu, Moon, Sun, Globe, Bell, Search } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export function Header({ onMenuToggle }: { onMenuToggle: () => void }) {
  const { theme, setTheme } = useTheme();
  const tNav = useTranslations('nav');
  const tCommon = useTranslations('common');
  const pathname = usePathname();

  // Simple breadcrumbs logic
  const sections = ['dashboard', 'my_agent', 'conversations', 'connectors', 'analytics', 'settings'];
  const currentSection = sections.find(key => pathname.includes(key)) || 'dashboard';

  return (
    <header className="h-16 border-b border-border bg-card flex items-center justify-between px-4 md:px-6 shrink-0 z-20">
      {/* Left: Menu & Title */}
      <div className="flex items-center gap-4">
        <button onClick={onMenuToggle} className="lg:hidden p-2 hover:bg-accent rounded-md">
          <Menu className="w-5 h-5" />
        </button>
        <h2 className="text-lg font-semibold capitalize hidden md:block">
          {tNav(currentSection as any)}
        </h2>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2 md:gap-4">
        {/* Search (Hidden on mobile) */}
        <div className="hidden md:flex items-center bg-muted/50 px-3 py-1.5 rounded-md border border-transparent focus-within:border-primary/50 transition-all w-64">
          <Search className="w-4 h-4 text-muted-foreground mr-2" />
          <input 
            type="text" 
            placeholder={tCommon('search')} 
            className="bg-transparent border-none outline-none text-sm w-full placeholder:text-muted-foreground" 
          />
        </div>

        {/* Theme Toggle */}
        <button 
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          className="p-2 rounded-md hover:bg-accent transition-colors"
        >
          {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>

        {/* Lang Toggle (Preserves Current Route) */}
        <div className="flex items-center gap-1">
          {['en', 'es', 'pt'].map((lang) => {
            const getLangUrl = () => {
              const segments = pathname.split('/');
              if (['en', 'es', 'pt'].includes(segments[1])) {
                segments[1] = lang;
                return segments.join('/');
              }
              return `/${lang}${pathname === '/' ? '' : pathname}`;
            };
            return (
              <Link 
                key={lang} 
                href={getLangUrl()} 
                className={`p-2 rounded-md hover:bg-accent transition-colors text-xs font-bold uppercase ${pathname.startsWith(`/${lang}`) ? 'text-primary' : 'text-muted-foreground'}`}
              >
                {lang}
              </Link>
            );
          })}
        </div>

        {/* Notifications */}
        <button className="p-2 rounded-md hover:bg-accent transition-colors relative">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border-2 border-card" />
        </button>
      </div>
    </header>
  );
}
