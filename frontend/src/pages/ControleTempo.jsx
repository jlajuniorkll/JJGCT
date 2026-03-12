import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { tripService, activityService } from '../services/api';
import { 
  Play, 
  Pause, 
  Square, 
  ArrowLeft, 
  Clock, 
  AlertCircle,
  MessageCircle,
  X
} from 'lucide-react';
import { format, differenceInSeconds } from 'date-fns';

const ControleTempo = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [activeActivity, setActiveActivity] = useState(null);
  const [seconds, setSeconds] = useState(0);
  const [showPauseModal, setShowPauseModal] = useState(false);
  const [pauseReason, setPauseReason] = useState('');
  const [newActivityDesc, setNewActivityDesc] = useState('');

  const fetchTrip = useCallback(async () => {
    try {
      const response = await tripService.get(id);
      const active = response.data.atividades.find((a) => a.status !== 'finalizada');
      setActiveActivity(active || null);
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
    let timer;
    if (activeActivity?.status === 'ativa' && activeActivity.inicio) {
      timer = setInterval(() => {
        const start = new Date(activeActivity.inicio);
        const diff = differenceInSeconds(new Date(), start);
        setSeconds(diff);
      }, 1000);
    } else {
      setSeconds(0);
    }
    return () => clearInterval(timer);
  }, [activeActivity]);

  const handleCreateAndStart = async () => {
    if (!newActivityDesc) return;
    try {
      const res = await activityService.create(id, { 
        descricao: newActivityDesc,
        usuario_id: JSON.parse(localStorage.getItem('user')).id
      });
      await activityService.start(res.data.id);
      fetchTrip();
      setNewActivityDesc('');
    } catch (error) {
      console.error(error);
      alert('Erro ao iniciar atividade');
    }
  };

  const handlePause = async () => {
    if (!pauseReason) return;
    try {
      await activityService.pause(activeActivity.id, { 
        motivo: pauseReason,
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
      const activePausa = activeActivity.pausas.find(p => !p.fim);
      if (activePausa) {
        await activityService.finishPause(activePausa.id);
        fetchTrip();
      }
    } catch (error) {
      console.error(error);
      alert('Erro ao retomar atividade');
    }
  };

  const handleFinish = async () => {
    try {
      await activityService.finish(activeActivity.id);
      fetchTrip();
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

  if (loading) return <div className="p-8 text-center animate-pulse text-gray-500">Carregando controle de tempo...</div>;

  return (
    <div className="max-w-2xl mx-auto space-y-8 animate-fade-in py-8 px-4">
      <div className="flex items-center gap-4">
        <button onClick={() => navigate(`/viagens/${id}`)} className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-500">
          <ArrowLeft size={24} />
        </button>
        <h1 className="text-2xl font-bold text-gray-800">Controle de Tempo</h1>
      </div>

      {!activeActivity ? (
        <div className="bg-white p-8 rounded-3xl shadow-xl shadow-blue-100 border border-gray-100 space-y-6">
          <div className="text-center space-y-2">
            <div className="w-16 h-16 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Play size={32} />
            </div>
            <h2 className="text-xl font-bold text-gray-800">Nova Atividade</h2>
            <p className="text-gray-500">O que você vai realizar agora?</p>
          </div>
          
          <div className="space-y-4">
            <input 
              type="text"
              placeholder="Ex: Reunião com Cliente, Vistoria Técnica..."
              className="w-full px-6 py-4 bg-gray-50 border border-gray-200 rounded-2xl outline-none focus:ring-2 focus:ring-blue-500 font-medium"
              value={newActivityDesc}
              onChange={(e) => setNewActivityDesc(e.target.value)}
            />
            <button 
              onClick={handleCreateAndStart}
              disabled={!newActivityDesc}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold py-5 rounded-2xl shadow-xl shadow-blue-200 transition-all active:scale-[0.98] text-lg flex items-center justify-center gap-2"
            >
              <Play size={20} fill="currentColor" /> Iniciar Agora
            </button>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-3xl shadow-2xl border border-gray-100 overflow-hidden">
          <div className={`p-8 text-white text-center space-y-4 transition-colors duration-500 ${activeActivity.status === 'pausada' ? 'bg-orange-500' : 'bg-blue-600'}`}>
            <p className="text-xs font-bold uppercase tracking-widest opacity-80">
              {activeActivity.status === 'pausada' ? 'Atividade Pausada' : 'Atividade em Curso'}
            </p>
            <h2 className="text-2xl font-black">{activeActivity.descricao}</h2>
            <div className="text-6xl font-black tracking-tighter tabular-nums py-4">
              {activeActivity.status === 'pausada' ? '--:--:--' : formatTime(seconds)}
            </div>
            <div className="flex items-center justify-center gap-2 text-sm font-medium opacity-90">
              <Clock size={16} /> 
              Iniciado às {format(new Date(activeActivity.inicio), 'HH:mm')}
            </div>
          </div>

          <div className="p-8 grid grid-cols-2 gap-4">
            {activeActivity.status === 'ativa' ? (
              <button 
                onClick={() => setShowPauseModal(true)}
                className="col-span-1 bg-orange-500 hover:bg-orange-600 text-white font-bold py-4 rounded-2xl shadow-lg shadow-orange-100 flex flex-col items-center gap-2 transition-all active:scale-[0.95]"
              >
                <Pause size={24} fill="currentColor" />
                <span className="text-sm">Pausar</span>
              </button>
            ) : (
              <button 
                onClick={handleResume}
                className="col-span-1 bg-emerald-500 hover:bg-emerald-600 text-white font-bold py-4 rounded-2xl shadow-lg shadow-emerald-100 flex flex-col items-center gap-2 transition-all active:scale-[0.95]"
              >
                <Play size={24} fill="currentColor" />
                <span className="text-sm">Retomar</span>
              </button>
            )}

            <button 
              onClick={handleFinish}
              className="col-span-1 bg-gray-800 hover:bg-gray-900 text-white font-bold py-4 rounded-2xl shadow-lg shadow-gray-200 flex flex-col items-center gap-2 transition-all active:scale-[0.95]"
            >
              <Square size={24} fill="currentColor" />
              <span className="text-sm">Finalizar</span>
            </button>
          </div>

          {activeActivity.pausas?.length > 0 && (
            <div className="px-8 pb-8 space-y-3">
              <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Histórico de Pausas</p>
              <div className="space-y-2">
                {activeActivity.pausas.map((p, idx) => (
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
                  onClick={() => { setPauseReason(reason); handlePause(); }}
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
