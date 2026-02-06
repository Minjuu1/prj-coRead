import axios from 'axios';
import type { Document, Thread, Message, Section } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// User API
export const userApi = {
  login: async (userId: string) => {
    const response = await api.post('/users/login', { userId });
    return response.data;
  },

  getUser: async (userId: string) => {
    const response = await api.get(`/users/${userId}`);
    return response.data;
  },
};

// Document API
export const documentApi = {
  upload: async (file: File, userId: string): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', userId);

    const response = await api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  get: async (documentId: string): Promise<Document> => {
    const response = await api.get(`/documents/${documentId}`);
    return response.data;
  },

  getSections: async (documentId: string): Promise<Section[]> => {
    const response = await api.get(`/documents/${documentId}/sections`);
    return response.data;
  },

  delete: async (documentId: string): Promise<void> => {
    await api.delete(`/documents/${documentId}`);
  },

  getUserDocuments: async (userId: string) => {
    const response = await api.get(`/documents/user/${userId}`);
    return response.data;
  },
};

// Thread API
export interface ThreadListItem {
  threadId: string;
  threadType: 'comment' | 'discussion';
  discussionType?: string;
  tensionPoint: string;
  participants: string[];
  messageCount: number;
  anchor: {
    sectionId: string;
    startOffset: number;
    endOffset: number;
    snippetText: string;
  };
}

export const threadApi = {
  getDocumentThreads: async (documentId: string): Promise<ThreadListItem[]> => {
    const response = await api.get(`/threads/document/${documentId}`);
    return response.data;
  },

  get: async (threadId: string): Promise<Thread> => {
    const response = await api.get(`/threads/${threadId}`);
    return response.data;
  },

  sendMessage: async (
    threadId: string,
    content: string,
    taggedAgent?: string
  ): Promise<Message> => {
    const response = await api.post(`/threads/${threadId}/messages`, {
      content,
      taggedAgent,
    });
    return response.data;
  },

  generateMore: async (threadId: string): Promise<Message[]> => {
    const response = await api.post(`/threads/${threadId}/generate-more`);
    return response.data;
  },
};

// Pipeline API
export interface PipelineResult {
  status: string;
  annotations: Record<string, unknown[]>;
  seeds: unknown[];
  threads: Thread[];  // Full thread data including anchor, messages
  timings: Record<string, number>;
}

export const pipelineApi = {
  generateDiscussions: async (
    documentId: string,
    options?: {
      maxAnnotationsPerAgent?: number;
      targetSeeds?: number;
      turnsPerDiscussion?: number;
    }
  ): Promise<PipelineResult> => {
    const response = await api.post(
      `/pipeline/documents/${documentId}/generate-with-logging`,
      {
        maxAnnotationsPerAgent: options?.maxAnnotationsPerAgent ?? 12,
        targetSeeds: options?.targetSeeds ?? 5,
        turnsPerDiscussion: options?.turnsPerDiscussion ?? 4,
      }
    );
    return response.data;
  },
};

// Health check
export const healthApi = {
  check: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;
