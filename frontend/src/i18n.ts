import { getRequestConfig } from 'next-intl/server';

const locales = ['en', 'es', 'pt'];
const defaultLocale = 'es';

const loadMessages = async (locale: string) => ({
  ...(await import(`./messages/${locale}/global.json`)).default,
  auth: (await import(`./messages/${locale}/auth.json`)).default,
  landing: (await import(`./messages/${locale}/landing.json`)).default,
  onboarding: (await import(`./messages/${locale}/onboarding.json`)).default,
  conversations: (await import(`./messages/${locale}/conversations.json`)).default,
  billing: (await import(`./messages/${locale}/billing.json`)).default,
  connectors: (await import(`./messages/${locale}/connectors.json`)).default,
  analytics: (await import(`./messages/${locale}/analytics.json`)).default,
  insights: (await import(`./messages/${locale}/insights.json`)).default,
  chat: (await import(`./messages/${locale}/chat.json`)).default,
});

export default getRequestConfig(async ({ requestLocale }) => {
  let locale = await requestLocale;

  if (!locale || !locales.includes(locale)) {
    locale = defaultLocale;
  }

  try {
    const messages = await loadMessages(locale);
    return { locale, messages };
  } catch (error) {
    console.error(`Error loading messages for ${locale}, falling back to ${defaultLocale}`, error);
    const messages = await loadMessages(defaultLocale);
    return { locale: defaultLocale, messages };
  }
});
