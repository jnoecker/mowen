const BASE_URL = '/api/v1';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const { headers: customHeaders, ...rest } = options ?? {};
  const resp = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...customHeaders },
    ...rest,
  });
  if (!resp.ok) {
    const error = await resp.json().catch(() => ({ detail: resp.statusText }));
    let message = resp.statusText;
    if (typeof error.detail === 'string') {
      message = error.detail;
    } else if (Array.isArray(error.detail)) {
      // FastAPI Pydantic validation errors return detail as an array of objects
      message = error.detail
        .map((e: { msg?: string; loc?: string[] }) => {
          const loc = e.loc ? e.loc.join(' > ') : '';
          return loc ? `${loc}: ${e.msg}` : (e.msg || '');
        })
        .join('; ');
    }
    throw new Error(message);
  }
  if (resp.status === 204) return undefined as T;
  return resp.json();
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: BodyInit | object) =>
    request<T>(path, {
      method: 'POST',
      body: body instanceof FormData ? body : JSON.stringify(body),
      headers: body instanceof FormData ? {} : undefined,
    }),
  patch: <T>(path: string, body: object) =>
    request<T>(path, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
  delete: <T = void>(path: string, body?: object) =>
    request<T>(path, {
      method: 'DELETE',
      body: body ? JSON.stringify(body) : undefined,
    }),
};
