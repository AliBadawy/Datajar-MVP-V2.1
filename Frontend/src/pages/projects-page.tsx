import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, ArrowRight } from 'lucide-react';
import { useAppStore } from '../lib/store';
import { Button } from '../components/ui/button';
import { formatDate } from '../lib/utils';

export function ProjectsPage() {
  const { projects, setCurrentProject, fetchProjects } = useAppStore();
  const navigate = useNavigate();
  
  // Fetch projects when component mounts
  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);
  
  const handleCreateProject = () => {
    navigate('/setup-project');
  };
  
  const handleSelectProject = (projectId: string) => {
    setCurrentProject(projectId);
    navigate('/chat');
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
        
        {projects.length === 0 ? (
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
        ) : (
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
                <div className="flex items-center justify-between mt-4">
                  <div className="flex items-center">
                    <span className="px-2 py-1 text-xs bg-gray-100 rounded">
                      {project.industry}
                    </span>
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
