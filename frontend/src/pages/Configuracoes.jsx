import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { configService } from '../services/api';
import { Plus, Save, Settings, X } from 'lucide-react';

const STATUS_OPTIONS = [
  { value: 'planejada', label: 'Planejada' },
  { value: 'em_andamento', label: 'Em Andamento' },
  { value: 'finalizada', label: 'Finalizada' },
  { value: 'cancelada', label: 'Cancelada' },
];

const ACTIVITY_STATUS_OPTIONS = [
  { value: 'pendente', label: 'Pendente' },
  { value: 'ativa', label: 'Ativa' },
  { value: 'pausada', label: 'Pausada' },
  { value: 'finalizada', label: 'Finalizada' },
];

const Configuracoes = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [expensePhotoRequired, setExpensePhotoRequired] = useState(false);
  const [expenseDescriptionOptions, setExpenseDescriptionOptions] = useState([
    'Almoço',
    'Janta',
    'Lanche',
    'Hospedagem',
    'Taxi/Uber',
    'Estacionamento',
    'Pedágio',
    'Combustível',
    'Locação',
  ]);
  const [newExpenseDescriptionOption, setNewExpenseDescriptionOption] = useState('');
  const [activityEditDeleteAllowedStatuses, setActivityEditDeleteAllowedStatuses] = useState(['pendente']);
  const [blockedStatuses, setBlockedStatuses] = useState(['em_andamento', 'finalizada', 'cancelada']);
  const [activityExpenseAllowedStatuses, setActivityExpenseAllowedStatuses] = useState(['em_andamento']);
  const [tripsShowAllAdmin, setTripsShowAllAdmin] = useState(true);
  const [tripsShowAllColaborador, setTripsShowAllColaborador] = useState(true);

  const isAdmin = user?.tipousuario === 'admin';

  const blockedSet = useMemo(() => new Set(blockedStatuses), [blockedStatuses]);
  const activityExpenseAllowedSet = useMemo(
    () => new Set(activityExpenseAllowedStatuses),
    [activityExpenseAllowedStatuses],
  );

  const fetchConfig = useCallback(async () => {
    setLoading(true);
    try {
      const res = await configService.get();
      const data = res.data;
      setExpensePhotoRequired(!!data.expense_photo_required);
      setExpenseDescriptionOptions(
        Array.isArray(data.expense_description_options) && data.expense_description_options.length
          ? data.expense_description_options
          : [
              'Almoço',
              'Janta',
              'Lanche',
              'Hospedagem',
              'Taxi/Uber',
              'Estacionamento',
              'Pedágio',
              'Combustível',
              'Locação',
            ],
      );
      setActivityEditDeleteAllowedStatuses(
        Array.isArray(data.activity_edit_delete_allowed_statuses) && data.activity_edit_delete_allowed_statuses.length
          ? data.activity_edit_delete_allowed_statuses
          : ['pendente'],
      );
      setBlockedStatuses(Array.isArray(data.trip_edit_blocked_statuses) ? data.trip_edit_blocked_statuses : []);
      setActivityExpenseAllowedStatuses(
        Array.isArray(data.trip_activity_expense_allowed_statuses) ? data.trip_activity_expense_allowed_statuses : ['em_andamento'],
      );
      setTripsShowAllAdmin(data.trips_show_all_admin !== false);
      setTripsShowAllColaborador(data.trips_show_all_colaborador !== false);
    } catch (err) {
      console.error(err);
      alert(err?.response?.data?.detail || 'Erro ao carregar configurações');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isAdmin) {
      navigate('/');
      return;
    }
    fetchConfig();
  }, [fetchConfig, isAdmin, navigate]);

  const toggleStatus = (value) => {
    setBlockedStatuses((prev) => {
      const next = new Set(prev);
      if (next.has(value)) next.delete(value);
      else next.add(value);
      return Array.from(next);
    });
  };

  const toggleActivityExpenseStatus = (value) => {
    setActivityExpenseAllowedStatuses((prev) => {
      const next = new Set(prev);
      if (next.has(value)) next.delete(value);
      else next.add(value);
      return Array.from(next);
    });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await configService.update({
        expense_photo_required: expensePhotoRequired,
        expense_description_options: expenseDescriptionOptions,
        activity_edit_delete_allowed_statuses: activityEditDeleteAllowedStatuses,
        trip_edit_blocked_statuses: blockedStatuses,
        trip_activity_expense_allowed_statuses: activityExpenseAllowedStatuses,
        trips_show_all_admin: tripsShowAllAdmin,
        trips_show_all_colaborador: tripsShowAllColaborador,
      });
      alert('Configurações salvas');
    } catch (err) {
      console.error(err);
      alert(err?.response?.data?.detail || 'Erro ao salvar configurações');
    } finally {
      setSaving(false);
    }
  };

  if (!isAdmin) return null;

  return (
    <div className="space-y-6 animate-fade-in">
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <Settings className="text-blue-600" size={22} /> Configurações
          </h1>
          <p className="text-gray-500 font-medium">Regras administrativas do sistema.</p>
        </div>
        <button
          onClick={handleSave}
          disabled={saving || loading}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-6 py-3 rounded-xl font-bold shadow-lg shadow-blue-200 flex items-center gap-2"
        >
          <Save size={18} /> Salvar
        </button>
      </header>

      {loading ? (
        <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-8 text-center text-gray-500 font-medium">
          Carregando...
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6 space-y-4">
            <h2 className="text-sm font-black text-gray-400 uppercase tracking-widest">Despesas</h2>
            <label className="flex items-center justify-between gap-4 p-4 bg-gray-50 rounded-2xl border border-gray-100 cursor-pointer">
              <div>
                <p className="text-sm font-black text-gray-800">Foto/Comprovante obrigatório</p>
                <p className="text-xs font-bold text-gray-500">Exige anexo ao lançar uma despesa.</p>
              </div>
              <input
                type="checkbox"
                checked={expensePhotoRequired}
                onChange={(e) => setExpensePhotoRequired(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500 w-5 h-5"
              />
            </label>
            <div className="space-y-3">
              <div>
                <p className="text-sm font-black text-gray-800">Opções de descrição</p>
                <p className="text-xs font-bold text-gray-500">Sugestões exibidas ao registrar uma despesa.</p>
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  className="flex-1 px-4 py-3 bg-gray-50 border border-gray-200 rounded-2xl outline-none focus:ring-2 focus:ring-blue-500 font-medium"
                  placeholder="Ex: Almoço, Estacionamento..."
                  value={newExpenseDescriptionOption}
                  onChange={(e) => setNewExpenseDescriptionOption(e.target.value)}
                />
                <button
                  type="button"
                  onClick={() => {
                    const next = String(newExpenseDescriptionOption || '').trim();
                    if (!next) return;
                    setExpenseDescriptionOptions((prev) => {
                      const exists = prev.some((p) => String(p).toLowerCase() === next.toLowerCase());
                      return exists ? prev : [...prev, next];
                    });
                    setNewExpenseDescriptionOption('');
                  }}
                  className="px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-2xl font-bold flex items-center gap-2"
                >
                  <Plus size={18} /> Adicionar
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {expenseDescriptionOptions.map((opt) => (
                  <button
                    type="button"
                    key={opt}
                    onClick={() => setExpenseDescriptionOptions((prev) => prev.filter((p) => p !== opt))}
                    className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-2xl text-sm font-bold text-gray-700 flex items-center gap-2 hover:bg-gray-100"
                    aria-label={`Remover ${opt}`}
                  >
                    {opt} <X size={16} className="text-gray-400" />
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6 space-y-4">
            <h2 className="text-sm font-black text-gray-400 uppercase tracking-widest">Edição de Viagem</h2>
            <p className="text-sm font-medium text-gray-600">
              Selecione os status em que o usuário não poderá editar a viagem após criar.
            </p>
            <div className="grid grid-cols-2 gap-3">
              {STATUS_OPTIONS.map((opt) => (
                <label
                  key={opt.value}
                  className="flex items-center gap-3 p-4 bg-gray-50 rounded-2xl border border-gray-100 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={blockedSet.has(opt.value)}
                    onChange={() => toggleStatus(opt.value)}
                    className="rounded text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm font-black text-gray-800">{opt.label}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6 space-y-4">
            <h2 className="text-sm font-black text-gray-400 uppercase tracking-widest">Atividades e Despesas</h2>
            <p className="text-sm font-medium text-gray-600">
              Selecione os status em que o sistema deve liberar adicionar/editar/excluir atividades e despesas.
            </p>
            <div className="grid grid-cols-2 gap-3">
              {STATUS_OPTIONS.map((opt) => (
                <label
                  key={opt.value}
                  className="flex items-center gap-3 p-4 bg-gray-50 rounded-2xl border border-gray-100 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={activityExpenseAllowedSet.has(opt.value)}
                    onChange={() => toggleActivityExpenseStatus(opt.value)}
                    className="rounded text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm font-black text-gray-800">{opt.label}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6 space-y-4">
            <h2 className="text-sm font-black text-gray-400 uppercase tracking-widest">Edição/Exclusão de Atividades</h2>
            <p className="text-sm font-medium text-gray-600">
              Selecione os status da atividade em que o sistema deve liberar editar/excluir.
            </p>
            <div className="grid grid-cols-2 gap-3">
              {ACTIVITY_STATUS_OPTIONS.map((opt) => (
                <label
                  key={opt.value}
                  className="flex items-center gap-3 p-4 bg-gray-50 rounded-2xl border border-gray-100 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={activityEditDeleteAllowedStatuses.includes(opt.value)}
                    onChange={() => {
                      setActivityEditDeleteAllowedStatuses((prev) => {
                        const next = new Set(prev);
                        if (next.has(opt.value)) next.delete(opt.value);
                        else next.add(opt.value);
                        return Array.from(next);
                      });
                    }}
                    className="rounded text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm font-black text-gray-800">{opt.label}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6 space-y-4">
            <h2 className="text-sm font-black text-gray-400 uppercase tracking-widest">Visibilidade de Viagens</h2>
            <label className="flex items-center justify-between gap-4 p-4 bg-gray-50 rounded-2xl border border-gray-100 cursor-pointer">
              <div>
                <p className="text-sm font-black text-gray-800">Todas as viagens (administrador)</p>
                <p className="text-xs font-bold text-gray-500">
                  Se desativado, admin vê apenas viagens em que é participante, motorista ou responsável.
                </p>
              </div>
              <input
                type="checkbox"
                checked={tripsShowAllAdmin}
                onChange={(e) => setTripsShowAllAdmin(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500 w-5 h-5"
              />
            </label>
            <label className="flex items-center justify-between gap-4 p-4 bg-gray-50 rounded-2xl border border-gray-100 cursor-pointer">
              <div>
                <p className="text-sm font-black text-gray-800">Todas as viagens (colaborador)</p>
                <p className="text-xs font-bold text-gray-500">
                  Se desativado, colaborador vê apenas viagens em que é participante, motorista ou responsável.
                </p>
              </div>
              <input
                type="checkbox"
                checked={tripsShowAllColaborador}
                onChange={(e) => setTripsShowAllColaborador(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500 w-5 h-5"
              />
            </label>
          </div>
        </div>
      )}
    </div>
  );
};

export default Configuracoes;
