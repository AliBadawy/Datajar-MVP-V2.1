import { create } from 'zustand';
import { createProject as apiCreateProject, getProjects, fetchMessages, getProjectContext } from './api';

// Define the Project interface
export interface Project {
  id: string;
  name: string;
  industry: string;
  createdAt: string;
  context?: string;
  persona?: string;
}

// Define Message interface
export interface ChatMessage {
  content: string;
  isUser: boolean;
  isTyping?: boolean;
  intent?: string;
  type?: string;
  pandas_result?: any;
  narrative?: string;
  timestamp?: string;
}

// Define dataframe interface for project context
interface DataFrame {
  rows: any[];
  columns: string[];
  summary?: {
    total_rows: number;
    total_columns: number;
    memory_usage: string;
  };
}

// Define the AppStore interface
interface AppStore {
  // State
  projects: Project[];
  currentProjectId: string | null;
  isLoading: boolean;
  error: string | null;
  messages: ChatMessage[];
  messagesLoading: boolean;
  messagesError: string | null;
  dataframe: DataFrame | null;
  projectMetadata: {
    persona: string;
    industry: string;
    context: string;
  } | null;
  contextLoading: boolean;
  contextError: string | null;
  
  // Actions
  setCurrentProject: (projectId: string) => void;
  addProject: (project: Project) => void;
  createProject: (projectData: {
    name: string;
    persona: string;
    context: string;
    industry: string;
  }) => Promise<string>;
  fetchProjects: () => void;
  loadProjects: () => Promise<void>;
  fetchMessageHistory: (projectId: string | number) => Promise<void>;
  addMessage: (message: ChatMessage) => void;
  clearMessages: () => void;
  clearError: () => void;
  setDataFrame: (dataframe: DataFrame | null) => void;
  setProjectMetadata: (metadata: { persona: string; industry: string; context: string } | null) => void;
  loadProjectContext: (projectId: string | number) => Promise<void>;
}

// Create the store
export const useAppStore = create<AppStore>((set, get) => ({
  // Initial state
  projects: [],
  currentProjectId: null,
  isLoading: false,
  error: null,
  messages: [],
  messagesLoading: false,
  messagesError: null,
  dataframe: null,
  projectMetadata: null,
  contextLoading: false,
  contextError: null,
  
  // Actions
  setCurrentProject: (projectId) => set(() => ({ currentProjectId: projectId })),
  
  addProject: (project) => set((state) => ({ 
    projects: [...state.projects, project] 
  })),
  
  createProject: async (projectData) => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await apiCreateProject(projectData);
      
      // Convert backend response to our Project format
      const newProject: Project = {
        id: response.id.toString(),
        name: response.name,
        persona: response.persona,
        context: response.context,
        industry: response.industry,
        createdAt: response.created_at
      };
      
      // Add the project to our store
      get().addProject(newProject);
      
      // Set as current project
      set({ currentProjectId: newProject.id, isLoading: false });
      
      return newProject.id;
    } catch (error) {
      console.error('Failed to create project:', error);
      set({ 
        error: error instanceof Error ? error.message : 'Failed to create project', 
        isLoading: false 
      });
      throw error;
    }
  },
  
  // Load projects from API
  loadProjects: async () => {
    set({ isLoading: true, error: null });
    
    try {
      // Fetch projects from the backend API
      const projectsData = await getProjects();
      
      // Convert backend response format to our Project format
      const projects: Project[] = projectsData.map(project => ({
        id: project.id.toString(),
        name: project.name,
        persona: project.persona,
        context: project.context,
        industry: project.industry,
        createdAt: project.created_at
      }));
      
      // Update state with fetched projects
      set({ projects, isLoading: false });
    } catch (error) {
      console.error('Failed to load projects:', error);
      set({ 
        error: error instanceof Error ? error.message : 'Failed to load projects', 
        isLoading: false 
      });
    }
  },
  
  // This is now used as a fallback for mock data when loadProjects fails
  fetchProjects: () => {
    // Mock data - would be replaced with an actual API call
    const mockProjects: Project[] = [
      {
        id: '1',
        name: 'E-Commerce Sales Analysis',
        industry: 'Retail',
        context: 'Analyzing quarterly sales data for online store',
        persona: 'Data Analyst',
        createdAt: '2025-04-15T12:00:00Z'
      },
      {
        id: '2',
        name: 'Marketing Campaign Performance',
        industry: 'Marketing',
        context: 'Evaluating ROI of digital marketing channels',
        persona: 'Marketer',
        createdAt: '2025-05-01T09:30:00Z'
      },
      {
        id: '3',
        name: 'Customer Segmentation Study',
        industry: 'Analytics',
        context: 'Identifying high-value customer segments',
        persona: 'Business Owner',
        createdAt: '2025-05-04T14:45:00Z'
      }
    ];
    
    set({ projects: mockProjects });
  },
  
  // Fetch message history for a project
  fetchMessageHistory: async (projectId) => {
    set({ messagesLoading: true, messagesError: null });
    
    try {
      // Fetch messages from the API
      const messagesData = await fetchMessages(projectId);
      
      // Convert to our ChatMessage format
      const chatMessages: ChatMessage[] = messagesData.map(msg => ({
        content: msg.content,
        isUser: msg.role === 'user',
        intent: msg.intent,
        type: msg.intent,  // Map intent to type for rendering
        timestamp: msg.created_at
      }));
      
      // Update state with messages
      set({ messages: chatMessages, messagesLoading: false });
    } catch (error) {
      console.error('Failed to load message history:', error);
      set({ 
        messagesError: error instanceof Error ? error.message : 'Failed to load messages', 
        messagesLoading: false 
      });
    }
  },
  
  // Add a single message to the messages array
  addMessage: (message) => set(state => ({
    messages: [...state.messages, message]
  })),
  
  // Clear all messages
  clearMessages: () => set({ messages: [] }),
  
  clearError: () => set({ error: null }),
  
  // Set dataframe for analysis
  setDataFrame: (dataframe) => set({ dataframe }),
  
  // Set project metadata
  setProjectMetadata: (metadata) => set({ projectMetadata: metadata }),
  
  // Load full project context - includes project data, messages, and dataframe
  loadProjectContext: async (projectId) => {
    set({ contextLoading: true, contextError: null });
    
    try {
      // Fetch the full context from the backend
      const contextData = await getProjectContext(projectId);
      
      // Update state with all the context data
      set({ 
        projectMetadata: {
          persona: contextData.project.persona || 'Data Analyst',
          industry: contextData.project.industry || 'E-Commerce',
          context: contextData.project.context || ''
        },
        messages: contextData.messages.map(msg => ({
          content: msg.content,
          isUser: msg.role === 'user',
          intent: msg.intent,
          type: msg.intent,
          timestamp: msg.created_at
        })),
        dataframe: contextData.has_data ? {
          rows: contextData.data_preview || [],
          columns: contextData.columns || [],
          summary: contextData.data_summary
        } : null,
        contextLoading: false
      });
      
      console.log('Loaded project context:', { 
        project: contextData.project,
        messagesCount: contextData.messages.length,
        hasData: contextData.has_data
      });
      
    } catch (error) {
      console.error('Failed to load project context:', error);
      set({
        contextError: error instanceof Error ? error.message : 'Failed to load project context',
        contextLoading: false
      });
    }
  }
}));
