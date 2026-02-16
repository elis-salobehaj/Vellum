import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { useAuth } from "./useAuth";

export interface Model {
  id: string;
  is_active: boolean;
  name?: string;
  provider?: string;
}

export const useModels = () => {
  const { user, getToken } = useAuth();

  // Set the token getter for the API client
  // detailed Note: This is a side effect in render, but since api singleton is stable
  // and setTokenGetter is cheap, it's generally acceptable.
  // Ideally, this should be done in a Provider, effectively creating an API context.
  // For now, this ensures the API always has the latest mechanism to get tokens.
  api.setTokenGetter(getToken);

  return useQuery({
    queryKey: ["models"],
    queryFn: () => api.get<Model[]>("/admin/models"),
    enabled: !!user, // Only fetch if user is logged in
    staleTime: 5 * 60 * 1000, // consider models fresh for 5 minutes
  });
};
