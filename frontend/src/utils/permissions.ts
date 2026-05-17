import { UserRole } from '@/types/auth';

/**
 * Jerarquía de roles: mayor valor significa mayor privilegio.
 */
const ROLE_HIERARCHY: Record<UserRole, number> = {
  user: 1,
  admin: 2,
  super_admin: 3,
};

/**
 * Valida si un role tiene acceso a un recurso que requiere roles mínimos.
 * 
 * @example
 * canAccess('admin', ['super_admin']) -> false (admin es nivel 2, se requiere nivel 3)
 * canAccess('super_admin', ['admin']) -> true (super_admin es nivel 3, se requiere nivel 2)
 */
export const canAccess = (userRole: UserRole, requiredRoles: UserRole[]): boolean => {
  if (requiredRoles.length === 0) return true;
  
  // Nivel mínimo requerido entre los roles permitidos
  const minRequiredLevel = Math.min(...requiredRoles.map(r => ROLE_HIERARCHY[r]));
  
  return ROLE_HIERARCHY[userRole] >= minRequiredLevel;
};

/** Helpers de utilidad rápida */
export const isAdmin = (role: UserRole) => role === 'admin' || role === 'super_admin';
export const isSuperAdmin = (role: UserRole) => role === 'super_admin';
