import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { configService } from '../services/api';
import { Save, Settings } from 'lucide-react';

const STATUS_OPTIONS = [
  { value: 'planejada', label: 'Planejada' },
  { value: 'em_andamento', label: 'Em Andamento' },
  { value: 'finalizada', label: 'Finalizada' },
  { value: 'cancelada', label: 'Cancelada' },
];

const Configuracoes = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [expensePhotoRequired, setExpensePhotoRequired] = useState(false);
  const [blockedStatuses, setBlockedStatuses] = useState(['em_andamento', 'finalizada', 'cancelada']);

  const isAdmin = user?.tipousuario === 'admin';

  const blockedSet = useMemo(() => new Set(blockedStatuses), [blockedStatuses]);

  const fetchConfig = useCallback(async () => {
    setLoading(true);
    try {
      const res = await configService.get();
      const data = res.data;
      setExpensePhotoRequired(!!data.expense_photo_required);
      setBlockedStatuses(Array.isArray(data.trip_edit_blocked_statuses) ? data.trip_edit_blocked_statuses : []);
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

  const handleSave = async () => {
    setSaving(true);
    try {
      await configService.update({
        expense_photo_required: expensePhotoRequired,
        trip_edit_blocked_statuses: blockedStatuses,
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
        </div>
      )}
    </div>
  );
};

export default Configuracoes;
