import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import createMiddleware from 'next-intl/middleware';

const intlMiddleware = createMiddleware({
  locales: ['en', 'es', 'pt'],
  defaultLocale: 'en',
  localePrefix: 'as-needed',
  localeDetection: true
});

export default function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // 1. Ejecutar middleware de internacionalización primero
  const response = intlMiddleware(request);

  // 2. Lógica de protección de Onboarding
  const onboardingComplete = request.cookies.get('onboarding_complete');
  
  if (pathname.includes('/dashboard') && !onboardingComplete) {
    const segments = pathname.split('/');
    const locale = segments[1];
    const isLocale = ['en', 'es', 'pt'].includes(locale);
    const onboardingPath = isLocale ? `/${locale}/onboarding` : '/onboarding';
    
    return NextResponse.redirect(new URL(onboardingPath, request.url));
  }

  return response;
}

export const config = {
  // Protege las rutas y aplica i18n
  matcher: ['/', '/(es|en|pt)/:path*', '/dashboard/:path*', '/login/:path*', '/onboarding/:path*']
};
