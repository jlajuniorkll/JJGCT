import React, { useState, useEffect } from 'react';
import { tripService } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { 
  Briefcase, 
  CheckCircle, 
  Clock, 
  TrendingUp,
  Users,
  Car,
  MapPin,
  Calendar,
  ChevronRight
} from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { Link } from 'react-router-dom';

const StatCard = ({ title, value, icon, color }) => (
  <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center gap-4 group hover:shadow-md transition-shadow">
    <div className={`p-4 rounded-xl ${color} text-white shadow-lg`}>
      {React.createElement(icon, { size: 24 })}
    </div>
    <div>
      <p className="text-sm font-medium text-gray-500">{title}</p>
      <p className="text-2xl font-bold text-gray-800">{value}</p>
    </div>
  </div>
);

const Dashboard = () => {
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await tripService.list();
        setTrips(response.data);
      } catch (err) {
        console.error('Error fetching trips:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const stats = {
    total: trips.length,
    active: trips.filter(t => t.status === 'em_andamento').length,
    completed: trips.filter(t => t.status === 'finalizada').length,
    planned: trips.filter(t => t.status === 'planejada').length,
  };

  const activeTrips = trips.filter(t => t.status === 'em_andamento').slice(0, 5);

  if (loading) return <div className="animate-pulse flex items-center justify-center h-full">Carregando...</div>;

  return (
    <div className="space-y-8 animate-fade-in">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Olá, {user?.nome}! 👋</h1>
          <p className="text-gray-500 font-medium">Bem-vindo ao sistema de Viagens Corporativas.</p>
        </div>
        <Link 
          to="/viagens" 
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-bold shadow-lg shadow-blue-200 transition-all active:scale-[0.98] flex items-center justify-center gap-2"
        >
          Nova Viagem
        </Link>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Total de Viagens" value={stats.total} icon={Briefcase} color="bg-blue-500 shadow-blue-200" />
        <StatCard title="Em Andamento" value={stats.active} icon={Clock} color="bg-orange-500 shadow-orange-200" />
        <StatCard title="Finalizadas" value={stats.completed} icon={CheckCircle} color="bg-emerald-500 shadow-emerald-200" />
        <StatCard title="Planejadas" value={stats.planned} icon={Calendar} color="bg-indigo-500 shadow-indigo-200" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Active Trips Section */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-gray-800">Viagens em Andamento</h2>
            <Link to="/viagens" className="text-sm font-bold text-blue-600 hover:underline">Ver todas</Link>
          </div>

          <div className="space-y-4">
            {activeTrips.length === 0 ? (
              <div className="bg-white p-12 rounded-2xl border-2 border-dashed border-gray-100 flex flex-col items-center justify-center text-center">
                <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center text-gray-400 mb-4">
                  <MapPin size={32} />
                </div>
                <p className="text-gray-500 font-medium">Nenhuma viagem em andamento no momento.</p>
              </div>
            ) : (
              activeTrips.map(trip => (
                <Link 
                  key={trip.id} 
                  to={`/viagens/${trip.id}`}
                  className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100 flex items-center justify-between hover:border-blue-200 hover:shadow-md transition-all group"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center font-bold">
                      {trip.cliente?.[0]}
                    </div>
                    <div>
                      <p className="font-bold text-gray-800">{trip.cliente}</p>
                      <p className="text-sm text-gray-500 flex items-center gap-1">
                        <MapPin size={14} /> {trip.local_chegada}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="hidden sm:block text-right">
                      <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Previsto</p>
                      <p className="text-sm font-medium text-gray-600">
                        {format(new Date(trip.data_hora_prevista_chegada), 'dd MMM, HH:mm', { locale: ptBR })}
                      </p>
                    </div>
                    <ChevronRight className="text-gray-300 group-hover:text-blue-500 group-hover:translate-x-1 transition-all" />
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>

        {/* Quick Actions / Activity Feed */}
        <div className="space-y-6">
          <h2 className="text-xl font-bold text-gray-800">Ações Rápidas</h2>
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 space-y-4">
            <Link 
              to="/admin/usuarios"
              className="w-full flex items-center gap-3 p-4 rounded-xl hover:bg-blue-50 text-gray-700 hover:text-blue-600 transition-colors border border-transparent hover:border-blue-100 font-medium"
            >
              <div className="p-2 bg-gray-50 rounded-lg group-hover:bg-blue-100">
                <Users size={20} />
              </div>
              Gerenciar Usuários
            </Link>
            <Link 
              to="/admin/veiculos"
              className="w-full flex items-center gap-3 p-4 rounded-xl hover:bg-blue-50 text-gray-700 hover:text-blue-600 transition-colors border border-transparent hover:border-blue-100 font-medium"
            >
              <div className="p-2 bg-gray-50 rounded-lg group-hover:bg-blue-100">
                <Car size={20} />
              </div>
              Frota de Veículos
            </Link>
            <button
              className="w-full flex items-center gap-3 p-4 rounded-xl hover:bg-blue-50 text-gray-700 hover:text-blue-600 transition-colors border border-transparent hover:border-blue-100 font-medium"
            >
              <div className="p-2 bg-gray-50 rounded-lg group-hover:bg-blue-100">
                <TrendingUp size={20} />
              </div>
              Relatórios Mensais
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
