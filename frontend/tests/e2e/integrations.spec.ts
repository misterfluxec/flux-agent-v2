import { test, expect } from '@playwright/test';

test.describe('Integration Wizard E2E', () => {
  test('should complete the integration wizard flow', async ({ page }) => {
    // Interceptar la llamada de configuración de sesión
    await page.route('**/api/v1/integrations/sessions', async route => {
      const json = { session_id: 'test-session-123', status: 'configuring', provider: 'sqlserver' };
      await route.fulfill({ json });
    });

    // Interceptar el test de conexión
    await page.route('**/api/v1/integrations/sessions/*/test', async route => {
      const json = { status: 'discovering', message: 'Connection successful' };
      await route.fulfill({ json });
    });

    // Interceptar el trigger de discovery
    await page.route('**/api/v1/integrations/sessions/*/discover', async route => {
      const json = { status: 'discovering', message: 'Discovery started' };
      await route.fulfill({ json });
    });

    // Interceptar el polling (simulamos que el discovery terminó rápidamente)
    await page.route('**/api/v1/integrations/sessions/*', async route => {
      if (route.request().method() === 'GET') {
        const json = {
          session_id: 'test-session-123',
          status: 'mapping',
          discovered_schema: {
            tables: [
              { name: 'customers', columns: [{ name: 'id' }, { name: 'email' }] }
            ]
          }
        };
        await route.fulfill({ json });
      } else {
        await route.continue();
      }
    });

    // Navegar a la página de integraciones (asumimos la ruta /es/dashboard/integrations)
    await page.goto('/es/dashboard/integrations');

    // Esperar a que la página cargue y hacer click en un botón de conectar SQL Server
    const sqlServerCard = page.locator('div').filter({ hasText: 'SQL Server' }).first();
    await expect(sqlServerCard).toBeVisible();
    
    // Asumimos que hay un botón de Conectar dentro de la card
    const connectButton = sqlServerCard.locator('button', { hasText: 'Conectar' }).first();
    await connectButton.click();

    // Ahora deberíamos ver el formulario de credenciales
    await expect(page.locator('text=Configurar Conexión')).toBeVisible();

    // Llenar el formulario (ajustar selectores según el UI real)
    await page.fill('input[placeholder="Host"]', 'localhost');
    await page.fill('input[placeholder="Usuario"]', 'sa');
    await page.fill('input[placeholder="Contraseña"]', 'Password123');

    // Click en Test Connection
    await page.click('button:has-text("Test Connection")');

    // Debería avanzar a la pantalla de Canonical Mapper
    await expect(page.locator('text=Canonical Mapper')).toBeVisible();
    
    // Verificar que se haya renderizado el esquema
    await expect(page.locator('text=customers')).toBeVisible();
  });
});
