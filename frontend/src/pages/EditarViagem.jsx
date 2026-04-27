import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { tripService, userService, vehicleService, configService } from '../services/api';
import { ArrowLeft, Car, Plus, Save, Users, X } from 'lucide-react';

const toDateTimeLocalValue = (value) => {
  if (!value) return '';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return '';
  const offsetMinutes = d.getTimezoneOffset();
  const local = new Date(d.getTime() - offsetMinutes * 60 * 1000);
  return local.toISOString().slice(0, 16);
};

const EditarViagem = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [trip, setTrip] = useState(null);
  const [availableUsers, setAvailableUsers] = useState([]);
  const [availableVehicles, setAvailableVehicles] = useState([]);
  const [blockedStatuses, setBlockedStatuses] = useState(['em_andamento', 'finalizada', 'cancelada']);

  const [formData, setFormData] = useState({
    motivo: '',
    clientes: [''],
    data_hora_prevista_saida: '',
    data_hora_prevista_retorno: '',
    meio_transporte: 'carona',
    participantes_ids: [],
    transporte: {
      veiculo_id: '',
      motorista_id: '',
      km_saida: '',
    },
  });

  const requiresTransport = useMemo(
    () => ['carro empresa', 'carro próprio'].includes(formData.meio_transporte),
    [formData.meio_transporte],
  );

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      try {
        const [tripRes, usersRes, vehiclesRes, cfgRes] = await Promise.all([
          tripService.get(id),
          userService.list(),
          vehicleService.list(),
          configService.get().catch(() => ({ data: null })),
        ]);

        const t = tripRes.data;
        setTrip(t);
        setAvailableUsers(usersRes.data);
        setAvailableVehicles(vehiclesRes.data);

        const cfg = cfgRes?.data;
        if (cfg?.trip_edit_blocked_statuses && Array.isArray(cfg.trip_edit_blocked_statuses)) {
          setBlockedStatuses(cfg.trip_edit_blocked_statuses);
        }

        setFormData({
          motivo: t.motivo || '',
          clientes: t.clientes?.length ? t.clientes : [''],
          data_hora_prevista_saida: toDateTimeLocalValue(t.data_hora_prevista_saida),
          data_hora_prevista_retorno: toDateTimeLocalValue(t.data_hora_prevista_retorno),
          meio_transporte: t.meio_transporte || 'carona',
          participantes_ids: (t.participantes || []).map((p) => p.id),
          transporte: {
            veiculo_id: t.transporte?.veiculo_id ? String(t.transporte.veiculo_id) : '',
            motorista_id: t.transporte?.motorista_id ? String(t.transporte.motorista_id) : '',
            km_saida: t.transporte?.km_saida != null ? String(t.transporte.km_saida) : '',
          },
        });
      } catch (err) {
        console.error(err);
        alert(err?.response?.data?.detail || 'Erro ao carregar viagem');
        navigate(`/viagens/${id}`);
      } finally {
        setLoading(false);
      }
    };

    fetchAll();
  }, [id, navigate]);

  const handleToggleParticipant = (userId) => {
    setFormData((prev) => {
      const current = new Set(prev.participantes_ids);
      if (current.has(userId)) current.delete(userId);
      else current.add(userId);
      return { ...prev, participantes_ids: Array.from(current) };
    });
  };

  const addCliente = () => {
    setFormData((prev) => ({ ...prev, clientes: [...(prev.clientes || []), ''] }));
  };

  const updateCliente = (index, value) => {
    setFormData((prev) => ({
      ...prev,
      clientes: (prev.clientes || []).map((c, i) => (i === index ? value : c)),
    }));
  };

  const removeCliente = (index) => {
    setFormData((prev) => {
      const next = (prev.clientes || []).filter((_, i) => i !== index);
      return { ...prev, clientes: next.length ? next : [''] };
    });
  };

  const handleSave = async (e) => {
    e.preventDefault();
    if (!trip) return;

    if (blockedStatuses.includes(trip.status)) {
      alert('Edição não permitida para este status de viagem');
      return;
    }

    if (!formData.participantes_ids.length) {
      alert('Selecione ao menos um participante.');
      return;
    }

    const clientes = (formData.clientes || []).map((c) => String(c).trim()).filter(Boolean);
    if (!clientes.length) {
      alert('Informe pelo menos um cliente.');
      return;
    }

    const payload = {
      motivo: formData.motivo,
      clientes,
      data_hora_prevista_saida: formData.data_hora_prevista_saida,
      data_hora_prevista_retorno: formData.data_hora_prevista_retorno,
      meio_transporte: formData.meio_transporte,
      participantes_ids: formData.participantes_ids,
      transporte: { ...formData.transporte },
    };

    if (!requiresTransport) {
      delete payload.transporte;
    } else {
      if (payload.transporte.km_saida === '') delete payload.transporte.km_saida;
    }

    setSaving(true);
    try {
      await tripService.update(id, payload);
      navigate(`/viagens/${id}`);
    } catch (err) {
      console.error(err);
      alert(err?.response?.data?.detail || 'Erro ao salvar viagem');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-8 text-center text-gray-500 font-medium">
        Carregando...
      </div>
    );
  }

  if (!trip) return null;

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fade-in">
      <header className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => navigate(`/viagens/${id}`)}
            className="p-3 rounded-xl bg-white border border-gray-200 hover:bg-gray-50"
          >
            <ArrowLeft size={18} />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Editar Viagem</h1>
            <p className="text-gray-500 font-medium">#{trip.id} • {trip.status}</p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => {}}
          className="hidden"
        />
      </header>

      <form onSubmit={handleSave} className="space-y-6">
        <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-1">Motivo</label>
              <input
                type="text"
                required
                className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-blue-500"
                value={formData.motivo}
                onChange={(e) => setFormData({ ...formData, motivo: e.target.value })}
              />
            </div>
            <div className="md:col-span-2">
              <div className="flex items-center justify-between gap-3 mb-2">
                <label className="block text-sm font-bold text-gray-700">Clientes a Visitar</label>
                <button
                  type="button"
                  onClick={addCliente}
                  className="px-3 py-1.5 bg-blue-50 text-blue-700 border border-blue-100 rounded-lg font-bold text-sm flex items-center gap-2 hover:bg-blue-100 transition-colors"
                >
                  <Plus size={16} /> Adicionar
                </button>
              </div>
              <div className="space-y-2">
                {(formData.clientes || []).map((cliente, idx) => (
                  <div key={idx} className="flex gap-2">
                    <input
                      type="text"
                      required={idx === 0}
                      className="flex-1 px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder={`Cliente ${idx + 1}`}
                      value={cliente}
                      onChange={(e) => updateCliente(idx, e.target.value)}
                    />
                    <button
                      type="button"
                      onClick={() => removeCliente(idx)}
                      className="px-3 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 text-gray-600"
                      aria-label={`Remover cliente ${idx + 1}`}
                    >
                      <X size={16} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-1">Saída Prevista</label>
              <input
                type="datetime-local"
                required
                className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-blue-500"
                value={formData.data_hora_prevista_saida}
                onChange={(e) => setFormData({ ...formData, data_hora_prevista_saida: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-1">Retorno Previsto</label>
              <input
                type="datetime-local"
                required
                className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-blue-500"
                value={formData.data_hora_prevista_retorno}
                onChange={(e) => setFormData({ ...formData, data_hora_prevista_retorno: e.target.value })}
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-bold text-gray-700 mb-1">Meio de Transporte</label>
              <select
                className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-blue-500"
                value={formData.meio_transporte}
                onChange={(e) => setFormData({ ...formData, meio_transporte: e.target.value })}
              >
                <option value="carona">Carona</option>
                <option value="terceiros">Terceiros</option>
                <option value="carro empresa">Carro Empresa</option>
                <option value="carro próprio">Carro Próprio</option>
              </select>
            </div>
          </div>

          {requiresTransport && (
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
                    onChange={(e) =>
                      setFormData({ ...formData, transporte: { ...formData.transporte, veiculo_id: e.target.value } })
                    }
                  >
                    <option value="">Selecione...</option>
                    {availableVehicles.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.placa} - {v.modelo}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-blue-600 mb-1 uppercase tracking-wider">Motorista</label>
                  <select
                    required
                    className="w-full px-3 py-2 bg-white border border-blue-200 rounded-lg outline-none focus:ring-2 focus:ring-blue-500"
                    value={formData.transporte.motorista_id}
                    onChange={(e) =>
                      setFormData({ ...formData, transporte: { ...formData.transporte, motorista_id: e.target.value } })
                    }
                  >
                    <option value="">Selecione...</option>
                    {availableUsers
                      .filter((u) => u.tem_cnh)
                      .map((u) => (
                        <option key={u.id} value={u.id}>
                          {u.nome}
                        </option>
                      ))}
                  </select>
                </div>
              </div>
            </div>
          )}

          <div className="bg-gray-50 p-6 rounded-2xl border border-gray-100 space-y-4">
            <h3 className="font-bold text-gray-700 flex items-center gap-2">
              <Users size={18} /> Participantes
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {availableUsers.map((u) => (
                <label
                  key={u.id}
                  className="flex items-center gap-3 p-3 bg-white rounded-xl cursor-pointer border border-gray-200"
                >
                  <input
                    type="checkbox"
                    checked={formData.participantes_ids.includes(u.id)}
                    onChange={() => handleToggleParticipant(u.id)}
                    className="rounded text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm font-bold text-gray-700 truncate">{u.nome}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-6 py-3 rounded-xl font-bold shadow-lg shadow-blue-200 flex items-center gap-2"
          >
            <Save size={18} /> {saving ? 'Salvando...' : 'Salvar Alterações'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default EditarViagem;
