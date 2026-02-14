export const config = {
  apiUrl: import.meta.env.VITE_API_URL || '/api/v1',
  auth: {
    clientId: import.meta.env.VITE_AZURE_CLIENT_ID || '',
    authority: import.meta.env.VITE_AZURE_AUTHORITY || 'https://login.microsoftonline.com/common',
    bypassAuth: String(import.meta.env.VITE_BYPASS_AUTH).toLowerCase() === 'true'
  }
};
