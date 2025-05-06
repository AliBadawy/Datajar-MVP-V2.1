import ProjectSetupWizard from '../components/project-setup/ProjectSetupWizard';

export function SetupProjectPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-4xl">
        <h1 className="text-3xl font-bold text-black mb-6 text-center">Create a New Project</h1>
        <ProjectSetupWizard />
      </div>
    </div>
  );
}

export default SetupProjectPage;
