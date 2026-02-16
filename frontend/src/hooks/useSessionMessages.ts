import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import type { Message } from "@/types";

interface BackendCitation {
  source: string;
  page?: number;
  text: string;
}

interface BackendMessage {
  role: 'user' | 'assistant';
  content: string;
  citations: BackendCitation[];
}

export const useSessionMessages = (sessionId: string | undefined) => {
  const { user, getToken } = useAuth();
  api.setTokenGetter(getToken);

  return useQuery({
    queryKey: ["session", sessionId],
    queryFn: async () => {
      if (!sessionId) return [];
      const data = await api.get<BackendMessage[]>(`/history/${sessionId}`);

      // Transform to frontend Message format
      return data.map((msg, idx) => ({
        id: `hist-${idx}`,
        role: msg.role,
        content: msg.content,
        citations: msg.citations?.map((c, i) => ({
          id: `hist-${idx}-${i}`,
          source: c.source,
          page: c.page,
          text: c.text
        })) || []
      })) as Message[];
    },
    enabled: !!user && !!sessionId,
    refetchOnWindowFocus: false,
  });
};
