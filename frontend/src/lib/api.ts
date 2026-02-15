import { config } from "@/config";
import { logger } from "@/lib/logger";

/**
 * API Error class for better error handling
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Centralized API client with automatic token injection and error handling.
 * All API calls should go through this client for consistency.
 */
class ApiClient {
  private baseUrl: string;
  private getToken: (() => Promise<string>) | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  /**
   * Set the token getter function (called from useAuth hook)
   */
  setTokenGetter(getter: () => Promise<string>) {
    this.getToken = getter;
  }

  /**
   * Get headers with authorization token
   */
  private async getHeaders(customHeaders: HeadersInit = {}): Promise<HeadersInit> {
    const token = this.getToken ? await this.getToken() : "mock-token";

    return {
      "Authorization": `Bearer ${token}`,
      ...customHeaders
    };
  }

  /**
   * Handle response and errors
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorText = await response.text().catch(() => "Unknown error");
      logger.error("api_request_failed", {
        status: response.status,
        statusText: response.statusText,
        error: errorText
      });
      throw new ApiError(response.status, response.statusText, errorText);
    }

    // Handle empty responses
    const contentType = response.headers.get("content-type");
    if (!contentType || !contentType.includes("application/json")) {
      return {} as T;
    }

    return response.json();
  }

  /**
   * GET request
   */
  async get<T>(path: string, customHeaders?: HeadersInit): Promise<T> {
    logger.debug("api_get", { path });

    const headers = await this.getHeaders(customHeaders);
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: "GET",
      headers
    });

    return this.handleResponse<T>(response);
  }

  /**
   * POST request
   */
  async post<T>(path: string, body?: any, customHeaders?: HeadersInit): Promise<T> {
    logger.debug("api_post", { path, hasBody: !!body });

    const headers = await this.getHeaders(customHeaders);
    if (body) { (headers as any)["Content-Type"] = "application/json"; }

    const response = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers,
      body: body ? JSON.stringify(body) : undefined
    });

    return this.handleResponse<T>(response);
  }

  /**
   * PUT request
   */
  async put<T>(path: string, body?: any, customHeaders?: HeadersInit): Promise<T> {
    logger.debug("api_put", { path, hasBody: !!body });

    const headers = await this.getHeaders(customHeaders);
    if (body) { (headers as any)["Content-Type"] = "application/json"; }

    const response = await fetch(`${this.baseUrl}${path}`, {
      method: "PUT",
      headers,
      body: body ? JSON.stringify(body) : undefined
    });

    return this.handleResponse<T>(response);
  }

  /**
   * DELETE request
   */
  async delete<T>(path: string, customHeaders?: HeadersInit): Promise<T> {
    logger.debug("api_delete", { path });

    const headers = await this.getHeaders(customHeaders);
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: "DELETE",
      headers
    });

    return this.handleResponse<T>(response);
  }

  /**
   * Stream request for SSE/streaming responses
   * Returns the raw Response object for streaming consumption
   */
  async stream(path: string, body?: any, customHeaders?: HeadersInit): Promise<Response> {
    logger.debug("api_stream", { path, hasBody: !!body });

    const headers = await this.getHeaders(customHeaders);
    if (body) { (headers as any)["Content-Type"] = "application/json"; }

    const response = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers,
      body: body ? JSON.stringify(body) : undefined
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => "Unknown error");
      logger.error("api_stream_failed", {
        status: response.status,
        statusText: response.statusText,
        error: errorText
      });
      throw new ApiError(response.status, response.statusText, errorText);
    }

    return response;
  }
}

// Export singleton instance
export const api = new ApiClient(config.apiUrl);
