import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api';
const ACCESS_KEY = 'carebridge.access';
const REFRESH_KEY = 'carebridge.refresh';

export const api = axios.create({ baseURL: API_BASE_URL, timeout: 20000 });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(ACCESS_KEY);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshPromise = null;
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && original && !original._retry && !original.url?.includes('/auth/token/')) {
      const refresh = localStorage.getItem(REFRESH_KEY);
      if (!refresh) {
        localStorage.removeItem(ACCESS_KEY);
        window.dispatchEvent(new CustomEvent('carebridge:session-expired'));
        return Promise.reject(error);
      }
      original._retry = true;
      try {
        if (!refreshPromise) {
          refreshPromise = axios.post(`${API_BASE_URL}/auth/token/refresh/`, { refresh })
            .then(({ data }) => {
              localStorage.setItem(ACCESS_KEY, data.access);
              if (data.refresh) localStorage.setItem(REFRESH_KEY, data.refresh);
              return data.access;
            })
            .finally(() => { refreshPromise = null; });
        }
        const access = await refreshPromise;
        original.headers = original.headers || {};
        original.headers.Authorization = `Bearer ${access}`;
        return api(original);
      } catch (refreshError) {
        localStorage.removeItem(ACCESS_KEY);
        localStorage.removeItem(REFRESH_KEY);
        window.dispatchEvent(new CustomEvent('carebridge:session-expired'));
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  },
);

export const authApi = {
  login: (credentials) => api.post('/auth/token/', credentials),
  me: () => api.get('/auth/me/'),
  updateMe: (payload) => api.patch('/auth/me/', payload),
  changePassword: (payload) => api.post('/auth/me/', payload),
};

export const resources = {
  patients: '/patients/',
  doctors: '/doctors/',
  availabilities: '/availabilities/',
  appointments: '/appointments/',
  prescriptions: '/prescriptions/',
  invoices: '/invoices/',
  payments: '/payments/',
};

export async function getList(path, params = {}) {
  const firstResponse = await api.get(path, { params });
  const firstData = firstResponse.data;
  if (Array.isArray(firstData)) return firstData;

  const results = [...(firstData?.results || [])];
  let next = firstData?.next;
  // DRF uses absolute URLs for `next`; Axios accepts those directly and the
  // auth interceptor continues to attach the current access token.
  const visited = new Set();
  while (next && !visited.has(next)) {
    visited.add(next);
    const { data } = await api.get(next);
    if (Array.isArray(data)) {
      results.push(...data);
      break;
    }
    results.push(...(data?.results || []));
    next = data?.next;
  }
  return results;
}

export function getErrorMessage(error) {
  const data = error?.response?.data;
  if (!data) return error?.message || 'Something went wrong. Please try again.';
  if (typeof data.detail === 'string') return data.detail;
  if (typeof data === 'string') return data;
  const messages = Object.entries(data).flatMap(([key, value]) => {
    const text = Array.isArray(value) ? value.join(' ') : typeof value === 'object' && value !== null ? JSON.stringify(value) : String(value);
    return [`${key.replaceAll('_', ' ')}: ${text}`];
  });
  return messages.join(' · ') || 'Request failed. Please check your information.';
}

export const tokenStorage = {
  ACCESS_KEY,
  REFRESH_KEY,
  set: (access, refresh) => {
    localStorage.setItem(ACCESS_KEY, access);
    localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear: () => {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};
