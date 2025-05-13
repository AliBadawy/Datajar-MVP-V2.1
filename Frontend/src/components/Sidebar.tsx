import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Menu, X, Plus } from "lucide-react";

import { useAppStore } from '../lib/store';

export default function Sidebar() {
  const [projects, setProjects] = useState<any[]>([]);
  const [open, setOpen] = useState(true); // for mobile (slide in/out)
  const [collapsed, setCollapsed] = useState(false); // for desktop (collapse/expand)
  const [projectsOpen, setProjectsOpen] = useState(true); // controls expansion of projects sub-list
  const location = useLocation();
  const navigate = useNavigate();
  const setCurrentProject = useAppStore(state => state.setCurrentProject);

  const toggleSidebar = () => setOpen(!open);
  const toggleCollapse = () => setCollapsed((prev) => {
    const newCollapsed = !prev;
    if (newCollapsed) setProjectsOpen(false);
    return newCollapsed;
  });

  useEffect(() => {
    const fetchUserProjects = async () => {
      try {
        // Use the same helper as the Projects page
        const userProjects = await import('../lib/queries').then(mod => mod.fetchProjectsForUser());
        setProjects(userProjects);
      } catch (error) {
        setProjects([]);
      }
    };
    fetchUserProjects();
  }, []);

  return (
    <>
      {/* Toggle Button (Mobile) */}
      <div className="md:hidden p-4 flex justify-between items-center bg-white shadow z-50">
        <h1 className="text-lg font-bold text-indigo-600">DataJar</h1>
        <button onClick={toggleSidebar}>
          {open ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Sidebar */}
      <div
        className={`fixed top-0 left-0 h-screen bg-white border-r border-gray-200 shadow-md z-40 transition-all duration-300 flex flex-col ${
          collapsed ? 'w-16' : 'w-64'
        } ${open ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}`}
      >
        <div className="flex items-center h-16 border-b border-gray-200 px-2 gap-2">
          {!collapsed && (
            <h1 className="text-xl font-bold text-indigo-600 text-left w-full px-2">DataJar</h1>
          )}
        </div>

        <nav className="flex flex-col mt-4 space-y-2 px-2 text-left">
          <div className="relative">
            <button
              type="button"
              onClick={() => setProjectsOpen((open) => !open)}
              className={`flex items-center gap-2 px-4 py-2 rounded text-left transition-all cursor-pointer select-none w-full ${
                location.pathname === "/projects"
                  ? "bg-gray-100 text-black"
                  : "text-gray-700 hover:bg-gray-100"
              }`}
              aria-label={projectsOpen ? 'Collapse projects list' : 'Expand projects list'}
            >
              <span role="img" aria-label="Projects">📁</span>
              {!collapsed && (
                <>
                  <span
                    className="flex-1 cursor-pointer"
                    style={{ minWidth: 0 }}
                    onClick={e => {
                      e.stopPropagation();
                      // navigate to /projects
                      if (location.pathname !== "/projects") {
                        window.location.href = "/projects";
                      }
                    }}
                  >
                    Projects
                  </span>
                  <span className="ml-2">
                    {projectsOpen ? (
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 9l6 6 6-6" /></svg>
                    ) : (
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                    )}
                  </span>
                </>
              )}
            </button>
            {/* Dynamic project links as sub-list under Projects */}
            {projects.length > 0 && !collapsed && projectsOpen && (
              <div className="flex flex-col gap-1 pl-8">
                {projects.map((project) => (
                  <button
                    key={project.id}
                    onClick={() => {
                      setCurrentProject(project.id);
                      navigate(`/chat/${project.id}`);
                    }}
                    className={`block text-left w-full text-sm px-2 py-1 rounded text-gray-600 bg-white hover:bg-gray-100 truncate ${location.pathname.includes(project.id) ? 'font-bold text-black' : ''}`}
                    style={{ border: 'none' }}
                    title={project.name}
                  >
                    {project.name}
                  </button>
                ))}
              </div>
            )}
          </div>
          <Link
            to="/setup-project"
            className={`flex items-center gap-2 px-4 py-2 rounded text-left transition-all ${
              location.pathname === "/setup-project"
                ? "bg-gray-100 text-black"
                : "text-gray-700 hover:bg-gray-100"
            }`}
          >
            <Plus className="w-4 h-4" aria-label="Create New Project" />
            {!collapsed && <span>Create New Project</span>}
          </Link>


        </nav>
        {/* Collapse/Expand Button at the bottom */}
        <div className="mt-auto flex items-center justify-end pb-4 pr-4">
          <button
            onClick={toggleCollapse}
            className="p-2 bg-white hover:bg-gray-100 rounded focus:outline-none"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
            )}
          </button>
        </div>
      </div>
    </>
  );
}

