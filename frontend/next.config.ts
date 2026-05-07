import type { NextConfig } from "next";
import createNextIntlPlugin from 'next-intl/plugin';

const withNextIntl = createNextIntlPlugin('./src/i18n.ts');

const nextConfig: NextConfig = {
  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
  // @ts-ignore
  allowedDevOrigins: ['app.labodegaec.com', 'localhost'],
  images: {
    domains: ['localhost', 'api.labodegaec.com'],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:9000/api/:path*', // Proxy to FastAPI Backend
      },
    ];
  },
};

export default withNextIntl(nextConfig);
