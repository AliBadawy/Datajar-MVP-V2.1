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

// Base API URL - Using environment variable for deployment flexibility
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

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
  const response = await api.get(`/api/projects/${projectId}/context`);
  return response.data;
}

// Generate static analysis metadata for a project
function getStaticAnalysisResult(projectId: string | number) {
  return {
    status: 'success',
    project_id: projectId,
    summary: {
      sources: ['Salla'],
      total_rows: 120,
    },
    metadata: {
      analyzed_at: new Date().toISOString(),
      data_sources: ['Salla'],
      basic_stats: {
        total_records: 120,
        columns_analyzed: 15,
        missing_data_percentage: 2.5,
      },
      column_details: {
        order_id: { type: 'string', missing: 0 },
        customer_name: { type: 'string', missing: 3 },
        amount: { type: 'numeric', missing: 0 },
        date: { type: 'datetime', missing: 0 },
        status: { type: 'string', missing: 0 },
      },
    }
  };
}

export async function analyzeProject(projectId: string | number): Promise<any> {
  // Option 1: Use static data only (completely client-side)
  console.log('Using static analysis data for project', projectId);
  return getStaticAnalysisResult(projectId);
  
  // Option 2: Try the API call, but fallback to static data if it fails
  // try {
  //   const api = await createAuthenticatedRequest();
  //   const res = await api.post(`/api/projects/${projectId}/analyze`);
  //   return res.data;
  // } catch (error) {
  //   console.log('Analysis API failed, using static data instead', error);
  //   return getStaticAnalysisResult(projectId);
  // }
}
