import { apiClient } from "@/lib/api-client";

// ─── LEGACY: PRODUCTOS (depreciado → usar CatalogItem) ─────────────────────

export interface ProductData {
  id: string;
  codigo?: string | null;
  name: string;
  price: number;
  stock: number;
  status?: string;
  categoria?: string;
  description?: string | null;
  metadata?: any;
}

// ─── CATÁLOGO UNIFICADO (catalog_items) ─────────────────────────────────────

export type CatalogItemType = 'physical_product' | 'digital' | 'service' | 'booking' | 'subscription';

export interface CatalogItemVariant {
  id: string;
  name: string; // e.g., "M - Rojo"
  sku?: string;
  price_override?: number;
  stock_quantity: number;
  attributes: Record<string, string>; // e.g., { "size": "M", "color": "Rojo" }
}

export interface CatalogPromotion {
  id: string;
  name: string;
  description?: string;
  discount_type: 'percentage' | 'fixed_amount';
  discount_value: number;
  start_date: string;
  end_date: string;
  target_products?: string[]; // IDs of products
  target_tags?: string[];
  is_active: boolean;
}

export interface CatalogItem {
  id: string;
  type: CatalogItemType;
  name: string;
  description?: string | null;
  base_price: number;
  currency: string;
  stock_quantity: number;
  status: string;
  capabilities?: Record<string, any>;
  metadata?: {
    variants?: CatalogItemVariant[];
    [key: string]: any;
  };
}

