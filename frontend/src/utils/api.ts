import AsyncStorage from '@react-native-async-storage/async-storage';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export async function apiRequest(method: string, path: string, body?: any) {
  const token = await AsyncStorage.getItem('access_token');
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_URL}/api${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail) || 'Erreur serveur');
  }
  return data;
}

export const api = {
  get: (path: string) => apiRequest('GET', path),
  post: (path: string, body?: any) => apiRequest('POST', path, body),
  put: (path: string, body?: any) => apiRequest('PUT', path, body),
  delete: (path: string) => apiRequest('DELETE', path),
};
