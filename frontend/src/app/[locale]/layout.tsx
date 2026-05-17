import { Plus_Jakarta_Sans } from 'next/font/google';
import { NextIntlClientProvider } from 'next-intl';
import { getMessages } from 'next-intl/server';
import { Providers } from '../providers';
import '../globals.css';

// Tipografía Enterprise B2B - Plus Jakarta Sans
const jakarta = Plus_Jakarta_Sans({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '800'],
  display: 'swap',
  variable: '--font-jakarta',  // expone como CSS var para globals.css
});

export const metadata = {
  title: 'FluxAgent OS — Sistema Operativo Comercial Inteligente',
  description: 'Plataforma de Agentes de Ventas IA con gobernanza, observabilidad y Revenue Intelligence.',
};

export default async function RootLayout({
  children,
  params
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale: rawLocale } = await params;
  const locale = ['en', 'es', 'pt'].includes(rawLocale) ? rawLocale : 'es';
  
  let messages;
  try {
    messages = await getMessages({ locale });
  } catch (error) {
    console.error('Failed to load messages:', error);
    messages = {};
  }

  return (
    <html lang={locale} className="dark" suppressHydrationWarning data-scroll-behavior="smooth">
      {/* Aplicar Plus Jakarta Sans en todo el body */}
      <body className={`${jakarta.variable} font-sans antialiased`}>
        <NextIntlClientProvider messages={messages} locale={locale}>
          <Providers>{children}</Providers>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
