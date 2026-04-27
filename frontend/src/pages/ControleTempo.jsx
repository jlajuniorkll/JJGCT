import React, { useMemo, useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { tripService, activityService, configService } from '../services/api';
import { 
  Play, 
  Pause, 
  Square, 
  ArrowLeft, 
  Clock, 
  AlertCircle,
  MessageCircle,
  X,
  CheckCircle,
  Circle,
  Plus,
  ChevronRight,
  GripVertical,
  Pencil,
  Trash2
} from 'lucide-react';
import { format, differenceInSeconds } from 'date-fns';

const ControleTempo = () => {
  const { id, atividadeId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [trip, setTrip] = useState(null);
  const [seconds, setSeconds] = useState(0);
  const [showPauseModal, setShowPauseModal] = useState(false);
  const [pauseReason, setPauseReason] = useState('');
  const [newActivityDesc, setNewActivityDesc] = useState('');
  const [tripStatus, setTripStatus] = useState(null);
  const [activityExpenseAllowedStatuses, setActivityExpenseAllowedStatuses] = useState(['em_andamento']);
  const [activityEditDeleteAllowedStatuses, setActivityEditDeleteAllowedStatuses] = useState(['pendente']);
  const [draggedActivityId, setDraggedActivityId] = useState(null);
  const [suppressClick, setSuppressClick] = useState(false);

  const fetchTrip = useCallback(async () => {
    try {
      const response = await tripService.get(id);
      setTripStatus(response.data.status);
      setTrip(response.data);
    } catch (error) {
      console.error(error);
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
        const allowed = res.data?.trip_activity_expense_allowed_statuses;
        if (Array.isArray(allowed)) setActivityExpenseAllowedStatuses(allowed);
        const editDelAllowed = res.data?.activity_edit_delete_allowed_statuses;
        if (Array.isArray(editDelAllowed)) setActivityEditDeleteAllowedStatuses(editDelAllowed);
      } catch (error) {
        console.error(error);
      }
    };
    fetchConfig();
  }, []);

  useEffect(() => {
    let timer;
    const atividadeAtual = trip?.atividades?.find((a) => String(a.id) === String(atividadeId));
    if (!atividadeId || !atividadeAtual?.inicio) {
      setSeconds(0);
      return () => clearInterval(timer);
    }
    if (atividadeAtual?.status === 'ativa') {
      timer = setInterval(() => {
        const start = new Date(atividadeAtual.inicio);
        const raw = differenceInSeconds(new Date(), start);
        const pausas = Array.isArray(atividadeAtual.pausas) ? atividadeAtual.pausas : [];
        const pausedSeconds = pausas.reduce((acc, p) => {
          if (!p?.inicio) return acc;
          const inicio = new Date(p.inicio);
          const fim = p.fim ? new Date(p.fim) : new Date();
          const d = differenceInSeconds(fim, inicio);
          return acc + (d > 0 ? d : 0);
        }, 0);
        const diff = raw - pausedSeconds;
        setSeconds(diff > 0 ? diff : 0);
      }, 1000);
    } else {
      setSeconds(0);
    }
    return () => clearInterval(timer);
  }, [trip, atividadeId]);

  const userId = useMemo(() => {
    try {
      return JSON.parse(localStorage.getItem('user'))?.id ?? null;
    } catch {
      return null;
    }
  }, []);

  const handleCreatePlanned = async () => {
    if (!newActivityDesc) return;
    try {
      if (!userId) {
        alert('Usuário não identificado. Faça login novamente.');
        return;
      }
      await activityService.create(id, { 
        descricao: newActivityDesc,
        usuario_id: userId
      });
      fetchTrip();
      setNewActivityDesc('');
      navigate(`/viagens/${id}/tempo`);
    } catch (error) {
      console.error(error);
      alert('Erro ao criar atividade');
    }
  };

  const handlePause = async (reasonOverride) => {
    const motivo = reasonOverride ?? pauseReason;
    if (!motivo) return;
    try {
      await activityService.pause(Number(atividadeId), { 
        motivo,
        inicio: new Date().toISOString()
      });
      setShowPauseModal(false);
      setPauseReason('');
      fetchTrip();
    } catch (error) {
      console.error(error);
      alert('Erro ao pausar atividade');
    }
  };

  const handleResume = async () => {
    try {
      const atividadeAtual = trip?.atividades?.find((a) => String(a.id) === String(atividadeId));
      const activePausa = atividadeAtual?.pausas?.find((p) => !p.fim);
      if (activePausa) {
        await activityService.finishPause(activePausa.id);
        fetchTrip();
      }
    } catch (error) {
      console.error(error);
      alert('Erro ao retomar atividade');
    }
  };

  const handleStart = async () => {
    try {
      await activityService.start(Number(atividadeId));
      fetchTrip();
    } catch (error) {
      console.error(error);
      alert('Erro ao iniciar atividade');
    }
  };

  const handleFinish = async () => {
    try {
      await activityService.finish(Number(atividadeId));
      fetchTrip();
      navigate(`/viagens/${id}/tempo`);
    } catch (error) {
      console.error(error);
      alert('Erro ao finalizar atividade');
    }
  };

  const formatTime = (totalSeconds) => {
    const hrs = Math.floor(totalSeconds / 3600);
    const mins = Math.floor((totalSeconds % 3600) / 60);
    const secs = totalSeconds % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const activities = useMemo(() => {
    const list = Array.isArray(trip?.atividades) ? trip.atividades : [];
    return [...list].sort((a, b) => {
      const ao = Number.isFinite(a?.ordem) ? a.ordem : 999999;
      const bo = Number.isFinite(b?.ordem) ? b.ordem : 999999;
      if (ao !== bo) return ao - bo;
      return (a?.id || 0) - (b?.id || 0);
    });
  }, [trip]);

  const currentActivity = useMemo(() => {
    if (!atividadeId) return null;
    return activities.find((a) => String(a.id) === String(atividadeId)) || null;
  }, [activities, atividadeId]);

  const isTimerView = Boolean(atividadeId);

  if (loading) return <div className="p-8 text-center animate-pulse text-gray-500">Carregando controle de tempo...</div>;
  const canMutate = tripStatus ? activityExpenseAllowedStatuses.includes(tripStatus) : false;

  const handleDragStart = (atividade) => (e) => {
    if (!canMutate) return;
    setDraggedActivityId(atividade.id);
    try {
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', String(atividade.id));
    } catch {
      return;
    }
  };

  const handleDragOver = (e) => {
    if (!canMutate) return;
    e.preventDefault();
    try {
      e.dataTransfer.dropEffect = 'move';
    } catch {
      return;
    }
  };

  const handleDrop = (targetId) => async (e) => {
    if (!canMutate) return;
    e.preventDefault();
    e.stopPropagation();

    const raw = (() => {
      try {
        return e.dataTransfer.getData('text/plain');
      } catch {
        return '';
      }
    })();
    const sourceId = draggedActivityId ?? (raw ? Number(raw) : null);
    if (!sourceId || sourceId === targetId) return;

    const currentIds = activities.map((a) => a.id);
    const fromIdx = currentIds.indexOf(sourceId);
    const toIdx = currentIds.indexOf(targetId);
    if (fromIdx < 0 || toIdx < 0) return;

    const nextIds = [...currentIds];
    nextIds.splice(fromIdx, 1);
    nextIds.splice(toIdx, 0, sourceId);

    const byId = new Map(activities.map((a) => [a.id, a]));
    const nextActivities = nextIds.map((aid) => byId.get(aid)).filter(Boolean);

    setTrip((prev) => (prev ? { ...prev, atividades: nextActivities } : prev));
    setDraggedActivityId(null);
    setSuppressClick(true);
    setTimeout(() => setSuppressClick(false), 0);

    try {
      await activityService.reorder(id, nextIds);
      fetchTrip();
    } catch (error) {
      console.error(error);
      fetchTrip();
      alert('Erro ao reordenar atividades');
    }
  };

  const handleDragEnd = () => {
    setDraggedActivityId(null);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8 animate-fade-in py-8 px-4">
      <div className="flex items-center gap-4">
        <button onClick={() => navigate(isTimerView ? `/viagens/${id}/tempo` : `/viagens/${id}`)} className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-500">
          <ArrowLeft size={24} />
        </button>
        <h1 className="text-2xl font-bold text-gray-800">{isTimerView ? 'Controle de Tempo' : 'Atividades'}</h1>
      </div>

      {!isTimerView ? (
        <>
          <div className="bg-white p-6 rounded-3xl shadow-sm border border-gray-100 space-y-4">
            <h2 className="text-lg font-bold text-gray-800">Nova Atividade</h2>
            <div className="space-y-3">
              <input 
                type="text"
                placeholder="Ex: Reunião com Cliente, Vistoria Técnica..."
                className="w-full px-5 py-3 bg-gray-50 border border-gray-200 rounded-2xl outline-none focus:ring-2 focus:ring-blue-500 font-medium"
                value={newActivityDesc}
                onChange={(e) => setNewActivityDesc(e.target.value)}
              />
              <button 
                type="button"
                onClick={handleCreatePlanned}
                disabled={!canMutate || !newActivityDesc}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold py-4 rounded-2xl shadow-lg shadow-blue-200 transition-all active:scale-[0.98] flex items-center justify-center gap-2"
              >
                <Plus size={18} /> Criar Atividade
              </button>
            </div>
          </div>

          <div className="space-y-3">
            {activities.length === 0 ? (
              <div className="bg-white p-10 rounded-3xl border-2 border-dashed border-gray-100 text-center">
                <p className="text-gray-500 font-medium">Nenhuma atividade registrada ainda.</p>
              </div>
            ) : (
              activities.map((a) => {
                const isDone = a.status === 'finalizada';
                const Icon = isDone ? CheckCircle : Circle;
                const iconClass = isDone ? 'bg-emerald-50 text-emerald-600' : 'bg-gray-50 text-gray-500';
                const statusLabel = String(a.status || '').replace('_', ' ');
                const canEditDeleteThis = canMutate && activityEditDeleteAllowedStatuses.includes(a.status);
                return (
                  <div
                    key={a.id}
                    onDragOver={handleDragOver}
                    onDrop={handleDrop(a.id)}
                    onClick={() => {
                      if (suppressClick) return;
                      navigate(`/viagens/${id}/tempo/${a.id}`);
                    }}
                    className={`w-full bg-white p-4 rounded-2xl shadow-sm border border-gray-100 flex items-center justify-between hover:border-blue-100 transition-all text-left ${draggedActivityId === a.id ? 'opacity-70' : ''}`}
                  >
                    <div className="flex items-center gap-4 min-w-0">
                      <div
                        draggable={canMutate}
                        onDragStart={handleDragStart(a)}
                        onDragEnd={handleDragEnd}
                        onClick={(e) => e.stopPropagation()}
                        className={`p-2 rounded-xl ${canMutate ? 'cursor-grab active:cursor-grabbing text-gray-400 hover:text-gray-600 hover:bg-gray-50' : 'text-gray-200'}`}
                        aria-label="Reordenar"
                      >
                        <GripVertical size={18} />
                      </div>
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${iconClass}`}>
                        <Icon size={20} />
                      </div>
                      <div className="min-w-0">
                        <p className="font-bold text-gray-800 text-sm whitespace-normal break-words leading-snug">{a.descricao}</p>
                        <p className="text-xs text-gray-500">{statusLabel}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        disabled={!canEditDeleteThis}
                        onClick={async (e) => {
                          e.stopPropagation();
                          const next = window.prompt('Editar atividade', a.descricao);
                          if (next === null) return;
                          const trimmed = String(next).trim();
                          if (!trimmed) {
                            alert('Descrição inválida');
                            return;
                          }
                          try {
                            await activityService.update(a.id, { descricao: trimmed });
                            fetchTrip();
                          } catch (error) {
                            console.error(error);
                            alert(error?.response?.data?.detail || 'Erro ao editar atividade');
                          }
                        }}
                        className="p-2 rounded-xl border border-gray-200 text-gray-600 hover:bg-gray-50 hover:text-blue-600 transition-colors disabled:opacity-50"
                        aria-label="Editar atividade"
                      >
                        <Pencil size={16} />
                      </button>
                      <button
                        type="button"
                        disabled={!canEditDeleteThis}
                        onClick={async (e) => {
                          e.stopPropagation();
                          const ok = window.confirm('Excluir esta atividade?');
                          if (!ok) return;
                          try {
                            await activityService.remove(a.id);
                            fetchTrip();
                          } catch (error) {
                            console.error(error);
                            alert(error?.response?.data?.detail || 'Erro ao excluir atividade');
                          }
                        }}
                        className="p-2 rounded-xl border border-gray-200 text-gray-600 hover:bg-red-50 hover:text-red-600 transition-colors disabled:opacity-50"
                        aria-label="Excluir atividade"
                      >
                        <Trash2 size={16} />
                      </button>
                      <ChevronRight className="text-gray-300" size={20} />
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </>
      ) : !currentActivity ? (
        <div className="bg-white p-8 rounded-3xl shadow-sm border border-gray-100 text-center space-y-3">
          <AlertCircle className="mx-auto text-gray-400" size={40} />
          <p className="text-gray-600 font-medium">Atividade não encontrada.</p>
        </div>
      ) : currentActivity.status === 'pendente' ? (
        <div className="bg-white p-8 rounded-3xl shadow-xl shadow-blue-100 border border-gray-100 space-y-6">
          <div className="text-center space-y-2">
            <div className="w-16 h-16 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Play size={32} />
            </div>
            <h2 className="text-xl font-bold text-gray-800">Atividade Pendente</h2>
            <p className="text-gray-500">{currentActivity.descricao}</p>
          </div>
          
          <div className="space-y-4">
            <button 
              onClick={handleStart}
              disabled={!canMutate}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold py-5 rounded-2xl shadow-xl shadow-blue-200 transition-all active:scale-[0.98] text-lg flex items-center justify-center gap-2"
            >
              <Play size={20} fill="currentColor" /> Iniciar
            </button>
          </div>
        </div>
      ) : currentActivity.status === 'finalizada' ? (
        <div className="bg-white rounded-3xl shadow-2xl border border-gray-100 overflow-hidden">
          <div className="p-8 bg-emerald-600 text-white text-center space-y-4">
            <p className="text-xs font-bold uppercase tracking-widest opacity-80">Atividade Finalizada</p>
            <h2 className="text-2xl font-black">{currentActivity.descricao}</h2>
            <div className="flex items-center justify-center gap-2 text-sm font-medium opacity-90">
              <CheckCircle size={16} /> Concluída
            </div>
          </div>
          <div className="p-8 space-y-3">
            <div className="flex items-center justify-between text-sm font-medium text-gray-700">
              <span>Início</span>
              <span className="font-bold text-gray-800">{currentActivity.inicio ? format(new Date(currentActivity.inicio), 'dd/MM/yyyy HH:mm') : '--'}</span>
            </div>
            <div className="flex items-center justify-between text-sm font-medium text-gray-700">
              <span>Fim</span>
              <span className="font-bold text-gray-800">{currentActivity.fim ? format(new Date(currentActivity.fim), 'dd/MM/yyyy HH:mm') : '--'}</span>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-3xl shadow-2xl border border-gray-100 overflow-hidden">
          <div className={`p-8 text-white text-center space-y-4 transition-colors duration-500 ${currentActivity.status === 'pausada' ? 'bg-orange-500' : 'bg-blue-600'}`}>
            <p className="text-xs font-bold uppercase tracking-widest opacity-80">
              {currentActivity.status === 'pausada' ? 'Atividade Pausada' : 'Atividade em Curso'}
            </p>
            <h2 className="text-2xl font-black">{currentActivity.descricao}</h2>
            <div className="text-6xl font-black tracking-tighter tabular-nums py-4">
              {currentActivity.status === 'pausada' ? '--:--:--' : formatTime(seconds)}
            </div>
            <div className="flex items-center justify-center gap-2 text-sm font-medium opacity-90">
              <Clock size={16} /> 
              Iniciado às {currentActivity.inicio ? format(new Date(currentActivity.inicio), 'HH:mm') : '--:--'}
            </div>
          </div>

          <div className="p-8 grid grid-cols-2 gap-4">
            {currentActivity.status === 'ativa' ? (
              <button 
                onClick={() => setShowPauseModal(true)}
                disabled={!canMutate}
                className="col-span-1 bg-orange-500 hover:bg-orange-600 text-white font-bold py-4 rounded-2xl shadow-lg shadow-orange-100 flex flex-col items-center gap-2 transition-all active:scale-[0.95]"
              >
                <Pause size={24} fill="currentColor" />
                <span className="text-sm">Pausar</span>
              </button>
            ) : (
              <button 
                onClick={handleResume}
                disabled={!canMutate}
                className="col-span-1 bg-emerald-500 hover:bg-emerald-600 text-white font-bold py-4 rounded-2xl shadow-lg shadow-emerald-100 flex flex-col items-center gap-2 transition-all active:scale-[0.95]"
              >
                <Play size={24} fill="currentColor" />
                <span className="text-sm">Retomar</span>
              </button>
            )}

            <button 
              onClick={handleFinish}
              disabled={!canMutate}
              className="col-span-1 bg-gray-800 hover:bg-gray-900 text-white font-bold py-4 rounded-2xl shadow-lg shadow-gray-200 flex flex-col items-center gap-2 transition-all active:scale-[0.95]"
            >
              <Square size={24} fill="currentColor" />
              <span className="text-sm">Finalizar</span>
            </button>
          </div>

          {currentActivity.pausas?.length > 0 && (
            <div className="px-8 pb-8 space-y-3">
              <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Histórico de Pausas</p>
              <div className="space-y-2">
                {currentActivity.pausas.map((p, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl text-xs font-medium text-gray-600 border border-gray-100">
                    <span className="flex items-center gap-2"><MessageCircle size={14} className="text-orange-500" /> {p.motivo}</span>
                    <span className="text-gray-400 font-bold">{format(new Date(p.inicio), 'HH:mm')} {p.fim ? `- ${format(new Date(p.fim), 'HH:mm')}` : '(Ativa)'}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Modal de Pausa */}
      {showPauseModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[110] flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-8 max-w-sm w-full space-y-6 animate-scale-up">
            <div className="flex justify-between items-center">
              <h3 className="text-xl font-bold text-gray-800">Motivo da Pausa</h3>
              <button onClick={() => setShowPauseModal(false)} className="text-gray-400 hover:text-gray-600"><X size={24} /></button>
            </div>
            
            <div className="grid grid-cols-1 gap-3">
              {['Almoço', 'Pausa Pessoal', 'Deslocamento Interno'].map(reason => (
                <button 
                  key={reason}
                  onClick={() => { setPauseReason(reason); handlePause(reason); }}
                  className={`
                    p-4 rounded-2xl border-2 text-left font-bold transition-all
                    ${pauseReason === reason ? 'border-orange-500 bg-orange-50 text-orange-600' : 'border-gray-100 hover:border-gray-200 text-gray-700'}
                  `}
                >
                  {reason}
                </button>
              ))}
              <input 
                type="text"
                placeholder="Outro motivo..."
                className="w-full p-4 rounded-2xl border-2 border-gray-100 outline-none focus:ring-2 focus:ring-orange-500 font-medium"
                value={pauseReason}
                onChange={(e) => setPauseReason(e.target.value)}
              />
            </div>

            <button 
              onClick={handlePause}
              disabled={!pauseReason}
              className="w-full bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white font-bold py-4 rounded-2xl shadow-lg shadow-orange-100 transition-all active:scale-[0.98]"
            >
              Confirmar Pausa
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ControleTempo;
