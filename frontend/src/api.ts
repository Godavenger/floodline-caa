export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set('X-Floodline-Client', 'web');
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  const response = await fetch(`/api${path}`, { ...options, headers, credentials: 'include' });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = typeof data.detail === 'string' ? data.detail
      : Array.isArray(data.detail) ? data.detail.map((error: { msg: string }) => error.msg).join('. ')
      : `The request failed (${response.status}). Please try again.`;
    throw new ApiError(message, response.status);
  }
  return data as T;
}

export const post = <T,>(path: string, body?: unknown) => api<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) });
export const time = (value: string | null | undefined) => value ? new Intl.DateTimeFormat('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(value)) + ' IST' : 'Unavailable';
export const dateTime = (value: string) => new Intl.DateTimeFormat('en-IN', { timeZone: 'Asia/Kolkata', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(value)) + ' IST';
export const number = (value: number | null | undefined, decimals = 1) => value == null ? '—' : value.toLocaleString('en-IN', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
export const riskWord = (level: string) => ({ low: 'Monitor', elevated: 'Elevated', high: 'High', unknown: 'Unknown' }[level] ?? level);
export const severityWord = (severity: string) => ({ water_on_road: 'Water on road', slow_passage: 'Passage affected', impassable: 'Road impassable', unknown: 'Severity uncertain' }[severity] ?? severity);

// datetime-local is a device-local value. Convert it with the device offset, never add a fixed IST suffix.
export function localInputTime(utc: string) {
  const value = new Date(utc);
  const local = new Date(value.getTime() - value.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 16);
}
