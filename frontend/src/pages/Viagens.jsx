import React, { useState, useEffect } from 'react';
import { tripService, userService, vehicleService } from '../services/api';
import { 
  Plus, 
  Search, 
  MapPin, 
  Calendar, 
  Users, 
  Car, 
  X,
  CheckCircle,
  Clock,
  AlertCircle
} from 'lucide-react';
import { format } from 'date-fns';
import { Link } from 'react-router-dom';

const Viagens = () => {
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [filterStatus, setFilterStatus] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  
  // Form state
  const [formData, setFormData] = useState({
    cliente: '',
    motivo: '',
    local_partida: '',
    local_chegada: '',
    data_hora_prevista_saida: '',
    data_hora_prevista_chegada: '',
    meio_transporte: 'carona',
    participantes_ids: [],
    transporte: {
      veiculo_id: '',
      motorista_id: '',
      km_saida: ''
    }
  });

  const [availableUsers, setAvailableUsers] = useState([]);
  const [availableVehicles, setAvailableVehicles] = useState([]);

  useEffect(() => {
    fetchTrips();
    fetchInitialData();
  }, []);

  const fetchTrips = async () => {
    try {
      const response = await tripService.list();
      setTrips(response.data);
    } catch (err) {
      console.error('Error fetching trips:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchInitialData = async () => {
    try {
      const [usersRes, vehiclesRes] = await Promise.all([
        userService.list(),
        vehicleService.list()
      ]);
      setAvailableUsers(usersRes.data);
      setAvailableVehicles(vehiclesRes.data);
    } catch (err) {
      console.error('Error fetching users/vehicles:', err);
    }
  };

  const handleCreateTrip = async (e) => {
    e.preventDefault();
    try {
      const payload = { ...formData };
      if (!['carro empresa', 'carro próprio'].includes(payload.meio_transporte)) {
        delete payload.transporte;
      } else {
        payload.transporte = { ...payload.transporte };
        if (payload.transporte.km_saida === '') delete payload.transporte.km_saida;
      }
      await tripService.create(payload);
      setShowModal(false);
      fetchTrips();
      // Reset form
      setFormData({
        cliente: '',
        motivo: '',
        local_partida: '',
        local_chegada: '',
        data_hora_prevista_saida: '',
        data_hora_prevista_chegada: '',
        meio_transporte: 'carona',
        participantes_ids: [],
        transporte: { veiculo_id: '', motorista_id: '', km_saida: '' }
      });
    } catch (err) {
      alert(err.response?.data?.detail || 'Erro ao criar viagem');
    }
  };

  const filteredTrips = trips.filter(trip => {
    const matchesStatus = !filterStatus || trip.status === filterStatus;
    const matchesSearch = !searchTerm || 
      trip.cliente.toLowerCase().includes(searchTerm.toLowerCase()) ||
      trip.local_chegada.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const statusColors = {
    planejada: 'bg-indigo-100 text-indigo-700',
    em_andamento: 'bg-orange-100 text-orange-700',
    finalizada: 'bg-emerald-100 text-emerald-700',
    cancelada: 'bg-red-100 text-red-700'
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Gestão de Viagens</h1>
          <p className="text-gray-500 font-medium">Controle e acompanhamento de rotas corporativas.</p>
        </div>
        <button 
          onClick={() => setShowModal(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-bold shadow-lg shadow-blue-200 transition-all flex items-center justify-center gap-2"
        >
          <Plus size={20} />
          Nova Viagem
        </button>
      </header>

      {/* Filters */}
      <div className="bg-white p-4 rounded-2xl shadow-sm border border-gray-100 flex flex-col md:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input 
            type="text" 
            placeholder="Buscar por cliente ou destino..."
            className="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-blue-500"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="flex gap-2">
          <select 
            className="px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-blue-500 font-medium text-gray-600"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
          >
            <option value="">Todos os Status</option>
            <option value="planejada">Planejada</option>
            <option value="em_andamento">Em Andamento</option>
            <option value="finalizada">Finalizada</option>
            <option value="cancelada">Cancelada</option>
          </select>
        </div>
      </div>

      {/* Trip List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          <p className="col-span-full text-center py-12 text-gray-500">Carregando viagens...</p>
        ) : filteredTrips.length === 0 ? (
          <div className="col-span-full bg-white p-12 rounded-2xl border-2 border-dashed border-gray-100 flex flex-col items-center justify-center text-center">
            <AlertCircle className="text-gray-400 mb-4" size={48} />
            <p className="text-gray-500 font-medium">Nenhuma viagem encontrada com os filtros atuais.</p>
          </div>
        ) : (
          filteredTrips.map(trip => (
            <Link 
              key={trip.id} 
              to={`/viagens/${trip.id}`}
              className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-all group"
            >
              <div className="flex justify-between items-start mb-4">
                <div className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${statusColors[trip.status]}`}>
                  {trip.status.replace('_', ' ')}
                </div>
                <span className="text-xs font-bold text-gray-400">#{trip.id}</span>
              </div>
              
              <h3 className="text-lg font-bold text-gray-800 mb-2 group-hover:text-blue-600 transition-colors">{trip.cliente}</h3>
              <p className="text-sm text-gray-500 mb-4 line-clamp-2">{trip.motivo}</p>
              
              <div className="space-y-3 pt-4 border-t border-gray-50">
                <div className="flex items-center gap-3 text-sm text-gray-600 font-medium">
                  <MapPin size={16} className="text-blue-500" />
                  <span className="truncate">{trip.local_partida} → {trip.local_chegada}</span>
                </div>
                <div className="flex items-center gap-3 text-sm text-gray-600 font-medium">
                  <Calendar size={16} className="text-blue-500" />
                  <span>{format(new Date(trip.data_hora_prevista_saida), 'dd/MM/yyyy HH:mm')}</span>
                </div>
                <div className="flex items-center justify-between pt-2">
                  <div className="flex -space-x-2">
                    {trip.participantes?.slice(0, 3).map((p, idx) => (
                      <div key={idx} className="w-8 h-8 rounded-full bg-blue-100 border-2 border-white flex items-center justify-center text-[10px] font-bold text-blue-600">
                        {p.nome[0]}
                      </div>
                    ))}
                    {trip.participantes?.length > 3 && (
                      <div className="w-8 h-8 rounded-full bg-gray-100 border-2 border-white flex items-center justify-center text-[10px] font-bold text-gray-500">
                        +{trip.participantes.length - 3}
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-xs font-bold text-gray-400">
                    <Car size={14} />
                    {trip.meio_transporte}
                  </div>
                </div>
              </div>
            </Link>
          ))
        )}
      </div>

      {/* Modal Criar Viagem */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col animate-scale-up">
            <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-blue-600 text-white">
              <h2 className="text-xl font-bold">Cadastrar Nova Viagem</h2>
              <button onClick={() => setShowModal(false)} className="hover:bg-white/20 p-2 rounded-lg transition-colors">
                <X size={24} />
              </button>
            </div>

            <form onSubmit={handleCreateTrip} className="p-6 overflow-y-auto space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-bold text-gray-700 mb-1">Cliente</label>
                    <input 
                      type="text" required
                      className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-blue-500"
                      value={formData.cliente}
                      onChange={(e) => setFormData({...formData, cliente: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-gray-700 mb-1">Motivo</label>
                    <textarea 
                      required
                      className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-blue-500 h-24"
                      value={formData.motivo}
                      onChange={(e) => setFormData({...formData, motivo: e.target.value})}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-bold text-gray-700 mb-1">Partida</label>
                      <input 
                        type="text" required
                        className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-blue-500"
                        value={formData.local_partida}
                        onChange={(e) => setFormData({...formData, local_partida: e.target.value})}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-gray-700 mb-1">Chegada</label>
                      <input 
                        type="text" required
                        className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-blue-500"
                        value={formData.local_chegada}
                        onChange={(e) => setFormData({...formData, local_chegada: e.target.value})}
                      />
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-bold text-gray-700 mb-1">Saída Prevista</label>
                    <input 
                      type="datetime-local" required
                      className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-blue-500"
                      value={formData.data_hora_prevista_saida}
                      onChange={(e) => setFormData({...formData, data_hora_prevista_saida: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-gray-700 mb-1">Chegada Prevista</label>
                    <input 
                      type="datetime-local" required
                      className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-blue-500"
                      value={formData.data_hora_prevista_chegada}
                      onChange={(e) => setFormData({...formData, data_hora_prevista_chegada: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-gray-700 mb-1">Meio de Transporte</label>
                    <select 
                      className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-blue-500"
                      value={formData.meio_transporte}
                      onChange={(e) => setFormData({...formData, meio_transporte: e.target.value})}
                    >
                      <option value="carona">Carona</option>
                      <option value="terceiros">Terceiros</option>
                      <option value="carro empresa">Carro Empresa</option>
                      <option value="carro próprio">Carro Próprio</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Dynamic Fields for Vehicle/Driver */}
              {['carro empresa', 'carro próprio'].includes(formData.meio_transporte) && (
                <div className="bg-blue-50 p-6 rounded-2xl border border-blue-100 space-y-4">
                  <h3 className="font-bold text-blue-800 flex items-center gap-2">
                    <Car size={18} /> Dados do Transporte
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-blue-600 mb-1 uppercase tracking-wider">Veículo</label>
                      <select 
                        required
                        className="w-full px-3 py-2 bg-white border border-blue-200 rounded-lg outline-none focus:ring-2 focus:ring-blue-500"
                        value={formData.transporte.veiculo_id}
                        onChange={(e) => setFormData({
                          ...formData, 
                          transporte: { ...formData.transporte, veiculo_id: e.target.value }
                        })}
                      >
                        <option value="">Selecione...</option>
                        {availableVehicles.map(v => (
                          <option key={v.id} value={v.id}>{v.modelo} ({v.placa})</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-blue-600 mb-1 uppercase tracking-wider">Motorista</label>
                      <select 
                        required
                        className="w-full px-3 py-2 bg-white border border-blue-200 rounded-lg outline-none focus:ring-2 focus:ring-blue-500"
                        value={formData.transporte.motorista_id}
                        onChange={(e) => setFormData({
                          ...formData, 
                          transporte: { ...formData.transporte, motorista_id: e.target.value }
                        })}
                      >
                        <option value="">Selecione...</option>
                        {availableUsers.filter(u => u.tem_cnh).map(u => (
                          <option key={u.id} value={u.id}>{u.nome}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              )}

              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">Participantes</label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 max-h-40 overflow-y-auto p-2 bg-gray-50 rounded-xl border border-gray-100">
                  {availableUsers.map(user => (
                    <label key={user.id} className="flex items-center gap-2 p-2 hover:bg-white rounded-lg cursor-pointer transition-colors">
                      <input 
                        type="checkbox"
                        checked={formData.participantes_ids.includes(user.id)}
                        onChange={(e) => {
                          const ids = e.target.checked 
                            ? [...formData.participantes_ids, user.id]
                            : formData.participantes_ids.filter(id => id !== user.id);
                          setFormData({...formData, participantes_ids: ids});
                        }}
                        className="rounded text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm font-medium text-gray-700 truncate">{user.nome}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="pt-6 border-t border-gray-100 flex gap-4">
                <button 
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 px-6 py-3 border border-gray-200 text-gray-600 rounded-xl font-bold hover:bg-gray-50 transition-colors"
                >
                  Cancelar
                </button>
                <button 
                  type="submit"
                  className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 shadow-lg shadow-blue-200 transition-all active:scale-[0.98]"
                >
                  Salvar Viagem
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Viagens;
