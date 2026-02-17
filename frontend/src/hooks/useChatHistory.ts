import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import type { ChatSession } from "@/types/index";

export const useChatHistory = () => {
  const { user, getToken } = useAuth();
  api.setTokenGetter(getToken);

  return useQuery({
    queryKey: ["history"],
    queryFn: () => api.get<ChatSession[]>("/history"),
    enabled: !!user,
  });
};
