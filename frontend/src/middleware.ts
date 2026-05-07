import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import createMiddleware from 'next-intl/middleware';

// =============================================================================
// CONFIGURACIÓN DE REDIRECCIONES (MIGRACIÓN DE RUTAS)
// =============================================================================

/**
 * Mapeo de rutas antiguas → nuevas rutas unificadas
 * Se ejecuta en el middleware para redirecciones 302 transparentes
 */
const ROUTE_REDIRECTS: Record<string, string> = {
  // Analytics unificado
  "/dashboard/insights": "/dashboard/metrics",
  "/dashboard/reports": "/dashboard/metrics",
  
  // Agente unificado (tabs)
  "/dashboard/script-editor": "/dashboard/agent?tab=scripts",
  "/dashboard/data-ingestion": "/dashboard/data",
  "/dashboard/inventory": "/dashboard/data?tab=catalog",
  
  // Settings unificado
  "/dashboard/settings/billing": "/dashboard/settings?tab=billing",
  "/dashboard/settings/team": "/dashboard/settings?tab=team",
  
  // Legacy: eliminar en próxima versión
  "/dashboard/testing": "/dashboard/agent?tab=config", // Redirigir a playground futuro
};

// =============================================================================
// CONFIGURACIÓN DE PROTECCIÓN DE RUTAS
// =============================================================================

/**
 * Rutas que requieren autenticación
 * Se verifica la presencia del token en cookies/headers
 */
const PROTECTED_ROUTES = ["/dashboard", "/api/v1"];

/**
 * Rutas públicas (no requieren auth)
 */
const PUBLIC_ROUTES = ["/", "/auth/login", "/auth/register", "/health"];

// =============================================================================
// CONFIGURACIÓN DE INTERNACIONALIZACIÓN
// =============================================================================

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

// =============================================================================
// MIDDLEWARE PRINCIPAL
// =============================================================================

export default function middleware(request: NextRequest) {
  const { pathname, searchParams } = request.nextUrl;
  const locale = request.nextUrl.locale || detectLocale(request);
  const isRootPath = pathname === '/';
  
  // =============================================================================
  // 1. REDIRECCIONES DE RUTAS OBSOLETAS
  // =============================================================================
  
  // Verificar si la ruta actual tiene una redirección configurada
  const normalizedPath = pathname.replace(`/${locale}`, "");
  
  if (ROUTE_REDIRECTS[normalizedPath]) {
    const targetPath = ROUTE_REDIRECTS[normalizedPath];
    const targetUrl = new URL(`/${locale}${targetPath}`, request.url);
    
    // Preservar query params originales si la ruta destino no los tiene
    if (!targetUrl.search && request.nextUrl.search) {
      targetUrl.search = request.nextUrl.search;
    }
    
    // Redirección 302 (temporal) para permitir rollback si es necesario
    return NextResponse.redirect(targetUrl, { status: 302 });
  }

  // =============================================================================
  // 2. MANEJO DE LOCALES Y ROOT PATH
  // =============================================================================
  
  if (isRootPath) {
    const targetPath = `/${locale}`;
    const redirectedResponse = NextResponse.redirect(new URL(targetPath, request.url));
    
    if (!request.cookies.has(LOCALE_COOKIE)) {
      redirectedResponse.cookies.set(LOCALE_COOKIE, locale, {
        httpOnly: false,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        maxAge: 60 * 60 * 24 * 365
      });
    }
    
    return redirectedResponse;
  }

  // =============================================================================
  // 3. PROTECCIÓN DE RUTAS (AUTH CHECK)
  // =============================================================================
  
  const isProtectedRoute = PROTECTED_ROUTES.some((route) =>
    normalizedPath.startsWith(route)
  );
  
  const isPublicRoute = PUBLIC_ROUTES.some((route) =>
    normalizedPath === route || normalizedPath.startsWith(`${route}/`)
  );

  if (isProtectedRoute && !isPublicRoute) {
    // Verificar token de autenticación (ajustar según tu estrategia de auth)
    const token = request.cookies.get("auth_token")?.value || 
                  request.headers.get("authorization")?.replace("Bearer ", "");
    
    if (!token) {
      // Redirigir a login preservando la ruta original para redirect post-login
      const loginUrl = new URL(`/${locale}/login`, request.url);
      loginUrl.searchParams.set("callbackUrl", pathname + request.nextUrl.search);
      
      return NextResponse.redirect(loginUrl);
    }
    
    // TODO: Validar token con backend si es necesario (rate limit, expiración, etc.)
    // Esto se puede hacer con una llamada a /auth/verify o decodificando JWT
  }

  // =============================================================================
  // 4. MANEJO DE PATHS CON LOCALES
  // =============================================================================
  
  if (!pathname.startsWith(`/${locale}/`) && 
      !SUPPORTED_LOCALES.some(loc => pathname.startsWith(`/${loc}`)) &&
      !pathname.match(/^\/(es|en|pt)$/)) {
    const newPath = `/${locale}${pathname === '/' ? '' : pathname}`;
    return NextResponse.redirect(new URL(newPath, request.url));
  }

  // =============================================================================
  // 5. ONBOARDING CHECK
  // =============================================================================
  
  const response = intlMiddleware(request);
  
  const onboardingComplete = request.cookies.get('onboarding_complete');
  if (pathname.includes('/dashboard') && !onboardingComplete) {
    const segments = pathname.split('/');
    const pathLocale = segments[1];
    const isLocale = SUPPORTED_LOCALES.includes(pathLocale);
    const onboardingPath = isLocale ? `/${pathLocale}/onboarding` : `/${locale}/onboarding`;
    
    return NextResponse.redirect(new URL(onboardingPath, request.url));
  }

  // =============================================================================
  // 6. HEADERS DE SEGURIDAD Y OBSERVABILIDAD
  // =============================================================================
  
  // Agregar headers para debugging y monitoreo
  response.headers.set("X-Request-ID", crypto.randomUUID());
  response.headers.set("X-Frame-Options", "DENY");
  response.headers.set("X-Content-Type-Options", "nosniff");
  
  // CORS para API calls desde el frontend
  if (pathname.startsWith("/api")) {
    response.headers.set("Access-Control-Allow-Origin", process.env.NEXT_PUBLIC_APP_URL || "*");
    response.headers.set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
    response.headers.set("Access-Control-Allow-Headers", "Content-Type, Authorization");
  }
  
  return response;
}

// =============================================================================
// CONFIGURACIÓN DE MATCHER (qué rutas ejecutan este middleware)
// =============================================================================

export const config = {
  matcher: [
    /*
     * Match todas las rutas excepto:
     * - Archivos estáticos (_next, images, etc.)
     * - Favicon, robots.txt
     * - API routes de Next.js (no las de tu app)
     */
    "/((?!_next/static|_next/image|favicon.ico|robots.txt|api/auth).*)",
  ],
};
