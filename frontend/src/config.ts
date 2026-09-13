let _apiBase = import.meta.env.VITE_API_BASE_URL;
if (!_apiBase || _apiBase === '/' || _apiBase === '' || _apiBase.includes('localhost') || _apiBase.includes('127.0.0.1') || _apiBase.includes('vercel.app')) {
  _apiBase = 'https://causen.onrender.com';
}
if (_apiBase.endsWith('/')) {
  _apiBase = _apiBase.slice(0, -1);
}
export const API_BASE_URL = _apiBase;
