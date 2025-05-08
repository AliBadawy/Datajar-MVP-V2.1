import axios from "axios";

export interface ProjectCreateRequest {
  name: string;
  persona: string;
  context: string;
  industry: string;
}

export interface ProjectResponse extends ProjectCreateRequest {
  id: number;
  created_at: string;
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

export async function createProject(projectData: ProjectCreateRequest): Promise<ProjectResponse> {
  const response = await axios.post(`${API_URL}/api/projects`, projectData);
  return response.data;
}

export async function getProjects(): Promise<ProjectResponse[]> {
  const response = await axios.get(`${API_URL}/api/projects`);
  return response.data;
}

export async function getProject(id: number): Promise<ProjectResponse> {
  const response = await axios.get(`${API_URL}/api/projects/${id}`);
  return response.data;
}

export async function fetchMessages(projectId: number | string, page: number = 1, limit: number = 100): Promise<MessageResponse[]> {
  const response = await axios.get(`${API_URL}/api/messages/${projectId}?page=${page}&limit=${limit}`);
  return response.data.messages;
}

export async function getProjectContext(projectId: number | string): Promise<ProjectContextResponse> {
  const response = await axios.get(`${API_URL}/api/project/${projectId}/context`);
  return response.data;
}