export interface CatalogItemCreate {
  type: CatalogItemType;
  name: string;
  description?: string;
  base_price: number;
  currency?: string;
  capabilities?: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface CatalogItemUpdate {
  name?: string;
  description?: string;
  base_price?: number;
  stock_quantity?: number;
  status?: string;
}

export interface InventoryResponse {
  productos: ProductData[];
  total: number;
}

export async function fetchProducts(): Promise<ProductData[]> {
  const { data } = await apiClient.get<ProductData[]>("/products");
  return data;
}

export async function updateProduct(id: string, updates: { price?: number; stock?: number }): Promise<{ mensaje: string }> {
  const { data } = await apiClient.patch<{ mensaje: string }>(`/products/${id}`, updates);
  return data;
}

export async function uploadInventory(file: File): Promise<{ mensaje: string; catalog_size: number }> {
  const form = new FormData();
  form.append("file", file);

  const { data } = await apiClient.post<{ mensaje: string; catalog_size: number }>("/inventory/upload", form);
  return data;
}

export async function syncShopify(shopUrl: string, accessToken: string): Promise<{ mensaje: string }> {
  const { data } = await apiClient.post<{ mensaje: string }>("/inventory/sync/shopify", {
    shop_url: shopUrl,
    access_token: accessToken,
  });
  return data;
}

// ─── COTIZACIONES (QUOTES) ────────────────────────────────────────────────

export interface QuoteItem {
  id?: string;
  quote_id?: string;
  product_id?: string;
  description: string;
  quantity: number;
  unit_price: number;
  subtotal?: number;
}

export interface Quote {
  id: string;
  tenant_id: string;
  customer_id: string;
  status: 'draft' | 'sent' | 'accepted' | 'rejected' | 'expired';
  total: number;
  valid_until?: string;
  items: QuoteItem[];
  created_at: string;
}

export async function getQuotes(params?: { status?: string; limit?: number }): Promise<Quote[]> {
  const qs = params ? `?${new URLSearchParams(params as any).toString()}` : '';
  const { data } = await apiClient.get<Quote[]>(`/commerce/quotes${qs}`);
  return data;
}

export async function getQuote(id: string): Promise<Quote> {
  const { data } = await apiClient.get<Quote>(`/commerce/quotes/${id}`);
  return data;
}

export async function createQuote(payload: { customer_id: string; items: Partial<QuoteItem>[] }): Promise<Quote> {
  const { data } = await apiClient.post<Quote>('/commerce/quotes', payload);
  return data;
}

export async function updateQuote(id: string, payload: Partial<Quote>): Promise<Quote> {
  const { data } = await apiClient.patch<Quote>(`/commerce/quotes/${id}`, payload);
  return data;
}

export async function approveQuote(id: string): Promise<Quote> {
  const { data } = await apiClient.patch<Quote>(`/commerce/quotes/${id}`, { status: 'accepted' });
  return data;
}

// ─── ÓRDENES (ORDERS) ────────────────────────────────────────────────────

export interface OrderAction {
  id: string;
  label: string;
  variant: string;
  requires_confirmation: boolean;
}

export interface Order {
  id: string;
  quote_id?: string;
  customer_id: string;
  status: 'pending' | 'confirmed' | 'processing' | 'paid' | 'shipped' | 'delivered' | 'completed' | 'cancelled' | 'refunded';
  total_amount: number;
  payment_status: 'unpaid' | 'pending' | 'paid' | 'refunded';
  payment_method?: string;
  created_at: string;
  available_actions?: OrderAction[];
}

export async function convertQuoteToOrder(quoteId: string): Promise<Order> {
  const { data } = await apiClient.post<Order>(`/commerce/quotes/${quoteId}/convert`, {});
  return data;
}

export async function getOrders(params?: { status?: string; customer_id?: string; limit?: number }): Promise<Order[]> {
  const qs = params ? `?${new URLSearchParams(params as any).toString()}` : '';
  const { data } = await apiClient.get<Order[]>(`/commerce/orders${qs}`);
  return data;
}

export async function getOrder(id: string): Promise<Order> {
  const { data } = await apiClient.get<Order>(`/commerce/orders/${id}`);
  return data;
}

export async function fulfillOrder(id: string, payload: { status: string, note?: string }): Promise<any> {
  const { data } = await apiClient.patch(`/commerce/orders/${id}/fulfill`, payload);
  return data;
}

// ─── FACTURACIÓN OPERACIONAL ───────────────────────────────────────────────────

export async function generateReceipt(order_id: string): Promise<{ invoice_id: string, receipt_number: string, status: string }> {
  const { data } = await apiClient.post(`/invoices/from-order/${order_id}`);
  return data;
}

export async function getInvoice(id: string): Promise<any> {
  const { data } = await apiClient.get(`/invoices/${id}`);
  return data;
}

// ─── PAGOS (PAYMENTS) ────────────────────────────────────────────────────

export interface PaymentLink {
  payment_url: string;
  preference_id: string;
}

export async function createPaymentLink(orderId: string): Promise<PaymentLink> {
  const { data } = await apiClient.post<PaymentLink>(`/commerce/orders/${orderId}/payment`, {});
  return data;
}

export async function getCommerceSummary(): Promise<{ total_quotes: number; total_orders: number; revenue_today: number }> {
  const { data } = await apiClient.get<{ total_quotes: number; total_orders: number; revenue_today: number }>('/commerce/summary');
  return data;
}

// ─── CATÁLOGO API (conecta con catalog_router.py) ───────────────────────────

export async function getCatalogItems(): Promise<CatalogItem[]> {
  const { data } = await apiClient.get<CatalogItem[]>('/catalog');
  return data;
}

export async function updateCatalogItem(id: string, updates: CatalogItemUpdate): Promise<{ mensaje: string }> {
  const { data } = await apiClient.patch<{ mensaje: string }>(`/catalog/${id}`, updates);
  return data;
}

export async function importCatalogBulk(items: Record<string, any>[], updateExisting = true): Promise<{ mensaje: string; procesados: number; errores: number }> {
  const { data } = await apiClient.post<{ mensaje: string; procesados: number; errores: number }>('/catalog/import', {
    items,
    update_existing: updateExisting
  });
  return data;
}

// ─── PROMOCIONES API ─────────────────────────────────────────────────────────

export async function getPromotions(): Promise<CatalogPromotion[]> {
  const { data } = await apiClient.get<CatalogPromotion[]>('/commerce/promotions');
  return data;
}

export async function createPromotion(payload: Omit<CatalogPromotion, 'id'>): Promise<CatalogPromotion> {
  const { data } = await apiClient.post<CatalogPromotion>('/commerce/promotions', payload);
  return data;
}

export async function updatePromotion(id: string, updates: Partial<CatalogPromotion>): Promise<CatalogPromotion> {
  const { data } = await apiClient.patch<CatalogPromotion>(`/commerce/promotions/${id}`, updates);
  return data;
}

export async function deletePromotion(id: string): Promise<{ mensaje: string }> {
  const { data } = await apiClient.delete<{ mensaje: string }>(`/commerce/promotions/${id}`);
  return data;
}
