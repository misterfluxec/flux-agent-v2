import { Navigation } from "@/components/landing-template/navigation";
import { HeroSection } from "@/components/landing-template/hero-section";
import { FeaturesSection } from "@/components/landing-template/features-section";
import { HowItWorksSection } from "@/components/landing-template/how-it-works-section";
import { InfrastructureSection } from "@/components/landing-template/infrastructure-section";
import { MetricsSection } from "@/components/landing-template/metrics-section";
import { IntegrationsSection } from "@/components/landing-template/integrations-section";
import { SecuritySection } from "@/components/landing-template/security-section";
import { DevelopersSection } from "@/components/landing-template/developers-section";
import { TestimonialsSection } from "@/components/landing-template/testimonials-section";
import { PricingSection } from "@/components/landing-template/pricing-section";
import { CtaSection } from "@/components/landing-template/cta-section";
import { FooterSection } from "@/components/landing-template/footer-section";
import { setRequestLocale } from "next-intl/server";

export default async function TemplatePreview({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  return (
    <main className="relative min-h-screen overflow-x-hidden bg-[#020617] text-white">
      <Navigation />
      <HeroSection />
      <FeaturesSection />
      <HowItWorksSection />
      <InfrastructureSection />
      <MetricsSection />
      <IntegrationsSection />
      <SecuritySection />
      <DevelopersSection />
      <TestimonialsSection />
      <PricingSection />
      <CtaSection />
      <FooterSection />
    </main>
  );
}
