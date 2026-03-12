import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { tripService } from '../services/api';
import { Navigation, ArrowLeft, Clock, MapPin, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

const RegistroSaida = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [trip, setTrip] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentTime, setCurrentTime] = useState(new Date());

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
      await tripService.registerDeparture(id);
      navigate(`/viagens/${id}`);
    } catch (err) {
      console.error(err);
      alert('Erro ao registrar saída');
    }
  };

  if (loading) return <div className="p-8 text-center animate-pulse">Carregando...</div>;
  if (!trip) return <div className="p-8 text-center">Viagem não encontrada.</div>;

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
                <MapPin size={20} />
              </div>
              <div>
                <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Partindo de</p>
                <p className="text-sm font-bold text-gray-800 truncate">{trip.local_partida}</p>
              </div>
            </div>

            <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-2xl">
              <div className="w-10 h-10 rounded-xl bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold">
                <Clock size={20} />
              </div>
              <div>
                <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Destino</p>
                <p className="text-sm font-bold text-gray-800 truncate">{trip.local_chegada}</p>
              </div>
            </div>
          </div>

          <div className="p-4 bg-orange-50 rounded-2xl border border-orange-100 flex gap-3">
            <AlertCircle className="text-orange-500 shrink-0" size={20} />
            <p className="text-xs text-orange-700 font-medium leading-relaxed">
              Ao confirmar, o status da viagem será alterado para <span className="font-bold">Em Andamento</span> e o horário atual será registrado como a saída real.
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
