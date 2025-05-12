import { Link } from 'react-router-dom';

export default function Header() {
  return (
    <nav className="w-full fixed top-0 left-0 z-50 bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="text-2xl font-bold text-indigo-600">DataJar</Link>
          </div>
          <div className="flex items-center space-x-4">
            <Link to="/blog" className="text-gray-600 hover:text-gray-900 px-3 py-2">Blog</Link>
            <Link to="/projects" className="text-gray-600 hover:text-gray-900 px-3 py-2">Projects</Link>
            <Link to="/setup-project" className="text-gray-600 hover:text-gray-900 px-3 py-2">Setup Project</Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
