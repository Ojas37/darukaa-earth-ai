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
