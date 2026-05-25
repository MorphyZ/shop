import axios from "axios";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const STORAGE_KEY = "shop_auth";

export function loadAuth() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return { username: "", password: "" };
    }
    const parsed = JSON.parse(raw);
    return {
      username: parsed.username || "",
      password: parsed.password || "",
    };
  } catch {
    return { username: "", password: "" };
  }
}

export function saveAuth(auth) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(auth));
}

export function clearAuth() {
  localStorage.removeItem(STORAGE_KEY);
}

function makeAuthHeader(auth) {
  const token = btoa(`${auth.username}:${auth.password}`);
  return `Basic ${token}`;
}

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
});

api.interceptors.request.use((config) => {
  const auth = loadAuth();
  if (auth.username && auth.password) {
    config.headers.Authorization = makeAuthHeader(auth);
  }
  config.headers.Accept = "application/json";
  return config;
});

export async function apiGet(path, params = {}) {
  const response = await api.get(path, { params });
  return response.data;
}

export async function apiPost(path, payload = {}) {
  const response = await api.post(path, payload);
  return response.data;
}

export async function apiPatch(path, payload = {}) {
  const response = await api.patch(path, payload);
  return response.data;
}

export async function apiDelete(path) {
  const response = await api.delete(path);
  return response.data;
}

