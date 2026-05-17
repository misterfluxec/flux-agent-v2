import React from 'react';

interface PermissionGateProps {
  feature: string;
  behavior?: "hide" | "disable" | "upsell";
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function PermissionGate({ feature, behavior = "hide", children, fallback = null }: PermissionGateProps) {
  // TODO: Replace with real RBAC engine (e.g., checking user.features.includes(feature))
  // For Sprint 1, we assume the user has the required features.
  const hasPermission = true;

  if (!hasPermission) {
    if (behavior === "hide") return null;
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
