import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, ArrowRight } from 'lucide-react';
import { useAppStore } from '../lib/store';
import { Button } from '../components/ui/button';
import { formatDate } from '../lib/utils';
import { fetchProjectsForUser } from '../lib/queries';
import type { Project } from '../lib/store';

export function ProjectsPage() {
  // State for direct Supabase query approach
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Still use Zustand store for setting current project
  const { setCurrentProject } = useAppStore();
  const navigate = useNavigate();
  
  // Fetch projects directly from Supabase when component mounts
  useEffect(() => {
    async function loadUserProjects() {
      try {
        setIsLoading(true);
        setError(null);
        
        // Use direct Supabase query through our helper function
        const userProjects = await fetchProjectsForUser();
        setProjects(userProjects);
        
        console.log(`Loaded ${userProjects.length} projects for user`);
      } catch (err) {
        console.error('Error fetching projects:', err);
        setError(err instanceof Error ? err.message : 'Failed to load projects');
      } finally {
        setIsLoading(false);
      }
    }
    
    loadUserProjects();
  }, []); // Empty dependency array to run only on mount
  
  const handleCreateProject = () => {
    navigate('/setup-project');
  };
  
  const handleSelectProject = (projectId: string) => {
    // Still use the store to set current project for other components
    setCurrentProject(projectId);
    navigate(`/chat/${projectId}`);
  };
  
  // Function to retry loading if there was an error
  const handleRetryLoading = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const userProjects = await fetchProjectsForUser();
      setProjects(userProjects);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load projects');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-2xl font-bold text-black">Your Projects</h1>
          <Button onClick={handleCreateProject}>
            <Plus className="h-4 w-4 mr-2" />
            New Project
          </Button>
        </div>
        
        {/* Loading state */}
        {isLoading && (
          <div className="bg-white shadow-sm rounded-lg p-8 text-center border border-gray-200">
            <div className="flex justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black"></div>
            </div>
            <p className="text-gray-600 mt-4">Loading your projects...</p>
          </div>
        )}
        
        {/* Error state */}
        {error && !isLoading && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-6">
            <h3 className="text-red-800 font-medium mb-2">Error loading projects</h3>
            <p className="text-red-700">{error}</p>
            <Button 
              className="mt-4 bg-red-100 hover:bg-red-200 text-red-800 border-red-300"
              onClick={handleRetryLoading}
            >
              Try Again
            </Button>
          </div>
        )}
        
        {/* Empty state */}
        {!isLoading && !error && projects.length === 0 && (
          <div className="bg-white shadow-sm rounded-lg p-8 text-center border border-gray-200">
            <h2 className="text-xl font-semibold mb-2 text-black">No projects yet</h2>
            <p className="text-gray-600 mb-6">
              Create your first project to get started with Datajar
            </p>
            <Button onClick={handleCreateProject}>
              <Plus className="h-4 w-4 mr-2" />
              Create Project
            </Button>
          </div>
        )}
        
        {/* Projects list */}
        {!isLoading && !error && projects.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((project) => (
              <div 
                key={project.id} 
                className="bg-white shadow-sm rounded-lg p-6 hover:shadow-md transition-shadow cursor-pointer border border-gray-200"
                onClick={() => handleSelectProject(project.id)}
              >
                <h2 className="text-lg font-semibold mb-2 text-black">{project.name}</h2>
                <p className="text-sm text-gray-500 mb-3">
                  {formatDate(project.createdAt)}
                </p>
                <div className="flex flex-wrap gap-2 mb-4">
                  {project.industry && (
                    <span className="px-2 py-1 text-xs bg-gray-100 rounded">
                      {project.industry}
                    </span>
                  )}
                  {project.persona && (
                    <span className="px-2 py-1 text-xs bg-gray-100 rounded">
                      {project.persona}
                    </span>
                  )}
                </div>
                <div className="flex items-center justify-between mt-4">
                  <div className="text-xs text-gray-500">
                    {project.context ? 
                      project.context.substring(0, 60) + (project.context.length > 60 ? '...' : '')
                      : 'No context provided'
                    }
                  </div>
                  <ArrowRight className="h-4 w-4 text-black" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
