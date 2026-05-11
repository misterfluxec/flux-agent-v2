import React from "react";

interface ActionableButtonProps {
  label: string;
  onClick?: () => void;
  variant?: "default" | "danger" | "ghost";
  disabled?: boolean;
  icon?: string;
}

const variantStyles = {
  default: "border-neutral-700 text-neutral-300 hover:border-neutral-500 hover:text-white hover:bg-neutral-800",
  danger:  "border-rose-800 text-rose-400 hover:border-rose-600 hover:text-rose-300 hover:bg-rose-950",
  ghost:   "border-transparent text-neutral-500 hover:text-neutral-300 hover:border-neutral-800",
};

export function ActionableButton({ label, onClick, variant = "default", disabled = false, icon }: ActionableButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-xs font-medium 
        transition-all duration-150 cursor-pointer select-none
        disabled:opacity-40 disabled:cursor-not-allowed
        ${variantStyles[variant]}
      `}
    >
      {icon && <span className="text-sm">{icon}</span>}
      {label}
    </button>
  );
}
