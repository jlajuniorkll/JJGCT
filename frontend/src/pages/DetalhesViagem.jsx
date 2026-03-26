import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { tripService, expenseService, configService } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { 
  MapPin, 
  Calendar, 
  Users, 
  Car, 
  Clock, 
  DollarSign, 
  ArrowLeft,
  ChevronRight,
  Plus,
  CheckCircle,
  FileText,
  Navigation,
  XCircle,
  Pencil,
  Trash2
} from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

const DetalhesViagem = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [trip, setTrip] = useState(null);
  const [loading, setLoading] = useState(true);
  const [blockedStatuses, setBlockedStatuses] = useState(['em_andamento', 'finalizada', 'cancelada']);
  const [activityExpenseAllowedStatuses, setActivityExpenseAllowedStatuses] = useState(['em_andamento']);

  const fetchTrip = useCallback(async () => {
    try {
      const response = await tripService.get(id);
      setTrip(response.data);
    } catch (err) {
      console.error('Error fetching trip:', err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchTrip();
  }, [fetchTrip]);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const res = await configService.get();
        const statuses = res.data?.trip_edit_blocked_statuses;
        if (Array.isArray(statuses)) setBlockedStatuses(statuses);
        const allowed = res.data?.trip_activity_expense_allowed_statuses;
        if (Array.isArray(allowed)) setActivityExpenseAllowedStatuses(allowed);
      } catch (err) {
        console.error(err);
      }
    };
    fetchConfig();
  }, []);

  if (loading) return <div className="p-8 text-center animate-pulse">Carregando detalhes...</div>;
  if (!trip) return <div className="p-8 text-center">Viagem não encontrada.</div>;

  const canFinish =
    trip.status === 'em_andamento' &&
    (trip.atividades || []).every((a) => a.status === 'finalizada');
  const canEdit = !blockedStatuses.includes(trip.status);
  const canMutateActivitiesExpenses = activityExpenseAllowedStatuses.includes(trip.status);
  const canRegisterDeparture = trip.status === 'planejada' && (
    (user?.id && trip?.responsavel_id === user.id) ||
    (user?.id && trip?.transporte?.motorista_id === user.id)
  );

  const statusColors = {
    planejada: 'bg-indigo-100 text-indigo-700',
    em_andamento: 'bg-orange-100 text-orange-700',
    finalizada: 'bg-emerald-100 text-emerald-700',
    cancelada: 'bg-red-100 text-red-700'
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate('/viagens')}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-500"
          >
            <ArrowLeft size={24} />
          </button>
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-bold text-gray-800">{trip.cliente}</h1>
              <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${statusColors[trip.status]}`}>
                {trip.status.replace('_', ' ')}
              </span>
            </div>
            <p className="text-gray-500 font-medium flex items-center gap-1">
              <MapPin size={16} /> {trip.local_partida} → {trip.local_chegada}
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          {canEdit && (
            <button
              type="button"
              onClick={() => navigate(`/viagens/${trip.id}/editar`)}
              className="bg-white hover:bg-gray-50 text-gray-700 px-6 py-3 rounded-xl font-bold shadow-sm border border-gray-200 transition-all active:scale-[0.98] flex items-center gap-2"
            >
              <Pencil size={20} /> Editar
            </button>
          )}
          {(trip.status === 'planejada' || trip.status === 'em_andamento') && (
            <button
              type="button"
              onClick={async () => {
                const ok = window.confirm('Cancelar esta viagem?');
                if (!ok) return;
                try {
                  await tripService.cancel(trip.id);
                  fetchTrip();
                } catch (err) {
                  console.error(err);
                  alert(err?.response?.data?.detail || 'Erro ao cancelar viagem');
                }
              }}
              className="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-xl font-bold shadow-lg shadow-red-200 transition-all active:scale-[0.98] flex items-center gap-2"
            >
              <XCircle size={20} /> Cancelar Viagem
            </button>
          )}
          {trip.status === 'planejada' && (
            <button 
              onClick={() => navigate(`/viagens/${trip.id}/saida`)}
              disabled={!canRegisterDeparture}
              className={`px-6 py-3 rounded-xl font-bold transition-all active:scale-[0.98] flex items-center gap-2 ${
                canRegisterDeparture
                  ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-200'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }`}
            >
              <Navigation size={20} /> Registrar Saída
            </button>
          )}
          {trip.status === 'em_andamento' && (
            <button 
              onClick={() => navigate(`/viagens/${trip.id}/chegada`)}
              disabled={!canFinish}
              className={`
                px-6 py-3 rounded-xl font-bold transition-all active:scale-[0.98] flex items-center gap-2
                ${canFinish 
                  ? 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg shadow-emerald-200' 
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'}
              `}
            >
              <CheckCircle size={20} /> Finalizar Viagem
            </button>
          )}
          {trip.status === 'finalizada' && (
            <Link 
              to={`/viagens/${trip.id}/relatorio`}
              className="bg-gray-800 hover:bg-gray-900 text-white px-6 py-3 rounded-xl font-bold shadow-lg shadow-gray-200 transition-all active:scale-[0.98] flex items-center gap-2"
            >
              <FileText size={20} /> Ver Relatório
            </Link>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Left Column: Info & Participants */}
        <div className="md:col-span-2 space-y-8">
          {/* Trip Info Card */}
          <section className="bg-white p-6 rounded-3xl shadow-sm border border-gray-100 space-y-4">
            <h2 className="text-lg font-bold text-gray-800">Sobre a Viagem</h2>
            <p className="text-gray-600 leading-relaxed">{trip.motivo}</p>
            <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-50">
              <div className="space-y-1">
                <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Partida Prevista</p>
                <p className="text-sm font-medium text-gray-700">
                  {format(new Date(trip.data_hora_prevista_saida), 'dd MMM yyyy, HH:mm', { locale: ptBR })}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Chegada Prevista</p>
                <p className="text-sm font-medium text-gray-700">
                  {format(new Date(trip.data_hora_prevista_chegada), 'dd MMM yyyy, HH:mm', { locale: ptBR })}
                </p>
              </div>
            </div>
          </section>

          {/* Activities Section */}
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                <Clock className="text-blue-600" size={20} /> Atividades
              </h2>
              {canMutateActivitiesExpenses && (
                <Link to={`/viagens/${trip.id}/tempo`} className="text-blue-600 font-bold text-sm flex items-center gap-1 hover:underline">
                  <Plus size={16} /> Nova Atividade
                </Link>
              )}
            </div>

            <div className="space-y-3">
              {trip.atividades?.length === 0 ? (
                <p className="text-sm text-gray-500 bg-gray-50 p-6 rounded-2xl text-center border-2 border-dashed border-gray-100">
                  Nenhuma atividade registrada ainda.
                </p>
              ) : (
                trip.atividades.map(atv => (
                  <div key={atv.id} className="bg-white p-4 rounded-2xl shadow-sm border border-gray-100 flex items-center justify-between group hover:border-blue-100 transition-all">
                    <div className="flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${atv.status === 'finalizada' ? 'bg-emerald-50 text-emerald-600' : 'bg-blue-50 text-blue-600'}`}>
                        {atv.status === 'finalizada' ? <CheckCircle size={20} /> : <Clock size={20} />}
                      </div>
                      <div>
                        <p className="font-bold text-gray-800 text-sm">{atv.descricao}</p>
                        <p className="text-xs text-gray-500">{atv.status}</p>
                      </div>
                    </div>
                    {canMutateActivitiesExpenses && atv.status !== 'finalizada' && (
                      <Link to={`/viagens/${trip.id}/tempo`} className="p-2 text-gray-400 hover:text-blue-600 transition-colors">
                        <ChevronRight size={20} />
                      </Link>
                    )}
                  </div>
                ))
              )}
            </div>
          </section>

          {/* Expenses Section */}
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                <DollarSign className="text-emerald-600" size={20} /> Despesas
              </h2>
              {canMutateActivitiesExpenses && (
                <Link to={`/viagens/${trip.id}/despesa`} className="text-emerald-600 font-bold text-sm flex items-center gap-1 hover:underline">
                  <Plus size={16} /> Adicionar Despesa
                </Link>
              )}
            </div>

            <div className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
              {trip.despesas?.length === 0 ? (
                <p className="text-sm text-gray-500 p-8 text-center">Nenhuma despesa registrada.</p>
              ) : (
                <table className="w-full text-sm text-left">
                  <thead className="bg-gray-50 text-gray-400 font-bold uppercase text-[10px] tracking-widest">
                    <tr>
                      <th className="px-6 py-4">Descrição</th>
                      <th className="px-6 py-4">Registrado por</th>
                      <th className="px-6 py-4 text-right">Valor</th>
                      <th className="px-6 py-4 text-right">Ações</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {trip.despesas.map(exp => (
                      <tr key={exp.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-6 py-4 font-medium text-gray-700">{exp.descricao}</td>
                        <td className="px-6 py-4 text-gray-600 font-medium">{exp.criado_por?.nome || '--'}</td>
                        <td className="px-6 py-4 text-right font-bold text-gray-800">
                          R$ {exp.valor.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex justify-end gap-2">
                            <button
                              type="button"
                              disabled={!canMutateActivitiesExpenses}
                              onClick={() => navigate(`/viagens/${trip.id}/despesa/${exp.id}`)}
                              className="p-2 rounded-xl border border-gray-200 text-gray-600 hover:bg-gray-50 hover:text-blue-600 transition-colors disabled:opacity-50"
                              aria-label="Editar despesa"
                            >
                              <Pencil size={16} />
                            </button>
                            <button
                              type="button"
                              disabled={!canMutateActivitiesExpenses}
                              onClick={async () => {
                                const ok = window.confirm('Excluir esta despesa? O anexo será removido.');
                                if (!ok) return;
                                try {
                                  await expenseService.remove(exp.id);
                                  fetchTrip();
                                } catch (err) {
                                  console.error(err);
                                  alert(err?.response?.data?.detail || 'Erro ao excluir despesa');
                                }
                              }}
                              className="p-2 rounded-xl border border-gray-200 text-gray-600 hover:bg-red-50 hover:text-red-600 transition-colors disabled:opacity-50"
                              aria-label="Excluir despesa"
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="bg-emerald-50">
                    <tr>
                      <td className="px-6 py-4 font-bold text-emerald-800">Total</td>
                      <td className="px-6 py-4 text-right font-bold text-emerald-800 text-lg">
                        R$ {trip.despesas.reduce((acc, curr) => acc + curr.valor, 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              )}
            </div>
          </section>
        </div>

        {/* Right Column: Sidebar info */}
        <div className="space-y-8">
          {/* Participants */}
          <div className="bg-white p-6 rounded-3xl shadow-sm border border-gray-100 space-y-6">
            <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
              <Users className="text-blue-600" size={20} /> Participantes
            </h2>
            <div className="space-y-4">
              {trip.participantes?.map(p => (
                <div key={p.id} className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center text-blue-600 font-bold shadow-sm">
                    {p.nome[0]}
                  </div>
                  <div>
                    <p className="text-sm font-bold text-gray-800">{p.nome}</p>
                    <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">{p.tipousuario}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Transport Info */}
          <div className="bg-blue-600 p-6 rounded-3xl shadow-xl shadow-blue-100 text-white space-y-6">
            <h2 className="text-lg font-bold flex items-center gap-2">
              <Car size={20} /> Transporte
            </h2>
            <div className="space-y-4">
              <div className="p-4 bg-white/10 rounded-2xl backdrop-blur-md">
                <p className="text-[10px] font-bold text-blue-200 uppercase tracking-widest mb-1">Meio</p>
                <p className="text-sm font-bold capitalize">{trip.meio_transporte}</p>
              </div>

              {trip.transporte && (
                <>
                  <div className="p-4 bg-white/10 rounded-2xl backdrop-blur-md">
                    <p className="text-[10px] font-bold text-blue-200 uppercase tracking-widest mb-1">Veículo</p>
                    <p className="text-sm font-bold">{trip.transporte.veiculo?.modelo || '--'}</p>
                    <p className="text-xs text-blue-100">{trip.transporte.veiculo?.placa || '--'}</p>
                  </div>
                  <div className="p-4 bg-white/10 rounded-2xl backdrop-blur-md">
                    <p className="text-[10px] font-bold text-blue-200 uppercase tracking-widest mb-1">Motorista</p>
                    <p className="text-sm font-bold">{trip.transporte.motorista?.nome || '--'}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-4 bg-white/10 rounded-2xl backdrop-blur-md text-center">
                      <p className="text-[10px] font-bold text-blue-200 uppercase tracking-widest mb-1">KM Inicial</p>
                      <p className="text-lg font-bold">{trip.transporte.km_saida}</p>
                    </div>
                    <div className="p-4 bg-white/10 rounded-2xl backdrop-blur-md text-center">
                      <p className="text-[10px] font-bold text-blue-200 uppercase tracking-widest mb-1">KM Final</p>
                      <p className="text-lg font-bold">{trip.transporte.km_chegada || '--'}</p>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DetalhesViagem;
