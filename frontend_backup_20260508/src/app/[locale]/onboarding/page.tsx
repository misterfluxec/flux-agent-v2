'use client';

import { useOnboardingWizard, OnboardingData } from '@/hooks/useOnboardingWizard';
import { WizardStepper } from '@/components/onboarding/WizardStepper';
import { StepIdentity } from '@/components/onboarding/StepIdentity';
import { StepIndustry } from '@/components/onboarding/StepIndustry';
import { StepKnowledge } from '@/components/onboarding/StepKnowledge';
import { StepConnect } from '@/components/onboarding/StepConnect';
import { StepComplete } from '@/components/onboarding/StepComplete';

export default function OnboardingPage() {
  const { step, data, isLoading, updateData, nextStep, prevStep, submitOnboarding } = useOnboardingWizard();

  const handleUpdate = (field: keyof OnboardingData, value: any) => {
    updateData({ [field]: value });
  };

  return (
    <div className="bg-card border border-white/5 rounded-2xl p-6 md:p-8 shadow-2xl backdrop-blur-md max-w-4xl mx-auto w-full">
      <WizardStepper currentStep={step} />
      <div className="mt-8">
        {step === 1 && <StepIdentity data={data} onChange={handleUpdate} onNext={nextStep} />}
        {step === 2 && <StepIndustry data={data} onChange={handleUpdate} onNext={nextStep} onBack={prevStep} />}
        {step === 3 && <StepKnowledge data={data} onChange={handleUpdate} onNext={nextStep} onBack={prevStep} />}
        {step === 4 && <StepConnect data={data} onChange={handleUpdate} onNext={nextStep} onBack={prevStep} />}
        {step === 5 && <StepComplete isLoading={isLoading} onSubmit={submitOnboarding} onBack={prevStep} />}
      </div>
    </div>
  );
}
