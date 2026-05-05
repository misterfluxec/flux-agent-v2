import { getRequestConfig } from 'next-intl/server';

export default getRequestConfig(async ({ locale }) => {
  const targetLocale = locale || 'es';
  
  return {
    locale: targetLocale,
    messages: {
      ...(await import(`./messages/${targetLocale}/global.json`)).default,
      onboarding: (await import(`./messages/${targetLocale}/onboarding.json`)).default,
      conversations: (await import(`./messages/${targetLocale}/conversations.json`)).default,
      billing: (await import(`./messages/${targetLocale}/billing.json`)).default,
      connectors: (await import(`./messages/${targetLocale}/connectors.json`)).default,
      analytics: (await import(`./messages/${targetLocale}/analytics.json`)).default,
      insights: (await import(`./messages/${targetLocale}/insights.json`)).default,
      chat: (await import(`./messages/${targetLocale}/chat.json`)).default,
    }
  };
});
