import { create } from 'zustand';
import { createProject as apiCreateProject, getProjects } from './api';

// Define the Project interface
export interface Project {
  id: string;
  name: string;
  industry: string;
  createdAt: string;
  context?: string;
  persona?: string;
}

// Define the AppStore interface
interface AppStore {
  // State
  projects: Project[];
  currentProjectId: string | null;
  isLoading: boolean;
  error: string | null;
  
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
  clearError: () => void;
}

// Create the store
export const useAppStore = create<AppStore>((set, get) => ({
  // Initial state
  projects: [],
  currentProjectId: null,
  isLoading: false,
  error: null,
  
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
  
  clearError: () => set({ error: null })
}));
