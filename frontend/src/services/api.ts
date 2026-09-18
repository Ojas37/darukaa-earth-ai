import type { ChatResponse, StructuredReportResponse } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export class ApiError extends Error {
  status?: number;
  data?: any;

  constructor(message: string, status?: number, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export interface StreamCallbacks {
  onStatus?: (stage: string, message: string) => void;
  onProfile?: (profile: Record<string, any>) => void;
  onPathways?: (pathways: any[]) => void;
  onDelta?: (deltaText: string) => void;
  onDone?: (response: ChatResponse) => void;
  onError?: (error: Error) => void;
}

/**
 * Sends a chat query using Server-Sent Events (SSE) streaming.
 * Emits progressive reasoning stages and real-time token deltas before completing.
 */
export async function streamChatMessage(
  message: string,
  conversationId: string | null,
  callbacks: StreamCallbacks
): Promise<ChatResponse> {
  const payload = {
    message,
    conversation_id: conversationId || null,
  };

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      let errorDetail = 'Failed to start streaming analysis';
      try {
        const errorJson = await response.json();
        if (errorJson?.detail) {
          errorDetail = typeof errorJson.detail === 'string'
            ? errorJson.detail
            : JSON.stringify(errorJson.detail);
        }
      } catch {
        errorDetail = response.statusText || errorDetail;
      }
      throw new ApiError(errorDetail, response.status);
    }

    if (!response.body) {
      throw new ApiError('ReadableStream not supported by response body');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';
    let finalResponse: ChatResponse | null = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop() || '';

      for (const part of parts) {
        if (!part.trim()) continue;

        let eventType = 'message';
        let dataStr = '';

        const lines = part.split('\n');
        for (const line of lines) {
          if (line.startsWith('event:')) {
            eventType = line.replace('event:', '').trim();
          } else if (line.startsWith('data:')) {
            dataStr = line.replace('data:', '').trim();
          }
        }

        if (!dataStr) continue;

        try {
          const parsed = JSON.parse(dataStr);

          if (eventType === 'status') {
            callbacks.onStatus?.(parsed.stage, parsed.message);
          } else if (eventType === 'profile') {
            callbacks.onProfile?.(parsed);
          } else if (eventType === 'pathways') {
            callbacks.onPathways?.(parsed);
          } else if (eventType === 'delta') {
            callbacks.onDelta?.(parsed.text);
          } else if (eventType === 'done') {
            finalResponse = parsed as ChatResponse;
            callbacks.onDone?.(finalResponse);
          } else if (eventType === 'error') {
            throw new Error(parsed.error || 'Streaming error encountered');
          }
        } catch (e: any) {
          if (e.message?.includes('Streaming error')) throw e;
          console.warn('Error parsing SSE event:', e, dataStr);
        }
      }
    }

    if (!finalResponse) {
      throw new ApiError('Stream closed before full synthesis completed');
    }

    return finalResponse;
  } catch (err: any) {
    const errorObj = err instanceof ApiError ? err : new ApiError(err.message || 'Stream connection failed');
    callbacks.onError?.(errorObj);
    throw errorObj;
  }
}

export async function sendChatMessage(
  message: string,
  conversationId?: string | null
): Promise<ChatResponse> {
  const payload = {
    message,
    conversation_id: conversationId || null,
  };

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      let errorDetail = 'Failed to analyze environmental query';
      try {
        const errorJson = await response.json();
        if (errorJson?.detail) {
          errorDetail = typeof errorJson.detail === 'string' 
            ? errorJson.detail 
            : JSON.stringify(errorJson.detail);
        }
      } catch {
        errorDetail = response.statusText || errorDetail;
      }
      throw new ApiError(errorDetail, response.status);
    }

    const data: ChatResponse = await response.json();
    return data;
  } catch (err: any) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(
      err.message || 'Unable to reach the Darukaa backend service. Please ensure the backend is running.',
      undefined,
      err
    );
  }
}

export async function fetchReport(conversationId: string): Promise<StructuredReportResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/report/${encodeURIComponent(conversationId)}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new ApiError(`Failed to fetch report (${response.status})`, response.status);
    }

    return await response.json();
  } catch (err: any) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(err.message || 'Failed to fetch structured report');
  }
}
