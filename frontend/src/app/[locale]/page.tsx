"use client";

import { useState, useEffect } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import Link from 'next/link';
import '../landing_web.css';

function useLandingContent() {
  const t = useTranslations('landing');
  return {
    nav: t.raw('nav'),
    auth: t.raw('auth'),
    hero: t.raw('hero'),
    market: t.raw('market'),
    features: t.raw('features'),
    chat: t.raw('chat'),
    comparison: t.raw('comparison.rows'),
    plans: Object.values(t.raw('plans')),
    marketAlternatives: t.raw('marketAlternatives.items'),
    stats: t.raw('stats.items'),
    footer: t.raw('footer'),
    final_cta: t.raw('final_cta')
  };
}

export default function LandingPage() {
  const locale = useLocale();
  const content = useLandingContent();
  const [isScrolled, setIsScrolled] = useState(false);
  const [activeFeature, setActiveFeature] = useState(0);
  const [chatOpen, setChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState([
    { sender: 'agent', text: content.chat.welcome }
  ]);
  const [chatInput, setChatInput] = useState('');

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleChatSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMessage = { sender: 'user', text: chatInput };
    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');

    setTimeout(() => {
      const agentResponses = content.chat.responses;
      const randomResponse = agentResponses[Math.floor(Math.random() * agentResponses.length)];
      setChatMessages(prev => [...prev, { sender: 'agent', text: randomResponse }]);
    }, 1500);
  };

  const featureIcons = [
    <svg key="1" className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>,
    <svg key="2" className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>,
    <svg key="3" className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
    <svg key="4" className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
  ];

  const featuresData = content.features.items.map((feat: any, idx: number) => ({
    ...feat,
    icon: featureIcons[idx]
  }));

  const planIcons = ['🛡️', '🎙️', '🧠'];
  const plansData = content.plans.map((plan: any, idx: number) => ({
    ...plan,
    icon: planIcons[idx]
  }));

  const footerIcons = [
    <svg key="f1" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>,
    <svg key="f2" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>,
    <svg key="f3" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>,
    <svg key="f4" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
  ];

  const footerItemIcons = [
    ['🇬🇧', '📍', '🏢'],
    ['🇬🇧', '🌎', '🔒'],
    ['🌎', '📡'],
    ['⚡', '🎧', '⚡', '🧠']
  ];

  const footerData = content.footer.sections.map((section: any, sectionIdx: number) => ({
    ...section,
    icon: footerIcons[sectionIdx],
    content: section.content.map((text: string, itemIdx: number) => ({
      text,
      icon: footerItemIcons[sectionIdx][itemIdx]
    }))
  }));

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white overflow-x-hidden">
      {/* Gradient Background Effects */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-gradient-to-br from-purple-600/20 via-transparent to-transparent blur-[120px] rounded-full animate-pulse-slow"></div>
        <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-gradient-to-br from-cyan-600/15 via-transparent to-transparent blur-[100px] rounded-full animate-pulse-slow-delay"></div>
      </div>

      {/* Navigation */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${isScrolled ? 'bg-[#0a0a0f]/90 backdrop-blur-xl border-b border-white/5' : ''}`}>
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="relative w-10 h-10 flex items-center justify-center">
                <img src="/logo.png" alt="FluxAgent V2 Logo" className="w-full h-full object-contain" />
              </div>
              <span className="text-xl font-black tracking-tight bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">FluxAgent V2</span>
            </div>

            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-gray-400 hover:text-white transition-colors text-sm font-medium">{content.nav.features}</a>
              <a href="#comparativa" className="text-gray-400 hover:text-white transition-colors text-sm font-medium">{content.nav.comparison}</a>
              <a href="#pricing" className="text-gray-400 hover:text-white transition-colors text-sm font-medium">{content.nav.pricing}</a>
              <a href="#tech" className="text-gray-400 hover:text-white transition-colors text-sm font-medium">{content.nav.tech}</a>
            </div>

            <div className="flex items-center gap-4">
              <Link href={`/${locale}/login`} className="text-gray-400 hover:text-white transition-colors text-sm font-medium hidden sm:block">{content.auth.login}</Link>
              <Link href={`/${locale}/register`} className="px-5 py-2.5 bg-gradient-to-r from-purple-600 to-purple-500 rounded-full text-sm font-semibold hover:shadow-lg hover:shadow-purple-500/25 transition-all hover:scale-105">
                {content.auth.free_trial}
              </Link>
              
              <div className="flex items-center gap-1.5 ml-2 pl-4 border-l border-white/10">
                {['en', 'es', 'pt'].map((lang) => (
                  <Link 
                    key={lang} 
                    href={`/${lang}`}
                    className={`px-2 py-1 rounded-md text-[10px] font-black uppercase transition-all ${
                      locale === lang ? 'bg-white/10 text-white border border-white/10' : 'text-gray-500 hover:text-gray-300'
                    }`}
                  >
                    {lang}
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-24 px-6 overflow-hidden">
        <div className="max-w-6xl mx-auto text-center relative">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-8 animate-fade-in">
            <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
            <span className="text-sm text-gray-300">{content.hero.badge}</span>
          </div>

          {/* Main Headline */}
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6 animate-fade-in-delay">
            <span className="bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
              {content.hero.title_1}
            </span>
            <br />
            <span className="bg-gradient-to-r from-purple-400 via-cyan-400 to-purple-400 bg-clip-text text-transparent">
              {content.hero.title_2}
            </span>
          </h1>

          {/* Subheadline */}
          <p className="text-xl md:text-2xl text-gray-400 mb-10 max-w-3xl mx-auto leading-relaxed animate-fade-in-delay-2">
            {content.hero.subtitle_1}
            <br className="hidden md:block" />
            <span className="text-white font-medium">{content.hero.subtitle_2}</span>
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center animate-fade-in-delay-3">
            <Link href={`/${locale}/register`} className="group px-8 py-4 bg-gradient-to-r from-purple-600 to-purple-500 rounded-xl font-bold text-lg hover:shadow-2xl hover:shadow-purple-500/30 transition-all hover:scale-105 flex items-center justify-center gap-2">
              {content.hero.cta_activate}
              <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </Link>
          </div>

          {/* Stats Bar */}
          <div className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-6 animate-fade-in-delay-4">
            {content.stats.map((stat: any, index: number) => (
              <div key={index} className="p-6 rounded-2xl bg-white/5 border border-white/10 hover:border-purple-500/30 transition-all group">
                <div className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent mb-2">
                  {stat.value}
                </div>
                <div className="text-sm text-gray-500 group-hover:text-gray-400 transition-colors">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Market Alternatives Section */}
      <section className="py-20 bg-white/5 border-y border-white/10">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-center text-sm font-semibold tracking-widest text-purple-400 uppercase mb-4">{content.market.title}</h2>
          <p className="text-center text-gray-400 mb-12">{content.market.subtitle}</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {content.marketAlternatives.map((alt: any, index: number) => (
              <div key={index} className="p-6 rounded-2xl bg-red-500/5 border border-red-500/20 hover:border-red-500/40 transition-all">
                <div className="text-lg font-bold text-red-400 mb-1">{alt.name}</div>
                <div className="text-xs text-gray-500 mb-2">{alt.category}</div>
                <div className="text-sm text-red-300">{alt.price}</div>
                <div className="text-xs text-red-400/70 mt-1">{alt.limit}</div>
              </div>
            ))}
          </div>
          <div className="text-center mt-8">
            <div className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-green-500/10 border border-green-500/30">
              <svg className="w-5 h-5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-green-400 font-medium">{content.market.fluxagent_value}</span>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 px-6 relative">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <span className="text-purple-400 text-sm font-semibold tracking-widest uppercase mb-4 block">{content.features.badge}</span>
            <h2 className="text-4xl md:text-5xl font-bold mb-6">
              {content.features.title_1}
              <br />
              <span className="bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">{content.features.title_2}</span>
            </h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              {content.features.subtitle}
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {featuresData.map((feature: any, index: number) => (
              <div
                key={index}
                className={`p-8 rounded-3xl border transition-all duration-300 cursor-pointer group ${
                  activeFeature === index
                    ? 'bg-gradient-to-br from-purple-500/10 to-cyan-500/5 border-purple-500/30'
                    : 'bg-white/5 border-white/10 hover:border-white/20'
                }`}
                onMouseEnter={() => setActiveFeature(index)}
              >
                <div className="flex items-start gap-6">
                  <div className={`p-4 rounded-2xl transition-all ${
                    activeFeature === index
                      ? 'bg-gradient-to-br from-purple-500 to-cyan-500 text-white'
                      : 'bg-white/10 text-gray-400 group-hover:text-white'
                  }`}>
                    {feature.icon}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-xl font-bold">{feature.title}</h3>
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        activeFeature === index
                          ? 'bg-purple-500/20 text-purple-300'
                          : 'bg-white/10 text-gray-400'
                      }`}>
                        {feature.highlight}
                      </span>
                    </div>
                    <p className="text-gray-400 leading-relaxed">{feature.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Comparison Section */}
      <section id="comparativa" className="py-24 px-6 relative bg-gradient-to-b from-transparent via-purple-950/20 to-transparent">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <span className="text-cyan-400 text-sm font-semibold tracking-widest uppercase mb-4 block">Comparativa</span>
            <h2 className="text-4xl md:text-5xl font-bold mb-6">
              La Libertad
              <br />
              <span className="bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">vs. El Taxímetro</span>
            </h2>
          </div>

          <div className="overflow-x-auto rounded-2xl border border-white/10 bg-white/5">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="p-6 text-gray-400 font-medium">Beneficio</th>
                  <th className="p-6 text-gray-400 font-medium">Competencia Típica</th>
                  <th className="p-6 text-purple-400 font-bold bg-purple-500/5">FluxAgent V2</th>
                </tr>
              </thead>
              <tbody>
                {content.comparison.map((row: any, index: number) => (
                  <tr key={index} className={`border-b border-white/5 ${row.highlight ? 'bg-green-500/5' : ''}`}>
                    <td className="p-6 font-medium">{row.benefit}</td>
                    <td className={`p-6 ${row.highlight ? 'text-red-400' : 'text-gray-400'}`}>{row.competitor}</td>
                    <td className="p-6 font-semibold bg-purple-500/5">
                      {row.highlight ? (
                        <span className="text-green-400 font-bold">{row.ventacore}</span>
                      ) : (
                        <span className="text-purple-300">{row.ventacore}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-24 px-6 relative">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <span className="text-purple-400 text-sm font-semibold tracking-widest uppercase mb-4 block">Planes</span>
            <h2 className="text-4xl md:text-5xl font-bold mb-6">
              Suscripción de Abundancia.
              <br />
              <span className="bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">Sin recargas, sin límites.</span>
            </h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              Paga una vez al mes y usa sin preocuparte por el consumo.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {plansData.map((plan: any, index: number) => (
              <div
                key={index}
                className={`relative p-8 rounded-3xl transition-all duration-300 ${
                  plan.recommended
                    ? 'bg-gradient-to-br from-purple-500/10 to-cyan-500/5 border-2 border-purple-500/50 scale-105 shadow-2xl shadow-purple-500/10'
                    : 'bg-white/5 border border-white/10 hover:border-white/20'
                }`}
              >
                {plan.recommended && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-gradient-to-r from-purple-600 to-cyan-600 rounded-full text-sm font-bold">
                    ⭐ Más Vendido
                  </div>
                )}

                <div className="text-center mb-6">
                  <div className="text-4xl mb-2">{plan.icon}</div>
                  <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>
                  <p className="text-gray-500 text-sm">{plan.tagline}</p>
                </div>

                <div className="text-center mb-8">
                  <span className="text-5xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                    ${plan.price}
                  </span>
                  <span className="text-gray-400">{plan.period}</span>
                </div>

                <ul className="space-y-4 mb-8">
                  {plan.features.map((feature: string, fIndex: number) => (
                    <li key={fIndex} className="flex items-start gap-3 text-gray-300">
                      <svg className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>

                <Link
                  href={`/${locale}/register`}
                  className={`block w-full py-4 rounded-xl font-bold text-center transition-all ${
                    plan.recommended
                      ? 'bg-gradient-to-r from-purple-600 to-cyan-600 hover:shadow-lg hover:shadow-purple-500/30 text-white'
                      : 'bg-white/10 hover:bg-white/15 border border-white/10'
                  }`}
                >
                  {plan.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-24 px-6 relative">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            {content.final_cta.title_1}
            <br />
            <span className="bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">{content.final_cta.title_2}</span>
          </h2>
          <p className="text-xl text-gray-400 mb-10 max-w-2xl mx-auto whitespace-pre-line">
            {content.final_cta.subtitle}
          </p>
          <Link href={`/${locale}/register`} className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-purple-600 to-cyan-600 rounded-xl font-bold text-lg hover:shadow-2xl hover:shadow-purple-500/30 transition-all hover:scale-105">
            {content.final_cta.button}
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </Link>
        </div>
      </section>

      {/* Enhanced Footer */}
      <footer className="py-16 px-6 bg-gradient-to-b from-transparent to-purple-950/20 border-t border-white/10">
        <div className="max-w-7xl mx-auto">
          {/* Main Footer Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 mb-12">
            {footerData.map((section: any, index: number) => (
              <div key={index} className="p-6 rounded-2xl bg-white/5 border border-white/10 hover:border-purple-500/30 transition-all">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 rounded-lg bg-purple-500/20 text-purple-400">
                    {section.icon}
                  </div>
                  <h3 className="text-lg font-bold text-white">{section.title}</h3>
                </div>
                <ul className="space-y-3">
                  {section.content.map((item: any, itemIndex: number) => (
                    <li key={itemIndex} className="flex items-start gap-2 text-sm text-gray-400">
                      <span className="flex-shrink-0 mt-0.5">{item.icon}</span>
                      <span>{item.text}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {/* Bottom Bar */}
          <div className="flex flex-col md:flex-row items-center justify-between gap-4 pt-6 border-t border-white/5">
            <div className="flex items-center gap-6 text-sm text-gray-500">
              <a href="#" className="hover:text-white transition-colors flex items-center gap-1">Privacidad</a>
              <a href="#" className="hover:text-white transition-colors flex items-center gap-1">Términos</a>
              <Link href={`/${locale}/login`} className="hover:text-white transition-colors flex items-center gap-1">Portal</Link>
            </div>
            <div className="text-sm text-gray-500">
              {content.footer.rights}
            </div>
          </div>
        </div>
      </footer>

      {/* Floating Chat Widget */}
      <div className="fixed bottom-6 right-6 z-50">
        {chatOpen ? (
          <div className="w-80 sm:w-96 rounded-2xl bg-[#1a1a2e] border border-white/10 shadow-2xl shadow-purple-500/20 overflow-hidden">
            {/* Chat Header */}
            <div className="bg-gradient-to-r from-purple-600 to-cyan-600 px-4 py-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
                <div>
                  <div className="text-white font-semibold text-sm">FluxAgent V2</div>
                  <div className="text-white/70 text-xs">Asistente Virtual</div>
                </div>
              </div>
              <button onClick={() => setChatOpen(false)} className="text-white/70 hover:text-white transition-colors">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Chat Messages */}
            <div className="h-80 overflow-y-auto p-4 space-y-4">
              {chatMessages.map((msg, index) => (
                <div key={index} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div
                    className={`max-w-[80%] px-4 py-2 rounded-2xl text-sm ${
                      msg.sender === 'user'
                        ? 'bg-purple-600 text-white rounded-br-md'
                        : 'bg-white/10 text-gray-300 rounded-bl-md'
                    }`}
                  >
                    {msg.text}
                  </div>
                </div>
              ))}
            </div>

            {/* Chat Input */}
            <form onSubmit={handleChatSubmit} className="p-4 border-t border-white/10">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder="Escribe tu mensaje..."
                  className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                />
                <button type="submit" className="px-4 py-2 bg-gradient-to-r from-purple-600 to-cyan-600 rounded-xl hover:opacity-90 transition-opacity">
                  <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </button>
              </div>
            </form>
          </div>
        ) : (
          <button
            onClick={() => setChatOpen(true)}
            className="group relative w-16 h-16 rounded-full bg-gradient-to-r from-purple-600 to-cyan-600 shadow-lg shadow-purple-500/30 hover:shadow-purple-500/50 transition-all hover:scale-105 flex items-center justify-center"
          >
            <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <span className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-400 rounded-full border-2 border-[#0a0a0f] animate-pulse"></span>
          </button>
        )}
      </div>
    </div>
  );
}
