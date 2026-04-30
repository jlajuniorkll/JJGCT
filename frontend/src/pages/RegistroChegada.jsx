import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { tripService } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { ArrowLeft, Clock, CheckCircle, AlertCircle, Car, Users } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

const toDateTimeLocalValue = (d) => format(d, "yyyy-MM-dd'T'HH:mm");

const RegistroChegada = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { appConfig } = useAuth();
  const allowManualArrivalDatetime = !!appConfig?.trip_allow_manual_arrival_datetime;
  const [trip, setTrip] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [kmChegada, setKmChegada] = useState('');
  const [useManualArrivalDatetime, setUseManualArrivalDatetime] = useState(false);
  const [manualArrivalDatetime, setManualArrivalDatetime] = useState('');

  useEffect(() => {
    const fetchTrip = async () => {
      try {
        const response = await tripService.get(id);
        setTrip(response.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchTrip();

    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, [id]);

  const handleConfirm = async () => {
    try {
      if (['carro empresa', 'carro próprio'].includes(trip.meio_transporte) && !kmChegada) {
        alert('KM de chegada é obrigatório.');
        return;
      }
      const km = requiresKm ? kmChegada : undefined;

      let dataHoraChegadaISO = undefined;
      if (allowManualArrivalDatetime && useManualArrivalDatetime) {
        const raw = String(manualArrivalDatetime || '').trim();
        const dt = raw ? new Date(raw) : null;
        if (!dt || Number.isNaN(dt.getTime())) {
          alert('Data/hora de chegada inválida.');
          return;
        }
        dataHoraChegadaISO = dt.toISOString();
      }

      await tripService.registerArrival(id, { km_chegada: km, data_hora_real_chegada: dataHoraChegadaISO });
      navigate(`/viagens/${id}`);
    } catch (err) {
      alert(err.response?.data?.detail || 'Erro ao registrar retorno');
    }
  };

  if (loading) return <div className="p-8 text-center animate-pulse">Carregando...</div>;
  if (!trip) return <div className="p-8 text-center">Viagem não encontrada.</div>;

  const requiresKm = ['carro empresa', 'carro próprio'].includes(trip.meio_transporte);

  return (
    <div className="max-w-md mx-auto space-y-8 animate-fade-in py-12">
      <div className="flex items-center gap-4">
        <button onClick={() => navigate(`/viagens/${id}`)} className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-500">
          <ArrowLeft size={24} />
        </button>
        <h1 className="text-2xl font-bold text-gray-800">Check-in de Retorno</h1>
      </div>

      <div className="bg-white rounded-3xl shadow-xl shadow-emerald-100 border border-gray-100 overflow-hidden flex flex-col">
        <div className="bg-emerald-600 p-8 text-white text-center space-y-2">
          <CheckCircle className="mx-auto mb-2 opacity-80" size={48} />
          <p className="text-4xl font-black tracking-tight">{format(currentTime, 'HH:mm:ss')}</p>
          <p className="text-emerald-100 font-medium">{format(currentTime, "EEEE, dd 'de' MMMM", { locale: ptBR })}</p>
        </div>

        <div className="p-8 space-y-6">
          <div className="space-y-4">
            <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-2xl">
              <div className="w-10 h-10 rounded-xl bg-emerald-100 flex items-center justify-center text-emerald-600 font-bold">
                <Users size={20} />
              </div>
              <div>
                <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Clientes</p>
                <p className="text-sm font-bold text-gray-800 truncate">{(trip.clientes || []).join(', ') || '--'}</p>
              </div>
            </div>

            <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-2xl">
              <div className="w-10 h-10 rounded-xl bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold">
                <Clock size={20} />
              </div>
              <div>
                <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Retorno Previsto</p>
                <p className="text-sm font-bold text-gray-800 truncate">
                  {trip.data_hora_prevista_retorno ? format(new Date(trip.data_hora_prevista_retorno), "dd/MM/yyyy HH:mm") : '--'}
                </p>
              </div>
            </div>

            {allowManualArrivalDatetime ? (
              <div className="p-4 bg-gray-50 rounded-2xl border border-gray-100 space-y-3">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-sm font-black text-gray-800">Definir data/hora de chegada</p>
                    <p className="text-xs font-bold text-gray-500">Se desativado, o sistema registra automaticamente.</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={useManualArrivalDatetime}
                    onChange={(e) => {
                      const next = e.target.checked;
                      setUseManualArrivalDatetime(next);
                      if (next) {
                        setManualArrivalDatetime((prev) => (String(prev || '').trim() ? prev : toDateTimeLocalValue(new Date())));
                      }
                    }}
                    className="rounded text-blue-600 focus:ring-blue-500 w-5 h-5"
                  />
                </div>
                {useManualArrivalDatetime ? (
                  <input
                    type="datetime-local"
                    value={manualArrivalDatetime}
                    onChange={(e) => setManualArrivalDatetime(e.target.value)}
                    className="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500 font-bold"
                  />
                ) : null}
              </div>
            ) : null}

            {requiresKm && (
              <div className="p-4 bg-emerald-50 rounded-2xl border border-emerald-100 space-y-3">
                <label className="flex items-center gap-2 text-xs font-bold text-emerald-700 uppercase tracking-widest">
                  <Car size={14} /> KM de Chegada (Obrigatório)
                </label>
                <input 
                  type="number" 
                  value={kmChegada}
                  onChange={(e) => setKmChegada(e.target.value)}
                  placeholder="Ex: 15420"
                  className="w-full px-4 py-3 bg-white border border-emerald-200 rounded-xl outline-none focus:ring-2 focus:ring-emerald-500 font-bold text-lg"
                />
                <p className="text-[10px] text-emerald-600 font-medium">KM inicial registrado: <span className="font-bold">{trip.transporte?.km_saida}</span></p>
              </div>
            )}
          </div>

          <div className="p-4 bg-blue-50 rounded-2xl border border-blue-100 flex gap-3">
            <AlertCircle className="text-blue-500 shrink-0" size={20} />
            <p className="text-xs text-blue-700 font-medium leading-relaxed">
              Ao confirmar, a viagem será marcada como <span className="font-bold">Finalizada</span>. Certifique-se de que todas as atividades foram concluídas.
            </p>
          </div>

          <button 
            onClick={handleConfirm}
            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-5 rounded-2xl shadow-xl shadow-emerald-200 transition-all active:scale-[0.98] text-lg"
          >
            Finalizar Viagem
          </button>
        </div>
      </div>
    </div>
  );
};

export default RegistroChegada;
