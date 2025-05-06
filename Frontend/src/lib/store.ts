import { create } from 'zustand';

// Define the Project interface
export interface Project {
  id: string;
  name: string;
  industry: string;
  createdAt: string;
}

// Define the AppStore interface
interface AppStore {
  // State
  projects: Project[];
  currentProjectId: string | null;
  
  // Actions
  setCurrentProject: (projectId: string) => void;
  addProject: (project: Project) => void;
  fetchProjects: () => void;
}

// Create the store
export const useAppStore = create<AppStore>((set) => ({
  // Initial state
  projects: [],
  currentProjectId: null,
  
  // Actions
  setCurrentProject: (projectId) => set(() => ({ currentProjectId: projectId })),
  
  addProject: (project) => set((state) => ({ 
    projects: [...state.projects, project] 
  })),
  
  // In a real app, this would fetch from an API
  fetchProjects: () => {
    // Mock data - would be replaced with an actual API call
    const mockProjects: Project[] = [
      {
        id: '1',
        name: 'E-Commerce Sales Analysis',
        industry: 'Retail',
        createdAt: '2025-04-15T12:00:00Z'
      },
      {
        id: '2',
        name: 'Marketing Campaign Performance',
        industry: 'Marketing',
        createdAt: '2025-05-01T09:30:00Z'
      },
      {
        id: '3',
        name: 'Customer Segmentation Study',
        industry: 'Analytics',
        createdAt: '2025-05-04T14:45:00Z'
      }
    ];
    
    set({ projects: mockProjects });
  }
}));
