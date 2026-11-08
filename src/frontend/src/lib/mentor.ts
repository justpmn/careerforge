
import { csrfHeader } from './auth';

export type MentorMessage = {
  id?: number;
  role: 'user' | 'assistant';
  content: string;
  created_at?: string;
};

export type MentorConversation = {
  id: number;
  title: string | null;
  career_id: number | null;
  created_at: string;
  updated_at: string;
};

export type MentorChatResponse = {
  conversation_id: number;
  response: string;
  career_key: string;
  target_updated: boolean;
};

export type MentorJobAccepted = {
  job_id: number;
  conversation_id: number;
  career_key: string;
  target_updated: boolean;
};

export type MentorJob = {
  id: number;
  conversation_id: number;
  status: 'queued' | 'running' | 'completed' | 'failed';
  response_seconds: number | null;
  error: string | null;
  created_at?: string;
  updated_at?: string;
};

const API = '/api/ai-mentor';

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API}${path}`, {
      ...options,
      credentials: 'include',
      headers: {
        ...(options.body
          ? { 'Content-Type': 'application/json' }
          : {}),
        ...(
          ['POST', 'PATCH', 'PUT', 'DELETE'].includes(
            (options.method ?? 'GET').toUpperCase()
          )
            ? csrfHeader()
            : {}
        ),
        ...options.headers,
      },
    });
  } catch {
    throw new Error(
      'Cannot connect to CareerForge. Check that the backend is running.'
    );
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null);

    throw new Error(
      typeof body?.detail === 'string'
        ? body.detail
        : `Request failed (HTTP ${response.status}).`
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export const mentorApi = {
  conversations() {
    return request<MentorConversation[]>('/conversations');
  },

  messages(conversationId: number) {
    return request<MentorMessage[]>(
      `/conversations/${conversationId}/messages`
    );
  },

    send(
    message: string,
    careerKey: string | null,
    conversationId: number | null
    ) {
    return request<MentorChatResponse>(
        '/chat/assessment/persistent',
        {
        method: 'POST',
        body: JSON.stringify({
            message,
            career_key: careerKey,
            conversation_id: conversationId,
        }),
        }
    );
    },
    queue(
    message: string,
    careerKey: string | null,
    conversationId: number | null
  ) {
    return request<MentorJobAccepted>('/jobs', {
      method: 'POST',
      body: JSON.stringify({
        message,
        career_key: careerKey,
        conversation_id: conversationId,
      }),
    });
  },

  jobs() {
    return request<MentorJob[]>('/jobs');
  },
  renameConversation(conversationId: number, title: string) {
  return request<MentorConversation>(
    `/conversations/${conversationId}`,
    {
      method: 'PATCH',
      body: JSON.stringify({ title }),
    }
  );
},

deleteConversation(conversationId: number) {
  return request<void>(
    `/conversations/${conversationId}`,
    {
      method: 'DELETE',
    }
  );
},

  job(jobId: number) {
    return request<MentorJob>(`/jobs/${jobId}`);
  },
};
