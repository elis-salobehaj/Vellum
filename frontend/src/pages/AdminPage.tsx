import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle, AlertCircle, ChevronDown, ChevronUp, Database, FileText, Upload, X, FileWarning } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { logger } from '@/lib/logger';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Skeleton } from '@/components/ui/skeleton';

import { useModels, type Model } from '@/hooks/useModels';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';

const AdminPage = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Data Fetching
  const { data: models = [], isLoading: loading } = useModels();

  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [ingestionLogs, setIngestionLogs] = useState<string[]>([]);
  const [isLogsOpen, setIsLogsOpen] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);

  // Phase 6.4: Form Validation
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);

  // Derive active model from fetched models
  const activeModelId = (models as Model[]).find(m => m.is_active)?.id || '';

  // Mutation for updating model
  const updateModelMutation = useMutation({
    mutationFn: async (modelId: string) => {
      const model = (models as Model[]).find(m => m.id === modelId);
      if (!model) throw new Error("Model not found");

      const updatedConfig = { ...model, is_active: true };
      return api.put(`/admin/models/${modelId}`, updatedConfig);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["models"] });
      setSuccessMsg("Model updated successfully");
      setTimeout(() => setSuccessMsg(null), 3000);
    },
    onError: (err: Error) => {
      setError(err.message || "Failed to update model");
    }
  });

  const handleModelChange = (modelId: string) => {
    updateModelMutation.mutate(modelId);
  };

  const validateFile = (file: File) => {
    if (file.type !== 'application/pdf') {
      return "Only PDF files are supported.";
    }
    if (file.size > 10 * 1024 * 1024) {
      return "File size must be less than 10MB.";
    }
    return null;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const error = validateFile(file);
      setFileError(error);
      if (!error) {
        setSelectedFile(file);
        logger.info("file_selected", { name: file.name, size: file.size });
      } else {
        setSelectedFile(null);
      }
    }
  };

  const handleIngest = async () => {
    setIsIngesting(true);
    setError(null);
    setSuccessMsg(null);
    setIngestionLogs(["Starting ingestion process..."]);
    setIsLogsOpen(true); // Auto-expand logs

    try {
      // Use api.stream for cleaner auth handling
      const response = await api.stream('/admin/upload-and-ingest');

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();

        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n').filter(Boolean);
          if (lines.length > 0) {
            setIngestionLogs(prev => [...prev, ...lines]);
          }
        }

        if (done) {
          setSuccessMsg("Ingestion completed successfully");
          break;
        }
      }
    } catch (err: unknown) {
      const error = err as Error;
      logger.error("ingestion_failed", error);
      setError(error.message || "Ingestion failed");
      setIngestionLogs(prev => [...prev, `Error: ${error.message}`]);
    } finally {
      setIsIngesting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-4xl mx-auto space-y-8">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Admin Dashboard</h1>
              <p className="text-muted-foreground mt-1">Manage system configuration and data ingestion</p>
            </div>
          </div>
        </div>

        {/* Notifications */}
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {successMsg && (
          <Alert className="border-green-500 text-green-600 bg-green-50 dark:bg-green-950/20">
            <CheckCircle className="h-4 w-4" />
            <AlertDescription>{successMsg}</AlertDescription>
          </Alert>
        )}

        {/* Model Configuration */}
        <Card>
          <CardHeader>
            <CardTitle className="text-xl flex items-center gap-2">
              <Database className="h-5 w-5 text-primary" />
              Model Configuration
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-2">
                <Skeleton className="h-10 w-full rounded-xl" />
                <Skeleton className="h-4 w-2/3" />
              </div>
            ) : (
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <Select
                    value={activeModelId}
                    onValueChange={handleModelChange}
                    disabled={updateModelMutation.isPending}
                  >
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <SelectTrigger>
                            <SelectValue placeholder="Select a model" />
                          </SelectTrigger>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Select the active LLM for chat generation</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                    <SelectContent className="bg-background!">
                      {(models as Model[]).map((m: Model) => (
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
                </div>
                {updateModelMutation.isPending && (
                  <span className="text-xs text-muted-foreground animate-pulse">Updating...</span>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Ingestion Control */}
        <Card>
          <CardHeader>
            <CardTitle className="text-xl flex items-center gap-2">
              Knowledge Base Ingestion
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-4">
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-foreground">Upload Knowledge Base (PDF)</label>
                <div className={cn(
                  "border-2 border-dashed rounded-2xl p-8 transition-all flex flex-col items-center justify-center gap-3 cursor-pointer hover:border-primary/50 hover:bg-primary/5",
                  fileError ? "border-destructive/50 bg-destructive/5" : "border-border",
                  selectedFile ? "border-primary/50 bg-primary/5" : ""
                )} onClick={() => document.getElementById('file-upload')?.click()}>
                  <input
                    id="file-upload"
                    type="file"
                    className="hidden"
                    accept=".pdf"
                    onChange={handleFileChange}
                  />
                  {selectedFile ? (
                    <>
                      <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                        <FileText size={24} />
                      </div>
                      <div className="text-center">
                        <p className="text-sm font-semibold">{selectedFile.name}</p>
                        <p className="text-xs text-muted-foreground">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 px-2 text-muted-foreground hover:text-destructive"
                        onClick={(e: React.MouseEvent) => {
                          e.stopPropagation();
                          setSelectedFile(null);
                        }}
                      >
                        <X size={14} className="mr-1" /> Remove
                      </Button>
                    </>
                  ) : (
                    <>
                      <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center text-muted-foreground">
                        <Upload size={24} />
                      </div>
                      <div className="text-center">
                        <p className="text-sm font-medium">Click to upload or drag and drop</p>
                        <p className="text-xs text-muted-foreground">PDF only (max 10MB)</p>
                      </div>
                    </>
                  )}
                </div>
                {fileError && (
                  <div className="flex items-center gap-2 text-xs text-destructive animate-in fade-in slide-in-from-top-1">
                    <FileWarning size={14} />
                    <span>{fileError}</span>
                  </div>
                )}
              </div>

              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      onClick={() => handleIngest()}
                      disabled={isIngesting}
                      className="w-full sm:w-auto min-w-50 rounded-xl h-11"
                    >
                      {isIngesting ? (
                        <>
                          <div className="h-4 w-4 mr-2 animate-spin rounded-full border-2 border-white border-t-transparent" />
                          Processing...
                        </>
                      ) : (
                        "Start Ingestion"
                      )}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Trigger document processing pipeline</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>

            {/* Logs Area */}
            <Collapsible
              open={isLogsOpen}
              onOpenChange={setIsLogsOpen}
              className="w-full space-y-2"
            >
              <div className="flex items-center justify-between space-x-4 px-4 py-2 bg-muted/50 rounded-lg">
                <h4 className="text-sm font-semibold">Ingestion Logs ({ingestionLogs.length})</h4>
                <CollapsibleTrigger asChild>
                  <Button variant="ghost" size="sm" className="w-9 p-0">
                    {isLogsOpen ? (
                      <ChevronUp className="h-4 w-4" />
                    ) : (
                      <ChevronDown className="h-4 w-4" />
                    )}
                    <span className="sr-only">Toggle</span>
                  </Button>
                </CollapsibleTrigger>
              </div>
              <CollapsibleContent>
                <ScrollArea className="h-75 w-full rounded-md border p-4 bg-muted/20 font-mono text-xs">
                  {ingestionLogs.length === 0 ? (
                    <div className="text-muted-foreground italic">No logs available. Start ingestion to see progress.</div>
                  ) : (
                    ingestionLogs.map((log, index) => (
                      <div key={index} className="mb-1 border-b border-border/10 pb-1 last:border-0">
                        <span className="text-muted-foreground">[{new Date().toLocaleTimeString()}]</span> {log}
                      </div>
                    ))
                  )}
                </ScrollArea>
              </CollapsibleContent>
            </Collapsible>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdminPage;
