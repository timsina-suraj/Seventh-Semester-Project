import axios from "axios";

const KEY_TOKEN    = "medishield_token";
const KEY_ROLE     = "medishield_role";
const KEY_EMAIL = "medishield_email";
const KEY_FULL_NAME = "medishield_full_name";

const client = axios.create({
  baseURL: "/api",
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem(KEY_TOKEN);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(KEY_TOKEN);
      localStorage.removeItem(KEY_ROLE);
      localStorage.removeItem(KEY_EMAIL);
      localStorage.removeItem(KEY_FULL_NAME);
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default client;
export { KEY_TOKEN, KEY_ROLE, KEY_EMAIL, KEY_FULL_NAME };
