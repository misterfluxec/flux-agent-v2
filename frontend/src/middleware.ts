import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import createMiddleware from 'next-intl/middleware';

const SUPPORTED_LOCALES = ['en', 'es', 'pt'];
const DEFAULT_LOCALE = 'en';
const LOCALE_COOKIE = 'preferred-locale';

const intlMiddleware = createMiddleware({
  locales: SUPPORTED_LOCALES,
  defaultLocale: DEFAULT_LOCALE,
  localePrefix: 'always',
  localeDetection: false
});

function detectLocale(request: NextRequest): string {
  const cookieLocale = request.cookies.get(LOCALE_COOKIE)?.value;
  if (cookieLocale && SUPPORTED_LOCALES.includes(cookieLocale)) {
    return cookieLocale;
  }

  const acceptLanguage = request.headers.get('accept-language');
  if (!acceptLanguage) return DEFAULT_LOCALE;
  
  const languages = acceptLanguage
    .split(',')
    .map(l => l.split(';')[0].trim().toLowerCase().substring(0, 2));
  
  for (const lang of languages) {
    if (SUPPORTED_LOCALES.includes(lang)) return lang;
  }
  
  return DEFAULT_LOCALE;
}

export default function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isRootPath = pathname === '/';
  
  const detectedLocale = detectLocale(request);
  
  if (isRootPath) {
    const targetPath = `/${detectedLocale}`;
    const redirectedResponse = NextResponse.redirect(new URL(targetPath, request.url));
    
    if (!request.cookies.has(LOCALE_COOKIE)) {
      redirectedResponse.cookies.set(LOCALE_COOKIE, detectedLocale, {
        httpOnly: false,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        maxAge: 60 * 60 * 24 * 365
      });
    }
    
    return redirectedResponse;
  }

  if (!pathname.startsWith(`/${detectedLocale}/`) && 
      !SUPPORTED_LOCALES.some(loc => pathname.startsWith(`/${loc}`)) &&
      !pathname.match(/^\/(es|en|pt)$/)) {
    const newPath = `/${detectedLocale}${pathname === '/' ? '' : pathname}`;
    return NextResponse.redirect(new URL(newPath, request.url));
  }

  const response = intlMiddleware(request);

  const onboardingComplete = request.cookies.get('onboarding_complete');
  if (pathname.includes('/dashboard') && !onboardingComplete) {
    const segments = pathname.split('/');
    const locale = segments[1];
    const isLocale = SUPPORTED_LOCALES.includes(locale);
    const onboardingPath = isLocale ? `/${locale}/onboarding` : `/${detectedLocale}/onboarding`;
    
    return NextResponse.redirect(new URL(onboardingPath, request.url));
  }

  return response;
}

export const config = {
  matcher: ['/', '/(es|en|pt)/:path*', '/dashboard/:path*', '/login/:path*', '/onboarding/:path*']
};
