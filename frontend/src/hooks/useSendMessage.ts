import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import { useAuth } from "./useAuth";
import type { Citation } from "../types";

interface SendMessageVariables {
  sessionId?: string;
  message: string;
  modelId?: string;
}

interface SendMessageResponse {
  response: string;
  citations?: Citation[];
  session_id?: string;
}

export const useSendMessage = () => {
  const { getToken } = useAuth();
  api.setTokenGetter(getToken);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (variables: SendMessageVariables) => {
      const { sessionId, message, modelId } = variables;
      return api.post<SendMessageResponse>("/chat", {
        message,
        session_id: sessionId,
        model_id: modelId
      });
    },
    onSuccess: (data, variables) => {
      // Invalidate history to show new session in sidebar if applicable
      if (!variables.sessionId && data.session_id) {
        queryClient.invalidateQueries({ queryKey: ["history"] });
      }

      // We could also invalidate specific session messages if we were relying solely on cache
      // queryClient.invalidateQueries({ queryKey: ["session", variables.sessionId || data.session_id] });
    }
  });
};
