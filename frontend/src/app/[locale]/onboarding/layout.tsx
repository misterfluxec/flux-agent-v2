export default function OnboardingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4 md:p-8 relative overflow-hidden">
      {/* Background gradient subtle */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-secondary/5 pointer-events-none" />
      
      <div className="w-full max-w-3xl relative z-10 animate-in fade-in duration-700">
        <div className="text-center mb-8">
          <span className="text-2xl font-bold bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">
            FluxAgent
          </span>
        </div>
        {children}
      </div>
    </div>
  );
}
