import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { tripService } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { Navigation, ArrowLeft, Clock, AlertCircle, Car, Users } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

const toDateTimeLocalValue = (d) => format(d, "yyyy-MM-dd'T'HH:mm");

const RegistroSaida = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { appConfig } = useAuth();
  const [trip, setTrip] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [kmSaida, setKmSaida] = useState('');
  const [useManualDepartureDatetime, setUseManualDepartureDatetime] = useState(false);
  const [manualDepartureDatetime, setManualDepartureDatetime] = useState('');

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
      const user = JSON.parse(localStorage.getItem('user') || 'null');
      const motoristaId = user?.id;
      const requiresKm = ['carro empresa', 'carro próprio'].includes(trip.meio_transporte) 
        && trip.transporte?.motorista_id === motoristaId;

      if (requiresKm && !kmSaida) {
        alert('KM de saída é obrigatório para o motorista.');
        return;
      }

      const allowManualDepartureDatetime = !!appConfig?.trip_allow_manual_departure_datetime;
      let dataHoraSaidaISO = undefined;
      if (allowManualDepartureDatetime && useManualDepartureDatetime) {
        const raw = String(manualDepartureDatetime || '').trim();
        const dt = raw ? new Date(raw) : null;
        if (!dt || Number.isNaN(dt.getTime())) {
          alert('Data/hora de saída inválida.');
          return;
        }
        dataHoraSaidaISO = dt.toISOString();
      }

      await tripService.registerDeparture(id, { 
        km_saida: requiresKm ? kmSaida : undefined, 
        motorista_id: motoristaId,
        data_hora_real_saida: dataHoraSaidaISO,
      });
      navigate(`/viagens/${id}`);
    } catch (err) {
      console.error(err);
      alert('Erro ao registrar saída');
    }
  };

  if (loading) return <div className="p-8 text-center animate-pulse">Carregando...</div>;
  if (!trip) return <div className="p-8 text-center">Viagem não encontrada.</div>;

  const user = JSON.parse(localStorage.getItem('user') || 'null');
  const isMotorista = user?.id && trip?.transporte?.motorista_id === user.id;
  const showKmField = ['carro empresa', 'carro próprio'].includes(trip.meio_transporte) && isMotorista;
  const allowManualDepartureDatetime = !!appConfig?.trip_allow_manual_departure_datetime;

  return (
    <div className="max-w-md mx-auto space-y-8 animate-fade-in py-12">
      <div className="flex items-center gap-4">
        <button onClick={() => navigate(`/viagens/${id}`)} className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-500">
          <ArrowLeft size={24} />
        </button>
        <h1 className="text-2xl font-bold text-gray-800">Check-in de Saída</h1>
      </div>

      <div className="bg-white rounded-3xl shadow-xl shadow-blue-100 border border-gray-100 overflow-hidden flex flex-col">
        <div className="bg-blue-600 p-8 text-white text-center space-y-2">
          <Navigation className="mx-auto mb-2 opacity-80" size={48} />
          <p className="text-4xl font-black tracking-tight">{format(currentTime, 'HH:mm:ss')}</p>
          <p className="text-blue-100 font-medium">{format(currentTime, "EEEE, dd 'de' MMMM", { locale: ptBR })}</p>
        </div>

          <div className="p-8 space-y-6">
          <div className="space-y-4">
            <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-2xl">
              <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center text-blue-600 font-bold">
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
          </div>

            {allowManualDepartureDatetime ? (
              <div className="p-4 bg-gray-50 rounded-2xl border border-gray-100 space-y-3">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-sm font-black text-gray-800">Definir data/hora de saída</p>
                    <p className="text-xs font-bold text-gray-500">Se desativado, o sistema registra automaticamente.</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={useManualDepartureDatetime}
                    onChange={(e) => {
                      const next = e.target.checked;
                      setUseManualDepartureDatetime(next);
                      if (next) {
                        setManualDepartureDatetime((prev) => (String(prev || '').trim() ? prev : toDateTimeLocalValue(new Date())));
                      }
                    }}
                    className="rounded text-blue-600 focus:ring-blue-500 w-5 h-5"
                  />
                </div>
                {useManualDepartureDatetime ? (
                  <input
                    type="datetime-local"
                    value={manualDepartureDatetime}
                    onChange={(e) => setManualDepartureDatetime(e.target.value)}
                    className="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500 font-bold"
                  />
                ) : null}
              </div>
            ) : null}

            {showKmField && (
              <div className="p-4 bg-white rounded-2xl border border-gray-100 space-y-2">
                <label className="flex items-center gap-2 text-xs font-bold text-gray-600 uppercase tracking-widest">
                  <Car size={14} /> KM de Saída (Obrigatório para o motorista)
                </label>
                <input 
                  type="number"
                  value={kmSaida}
                  onChange={(e) => setKmSaida(e.target.value)}
                  placeholder="Ex: 15230"
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500 font-bold"
                />
              </div>
            )}

          <div className="p-4 bg-orange-50 rounded-2xl border border-orange-100 flex gap-3">
            <AlertCircle className="text-orange-500 shrink-0" size={20} />
            <p className="text-xs text-orange-700 font-medium leading-relaxed">
              Ao confirmar, o status da viagem será alterado para <span className="font-bold">Em Andamento</span> e a saída real será registrada.
            </p>
          </div>

          <button 
            onClick={handleConfirm}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-5 rounded-2xl shadow-xl shadow-blue-200 transition-all active:scale-[0.98] text-lg"
          >
            Confirmar Saída
          </button>
        </div>
      </div>
    </div>
  );
};

export default RegistroSaida;
