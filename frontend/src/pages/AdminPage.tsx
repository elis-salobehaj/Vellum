import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle, AlertCircle, ChevronDown, ChevronUp, Play, Database } from 'lucide-react';
import { config } from '../config';
import { useMsal } from "@azure/msal-react";
import { loginRequest } from '../authConfig';
import { logger } from '../lib/logger';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';

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
  const [isLogsOpen, setIsLogsOpen] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);

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
    } catch (err) {
      logger.debug("admin_token_acquire_silent_failed", { error: err });
      return "mock-token";
    }
  };

  const fetchModels = async () => {
    try {
      setLoading(true);
      const token = await getToken();
      logger.info("admin_fetching_models");
      const res = await fetch(`${config.apiUrl}/admin/models`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("Failed to fetch models");
      const data = await res.json();
      logger.debug("admin_models_received", { count: data.length });
      setModels(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      logger.error("admin_fetch_models_failed", { error: msg });
      setError(msg);
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
      logger.info("admin_switching_model", { modelId });
      const token = await getToken();
      const model = models.find(m => m.id === modelId);
      if (!model) return;

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

      await fetchModels();
      logger.info("admin_switch_model_success", { modelId });
      setSuccessMsg(`Switched to ${model.name}`);
      setTimeout(() => setSuccessMsg(null), 3000);

    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      logger.error("admin_switch_model_failed", { modelId, error: msg });
      setError(msg);
    }
  };

  const handleIngest = async () => {
    logger.info("admin_trigger_ingest_start");
    setIngestionLogs(["Starting ingestion..."]);
    setIsLogsOpen(true); // Auto-expand logs when starting ingestion
    setIsIngesting(true);

    try {
      const token = await getToken();
      const response = await fetch(`${config.apiUrl}/admin/upload-and-ingest`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.body) {
        logger.error("admin_ingest_no_body");
        setIngestionLogs(prev => [...prev, "❌ No response body received."]);
        setIsIngesting(false);
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n').filter(Boolean);
        setIngestionLogs(prev => [...prev, ...lines]);
        logger.debug("admin_ingest_logs_chunk", { count: lines.length });
      }
      logger.info("admin_ingest_stream_complete");
    } catch (e) {
      logger.error("admin_ingest_failed", { error: e });
      setIngestionLogs(prev => [...prev, `❌ Error: ${e}`]);
    } finally {
      setIsIngesting(false);
    }
  };

  const activeModelId = models.find(m => m.is_active)?.id || "";

  return (
    <div className="p-6 w-full h-full overflow-auto bg-muted/30">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <Button
              variant="ghost"
              onClick={() => navigate('/')}
              className="mb-2 -ml-2 text-muted-foreground hover:text-foreground"
            >
              <ArrowLeft size={16} className="mr-2" />
              Back to Chat
            </Button>
            <h1 className="text-3xl font-bold tracking-tight">Admin Configuration</h1>
            <p className="text-muted-foreground mt-1">Manage models, data sources, and ingestion</p>
          </div>
        </div>

        {/* Alerts */}
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {successMsg && (
          <Alert className="border-green-200 bg-green-50 text-green-900">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription>{successMsg}</AlertDescription>
          </Alert>
        )}

        {/* LLM Configuration */}
        <Card>
          <CardHeader>
            <CardTitle>LLM Configuration</CardTitle>
            <CardDescription>Select the active language model for chat responses</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-sm text-muted-foreground">Loading models...</div>
            ) : (
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Active Model (Synced with Backend)</label>
                  <Select value={activeModelId} onValueChange={handleModelChange}>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select a model" />
                    </SelectTrigger>
                    <SelectContent className="!bg-background">
                      {models.map(m => (
                        <SelectItem key={m.id} value={m.id}>
                          <div className="flex items-center gap-2">
                            <span>{m.name}</span>
                            <span className="text-xs text-muted-foreground">({m.provider})</span>
                            {m.is_active && <Badge variant="outline" className="ml-2 text-[10px] px-1">Active</Badge>}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">
                    Switching models will restart the backend LLM service for the next request.
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Data Sources */}
        <Card>
          <CardHeader>
            <CardTitle>Data Sources</CardTitle>
            <CardDescription>Connected knowledge bases and vector stores</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg border border-border">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                  <Database size={20} className="text-primary" />
                </div>
                <div>
                  <div className="font-medium">Primary Knowledge Base</div>
                  <div className="text-sm text-muted-foreground">Local Vector DB (Qdrant)</div>
                </div>
              </div>
              <Badge className="bg-green-100 text-green-700 hover:bg-green-100">Connected</Badge>
            </div>

            {/* Ingestion Control - Collapsible */}
            <Collapsible open={isLogsOpen} onOpenChange={setIsLogsOpen} className="space-y-2">
              <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg border border-border">
                <div className="flex items-center gap-3">
                  <CollapsibleTrigger asChild>
                    <Button variant="ghost" size="sm" className="p-0 h-auto hover:bg-transparent">
                      {isLogsOpen ? <ChevronUp size={20} className="text-muted-foreground" /> : <ChevronDown size={20} className="text-muted-foreground" />}
                    </Button>
                  </CollapsibleTrigger>
                  <div>
                    <div className="font-medium">Ingestion Control</div>
                    <div className="text-sm text-muted-foreground">Upload and process documents</div>
                  </div>
                </div>
                <Button
                  onClick={handleIngest}
                  disabled={isIngesting}
                  className="gap-2"
                >
                  <Play size={16} />
                  {isIngesting ? "Ingesting..." : "Trigger Upload & Ingest"}
                </Button>
              </div>

              <CollapsibleContent className="space-y-2">
                <Card className="bg-gray-900 border-gray-800">
                  <CardContent className="p-0">
                    <ScrollArea className="h-[400px] w-full">
                      <div className="p-4 font-mono text-xs text-green-400 space-y-1">
                        {ingestionLogs.length === 0 ? (
                          <span className="text-gray-500">// Logs will appear here...</span>
                        ) : (
                          ingestionLogs.map((log, i) => (
                            <div key={i}>{log}</div>
                          ))
                        )}
                      </div>
                    </ScrollArea>
                  </CardContent>
                </Card>
              </CollapsibleContent>
            </Collapsible>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdminPage;
