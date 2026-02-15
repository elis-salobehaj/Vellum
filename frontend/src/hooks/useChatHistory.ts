import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuth } from "./useAuth";

export interface ChatSession {
  id: string;
  title?: string;
  timestamp?: string;
  created_at?: string;
  model_id?: string;
}

export const useChatHistory = () => {
  const { user, getToken } = useAuth();
  api.setTokenGetter(getToken);

  return useQuery({
    queryKey: ["history"],
    queryFn: () => api.get<ChatSession[]>("/history"),
    enabled: !!user,
  });
};
