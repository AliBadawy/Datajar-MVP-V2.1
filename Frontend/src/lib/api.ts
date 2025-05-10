import axios from "axios";
import { supabase } from "./supabase";

export interface ProjectCreateRequest {
  name: string;
  persona: string;
  context: string;
  industry: string;
  user_id?: string; // Add user_id field to associate with Supabase user
}

export interface ProjectResponse extends ProjectCreateRequest {
  id: number;
  created_at: string;
  user_id?: string; // Ensure user_id is also in the response
}

export interface MessageResponse {
  id: string;
  project_id: number;
  role: "user" | "assistant";
  content: string;
  intent: string;
  created_at: string;
}

export interface ProjectContextResponse {
  project: ProjectResponse;
  messages: MessageResponse[];
  has_data: boolean;
  data_preview?: any[];
  columns?: string[];
  data_summary?: {
    total_rows: number;
    total_columns: number;
    memory_usage: string;
  };
}

// Base API URL
const API_URL = "http://localhost:8000";

// Create authenticated axios instance
const createAuthenticatedRequest = async () => {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  
  return axios.create({
    baseURL: API_URL,
    headers: token ? {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    } : {
      'Content-Type': 'application/json'
    }
  });
};

export async function createProject(projectData: ProjectCreateRequest): Promise<ProjectResponse> {
  const api = await createAuthenticatedRequest();
  const response = await api.post(`/api/projects`, projectData);
  return response.data;
}

export async function getProjects(): Promise<ProjectResponse[]> {
  const api = await createAuthenticatedRequest();
  const response = await api.get(`/api/projects`);
  return response.data;
}

export async function getProject(id: number): Promise<ProjectResponse> {
  const api = await createAuthenticatedRequest();
  const response = await api.get(`/api/projects/${id}`);
  return response.data;
}

export async function fetchMessages(projectId: number | string, page: number = 1, limit: number = 100): Promise<MessageResponse[]> {
  const api = await createAuthenticatedRequest();
  const response = await api.get(`/api/messages/${projectId}?page=${page}&limit=${limit}`);
  return response.data.messages;
}

export async function getProjectContext(projectId: number | string): Promise<ProjectContextResponse> {
  const api = await createAuthenticatedRequest();
  const response = await api.get(`/api/project/${projectId}/context`);
  return response.data;
}
