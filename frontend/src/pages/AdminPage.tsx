import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle, AlertCircle } from 'lucide-react';
import { config } from '../config';
import { useMsal } from "@azure/msal-react";
import { loginRequest } from '../authConfig';

interface ModelConfig {
  id: string;
  name: string;
  provider: string;
  is_active: boolean;
}

const AdminPage = () => {
  const navigate = useNavigate();
  const { instance, accounts } = useMsal();

  const [models, setModels] = useState<ModelConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [ingestionLogs, setIngestionLogs] = useState<string[]>([]);

  const getToken = async () => {
    const account = accounts[0];
    if (!account) return "mock-token";
    if (config.auth.bypassAuth) return "mock-token";

    try {
      const response = await instance.acquireTokenSilent({
        ...loginRequest,
        account: account
      });
      return response.idToken;
    } catch {
      return "mock-token";
    }
  };

  const fetchModels = async () => {
    try {
      setLoading(true);
      const token = await getToken();
      const res = await fetch(`${config.apiUrl}/admin/models`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("Failed to fetch models");
      const data = await res.json();
      setModels(data);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError(String(err));
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {

    fetchModels();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [instance, accounts]);

  const handleModelChange = async (modelId: string) => {
    try {
      const token = await getToken();
      const model = models.find(m => m.id === modelId);
      if (!model) return;

      // Update backend
      // We need to set this model to active. 
      // The backend PUT /models/{id} accepts the full config object.
      // We should construct it with is_active=True
      const updatedConfig = { ...model, is_active: true };

      const res = await fetch(`${config.apiUrl}/admin/models/${modelId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(updatedConfig)
      });

      if (!res.ok) throw new Error("Failed to update model");

      // Refresh list to see changes (other models becoming inactive)
      await fetchModels();
      setSuccessMsg(`Switched to ${model.name}`);
      setTimeout(() => setSuccessMsg(null), 3000);

    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError(String(err));
      }
    }
  };

  const activeModelId = models.find(m => m.is_active)?.id || "";

  return (
    <div className="p-4 w-full h-full overflow-auto">
      <button
        onClick={() => navigate('/')}
        className="mb-4 flex items-center text-gray-500 hover:text-gray-900 transition-colors"
      >
        <ArrowLeft size={20} className="mr-2" />
        Back to Chat
      </button>
      <h1 className="text-2xl font-bold text-gray-900 mb-6 px-2">Admin Configuration</h1>

      {error && (
        <div className="mb-4 p-4 bg-red-50 text-red-700 rounded-lg flex items-center mx-2">
          <AlertCircle className="mr-2" size={20} />
          {error}
        </div>
      )}

      {successMsg && (
        <div className="mb-4 p-4 bg-green-50 text-green-700 rounded-lg flex items-center mx-2">
          <CheckCircle className="mr-2" size={20} />
          {successMsg}
        </div>
      )}

      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">LLM Configuration</h2>

        {loading ? (
          <div>Loading models...</div>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Active Model (Synced with Backend)</label>
              <select
                value={activeModelId}
                onChange={(e) => handleModelChange(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 bg-white"
              >
                {models.map(m => (
                  <option key={m.id} value={m.id}>
                    {m.name} ({m.provider}) {m.is_active ? "-- Active" : ""}
                  </option>
                ))}
              </select>
              <div className="mt-2 text-xs text-gray-500">
                Switching models will restart the backend LLM service for the next request.
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4">Data Sources</h2>
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg mb-4">
          <div>
            <div className="font-medium">Primary Knowledge Base</div>
            <div className="text-sm text-gray-500">Local Vector DB (Qdrant)</div>
          </div>
          <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">Connected</span>
        </div>

        <div className="p-4 bg-gray-50 rounded-lg w-full">
          <div className="flex items-center justify-between mb-2">
            <div className="font-medium">Ingestion Control</div>
            <button
              onClick={async () => {
                setIngestionLogs(["Starting ingestion..."]);
                try {
                  const token = await getToken();
                  // Use fetch to get a readable stream
                  const response = await fetch(`${config.apiUrl}/admin/upload-and-ingest`, {
                    method: 'POST',
                    headers: {
                      'Authorization': `Bearer ${token}`
                    }
                  });

                  if (!response.body) {
                    setIngestionLogs(prev => [...prev, "❌ No response body received."]);
                    return;
                  }

                  const reader = response.body.getReader();
                  const decoder = new TextDecoder("utf-8");

                  while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    const chunk = decoder.decode(value, { stream: true });
                    // Split by newlines and filter empty strings
                    const lines = chunk.split('\n').filter(Boolean);
                    setIngestionLogs(prev => [...prev, ...lines]);
                  }
                } catch (e) {
                  setIngestionLogs(prev => [...prev, `❌ Error: ${e}`]);
                }
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
            >
              Trigger Upload & Ingest
            </button>
          </div>

          <div className="bg-gray-900 text-green-400 font-mono text-xs p-3 rounded-lg h-[800px] overflow-y-auto w-full">
            {ingestionLogs.length === 0 ? (
              <span className="text-gray-500">// Logs will appear here...</span>
            ) : (
              ingestionLogs.map((log, i) => (
                <div key={i}>{log}</div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminPage;
