import { Inter } from 'next/font/google';
import { NextIntlClientProvider } from 'next-intl';
import { getMessages } from 'next-intl/server';
import { Providers } from '../providers';
import '../globals.css';

// Inter con todos los pesos operacionales — cargado por Next.js (sin @import manual)
const inter = Inter({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700', '800', '900'],
  display: 'swap',
  variable: '--font-inter',  // expone como CSS var para globals.css
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
      {/* inter.variable expone --font-inter, inter.className aplica font-family directo */}
      <body className={`${inter.variable} ${inter.className} antialiased`}>
        <NextIntlClientProvider messages={messages} locale={locale}>
          <Providers>{children}</Providers>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
