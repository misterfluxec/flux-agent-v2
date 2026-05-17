export type UserRole = 'user' | 'admin' | 'super_admin';

export interface UserSession {
  id: string;
  email: string;
  role: UserRole;
  tenant_id: string;
  name: string;
  avatar?: string;
  organization_name?: string;
}
