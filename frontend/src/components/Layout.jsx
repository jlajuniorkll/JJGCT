import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { 
  Home, 
  MapPin, 
  Users, 
  Car, 
  LogOut, 
  Menu, 
  X,
  Clock,
  DollarSign,
  FileText
} from 'lucide-react';

const Layout = ({ children }) => {
  const { user, logout } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const menuItems = [
    { name: 'Dashboard', icon: Home, path: '/' },
    { name: 'Viagens', icon: MapPin, path: '/viagens' },
    { name: 'Usuários', icon: Users, path: '/admin/usuarios', adminOnly: true },
    { name: 'Veículos', icon: Car, path: '/admin/veiculos', adminOnly: true },
  ];

  const filteredItems = menuItems.filter(item => !item.adminOnly || user?.tipousuario === 'admin');

  return (
    <div className="min-height-screen bg-gray-100 flex flex-col md:flex-row">
      {/* Mobile Header */}
      <div className="md:hidden bg-blue-600 text-white p-4 flex justify-between items-center shadow-md">
        <h1 className="text-xl font-bold">Viagens Corporativas</h1>
        <button onClick={() => setIsMenuOpen(!isMenuOpen)}>
          {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Sidebar / Mobile Menu */}
      <div className={`
        ${isMenuOpen ? 'block' : 'hidden'} 
        md:block md:w-64 bg-white border-r border-gray-200 h-screen sticky top-0 z-50
      `}>
        <div className="hidden md:flex p-6 border-b border-gray-100 items-center gap-2">
          <MapPin className="text-blue-600" />
          <h1 className="text-xl font-bold text-gray-800">Corporate Travel</h1>
        </div>

        <nav className="p-4 space-y-2">
          {filteredItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setIsMenuOpen(false)}
                className={`
                  flex items-center gap-3 p-3 rounded-lg transition-colors
                  ${isActive ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-50'}
                `}
              >
                <Icon size={20} />
                <span className="font-medium">{item.name}</span>
              </Link>
            );
          })}
        </nav>

        <div className="absolute bottom-0 w-full p-4 border-t border-gray-100">
          <div className="flex items-center gap-3 mb-4 px-2">
            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold">
              {user?.nome?.[0]}
            </div>
            <div className="overflow-hidden">
              <p className="text-sm font-bold text-gray-800 truncate">{user?.nome}</p>
              <p className="text-xs text-gray-500 truncate">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full p-3 text-red-600 hover:bg-red-50 rounded-lg transition-colors font-medium"
          >
            <LogOut size={20} />
            <span>Sair</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <main className="flex-1 p-4 md:p-8 overflow-auto">
        {children}
      </main>
    </div>
  );
};

export default Layout;
