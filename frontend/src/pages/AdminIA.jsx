import React, { useEffect, useMemo, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { iaService, userService } from '../services/api';
import { useAuth } from '../hooks/useAuth';

const toISOStart = (yyyyMmDd) => (yyyyMmDd ? `${yyyyMmDd}T00:00:00Z` : undefined);
const toISOEnd = (yyyyMmDd) => (yyyyMmDd ? `${yyyyMmDd}T23:59:59Z` : undefined);

const fmtUsd = (v) => {
  const n = Number(v || 0);
  return n.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
};

const fmtPct = (v) => `${Math.round((Number(v || 0) * 100) * 10) / 10}%`;

const AdminIA = () => {
  const { user } = useAuth();
  const [usuarios, setUsuarios] = useState([]);
  const [metricas, setMetricas] = useState(null);
  const [logs, setLogs] = useState([]);
  const [totalLogs, setTotalLogs] = useState(0);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState('');

  const hoje = new Date();
  const yyyy = hoje.getFullYear();
  const mm = String(hoje.getMonth() + 1).padStart(2, '0');
  const dd = String(hoje.getDate()).padStart(2, '0');
  const [periodoFim, setPeriodoFim] = useState(`${yyyy}-${mm}-${dd}`);
  const [periodoInicio, setPeriodoInicio] = useState(() => {
    const d = new Date(hoje);
    d.setDate(d.getDate() - 29);
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  });
  const [tipo, setTipo] = useState('');
  const [usuarioId, setUsuarioId] = useState('');

  useEffect(() => {
    if (user?.tipousuario !== 'admin') return;
    (async () => {
      try {
        const res = await userService.list();
        setUsuarios(Array.isArray(res.data) ? res.data : []);
      } catch {
        setUsuarios([]);
      }
    })();
  }, [user?.tipousuario]);

  useEffect(() => {
    if (user?.tipousuario !== 'admin') return;

    const paramsMetricas = {
      periodo_inicio: toISOStart(periodoInicio),
      periodo_fim: toISOEnd(periodoFim),
    };

    const paramsLogs = {
      periodo_inicio: toISOStart(periodoInicio),
      periodo_fim: toISOEnd(periodoFim),
      limit: 200,
      offset: 0,
    };
    if (tipo) paramsLogs.tipo = tipo;
    if (usuarioId) paramsLogs.usuario_id = Number(usuarioId);

    setLoading(true);
    setErro('');
    (async () => {
      try {
        const [mRes, lRes] = await Promise.all([iaService.getMetricasIA(paramsMetricas), iaService.getLogsIA(paramsLogs)]);
        setMetricas(mRes.data || null);
        const data = lRes.data || {};
        setLogs(Array.isArray(data.items) ? data.items : []);
        setTotalLogs(Number(data.total || 0));
      } catch (e) {
        const detail = e?.response?.data?.detail ? String(e.response.data.detail) : 'Não consegui carregar as métricas da IA.';
        setErro(detail);
        setMetricas(null);
        setLogs([]);
        setTotalLogs(0);
      } finally {
        setLoading(false);
      }
    })();
  }, [periodoInicio, periodoFim, tipo, usuarioId, user?.tipousuario]);

  const chartData = useMemo(() => {
    const byDay = new Map();
    for (const l of logs || []) {
      const dt = String(l?.criado_em || '');
      const day = dt ? dt.slice(0, 10) : '—';
      const prev = byDay.get(day) || { dia: day, chamadas: 0, custo_usd: 0 };
      prev.chamadas += 1;
      prev.custo_usd += Number(l?.custo_estimado_usd || 0);
      byDay.set(day, prev);
    }
    return Array.from(byDay.values()).sort((a, b) => String(a.dia).localeCompare(String(b.dia)));
  }, [logs]);

  const chamadasPorDia = useMemo(() => {
    if (!metricas?.total_chamadas) return 0;
    const ini = new Date(`${periodoInicio}T00:00:00`);
    const fim = new Date(`${periodoFim}T00:00:00`);
    const days = Math.max(1, Math.round((fim - ini) / (24 * 60 * 60 * 1000)) + 1);
    return metricas.total_chamadas / days;
  }, [metricas?.total_chamadas, periodoInicio, periodoFim]);

  if (user?.tipousuario !== 'admin') {
    return (
      <div className="space-y-2">
        <h1 className="text-2xl font-bold text-gray-800">IA</h1>
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100 text-gray-700 font-medium">
          Você não tem permissão para acessar esta página.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">IA</h1>
          <p className="text-gray-500 font-medium">Observabilidade, custo e adoção.</p>
        </div>
      </header>

      <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div>
            <label className="text-xs font-black uppercase tracking-wider text-gray-400">Período início</label>
            <input
              type="date"
              value={periodoInicio}
              onChange={(e) => setPeriodoInicio(e.target.value)}
              className="mt-1 w-full px-4 py-3 rounded-xl border border-gray-200 bg-gray-50 outline-none focus:ring-2 focus:ring-blue-500 font-medium"
            />
          </div>
          <div>
            <label className="text-xs font-black uppercase tracking-wider text-gray-400">Período fim</label>
            <input
              type="date"
              value={periodoFim}
              onChange={(e) => setPeriodoFim(e.target.value)}
              className="mt-1 w-full px-4 py-3 rounded-xl border border-gray-200 bg-gray-50 outline-none focus:ring-2 focus:ring-blue-500 font-medium"
            />
          </div>
          <div>
            <label className="text-xs font-black uppercase tracking-wider text-gray-400">Tipo</label>
            <select
              value={tipo}
              onChange={(e) => setTipo(e.target.value)}
              className="mt-1 w-full px-4 py-3 rounded-xl border border-gray-200 bg-gray-50 outline-none focus:ring-2 focus:ring-blue-500 font-medium"
            >
              <option value="">Todos</option>
              <option value="chat">Chat</option>
              <option value="extracao">Extração</option>
              <option value="relatorio">Relatório</option>
            </select>
          </div>
          <div>
            <label className="text-xs font-black uppercase tracking-wider text-gray-400">Usuário</label>
            <select
              value={usuarioId}
              onChange={(e) => setUsuarioId(e.target.value)}
              className="mt-1 w-full px-4 py-3 rounded-xl border border-gray-200 bg-gray-50 outline-none focus:ring-2 focus:ring-blue-500 font-medium"
            >
              <option value="">Todos</option>
              {usuarios.map((u) => (
                <option key={u.id} value={u.id}>{u.nome}</option>
              ))}
            </select>
          </div>
        </div>
        {erro ? <div className="mt-3 text-sm font-medium text-red-600">{erro}</div> : null}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100">
          <p className="text-xs font-black uppercase tracking-wider text-gray-400">Chamadas</p>
          <p className="text-2xl font-black text-gray-800 mt-1">{metricas?.total_chamadas ?? (loading ? '—' : 0)}</p>
          <p className="text-sm text-gray-500 font-medium mt-1">≈ {loading ? '—' : chamadasPorDia.toFixed(1)} / dia</p>
        </div>
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100">
          <p className="text-xs font-black uppercase tracking-wider text-gray-400">Custo</p>
          <p className="text-2xl font-black text-gray-800 mt-1">{loading ? '—' : fmtUsd(metricas?.custo_total_usd)}</p>
          <p className="text-sm text-gray-500 font-medium mt-1">no período</p>
        </div>
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100">
          <p className="text-xs font-black uppercase tracking-wider text-gray-400">Tokens</p>
          <p className="text-2xl font-black text-gray-800 mt-1">{metricas?.total_tokens ?? (loading ? '—' : 0)}</p>
          <p className="text-sm text-gray-500 font-medium mt-1">input+output+cache</p>
        </div>
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100">
          <p className="text-xs font-black uppercase tracking-wider text-gray-400">Taxa sucesso</p>
          <p className="text-2xl font-black text-gray-800 mt-1">{loading ? '—' : fmtPct(metricas?.taxa_sucesso)}</p>
          <p className="text-sm text-gray-500 font-medium mt-1">p50 {metricas?.latencia_p50 ?? '—'}ms · p95 {metricas?.latencia_p95 ?? '—'}ms</p>
        </div>
      </div>

      <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100">
        <div className="flex items-center justify-between gap-4 mb-3">
          <h2 className="text-lg font-bold text-gray-800">Uso ao longo do tempo</h2>
          <div className="text-xs font-black uppercase tracking-wider text-gray-400">{logs.length} logs carregados ({totalLogs} no período)</div>
        </div>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="dia" />
              <YAxis allowDecimals={false} />
              <Tooltip formatter={(value, name) => (name === 'custo_usd' ? [fmtUsd(value), 'Custo'] : [value, 'Chamadas'])} />
              <Line type="monotone" dataKey="chamadas" stroke="#3b82f6" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="custo_usd" stroke="#10b981" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100">
          <h2 className="text-lg font-bold text-gray-800 mb-3">Ferramentas mais usadas</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-gray-50 text-gray-400 font-bold uppercase text-[10px] tracking-widest">
                <tr>
                  <th className="px-4 py-3">Ferramenta</th>
                  <th className="px-4 py-3 text-right">Chamadas</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {(metricas?.ferramentas_top || []).map((t) => (
                  <tr key={t.nome}>
                    <td className="px-4 py-3 font-bold text-gray-700">{t.nome}</td>
                    <td className="px-4 py-3 text-right text-gray-600 font-bold">{t.count}</td>
                  </tr>
                ))}
                {(!metricas?.ferramentas_top || metricas.ferramentas_top.length === 0) && !loading ? (
                  <tr><td className="px-4 py-3 text-gray-500 font-medium" colSpan={2}>Sem dados no período.</td></tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100">
          <h2 className="text-lg font-bold text-gray-800 mb-3">Usuários com mais uso</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-gray-50 text-gray-400 font-bold uppercase text-[10px] tracking-widest">
                <tr>
                  <th className="px-4 py-3">Usuário</th>
                  <th className="px-4 py-3 text-right">Chamadas</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {(metricas?.usuarios_top || []).map((t) => (
                  <tr key={t.nome}>
                    <td className="px-4 py-3 font-bold text-gray-700">{t.nome}</td>
                    <td className="px-4 py-3 text-right text-gray-600 font-bold">{t.count}</td>
                  </tr>
                ))}
                {(!metricas?.usuarios_top || metricas.usuarios_top.length === 0) && !loading ? (
                  <tr><td className="px-4 py-3 text-gray-500 font-medium" colSpan={2}>Sem dados no período.</td></tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-5 flex items-center justify-between">
          <h2 className="text-lg font-bold text-gray-800">Logs recentes</h2>
          <div className="text-sm text-gray-500 font-medium">{loading ? 'Carregando…' : `${logs.length} itens`}</div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left min-w-[1050px]">
            <thead className="bg-gray-50 text-gray-400 font-bold uppercase text-[10px] tracking-widest">
              <tr>
                <th className="px-6 py-4">Quando</th>
                <th className="px-6 py-4">Tipo</th>
                <th className="px-6 py-4">Usuário</th>
                <th className="px-6 py-4">Resumo</th>
                <th className="px-6 py-4 text-right">Tokens</th>
                <th className="px-6 py-4 text-right">Custo</th>
                <th className="px-6 py-4 text-right">Latência</th>
                <th className="px-6 py-4 text-center">OK</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {(logs || []).map((l) => {
                const tokens = Number(l?.tokens_input || 0) + Number(l?.tokens_output || 0) + Number(l?.tokens_cache_read || 0);
                return (
                  <tr key={l.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 text-gray-600 font-medium">{String(l.criado_em || '').replace('T', ' ').slice(0, 19)}</td>
                    <td className="px-6 py-4">
                      <span className="px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-blue-50 text-blue-600">
                        {l.tipo}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-gray-700 font-bold">{l.usuario_nome || (l.usuario_id ? `Usuário #${l.usuario_id}` : '—')}</td>
                    <td className="px-6 py-4 text-gray-600 font-medium">{l.mensagem_resumo || '—'}</td>
                    <td className="px-6 py-4 text-right text-gray-700 font-bold">{tokens}</td>
                    <td className="px-6 py-4 text-right text-gray-700 font-bold">{fmtUsd(l.custo_estimado_usd)}</td>
                    <td className="px-6 py-4 text-right text-gray-700 font-bold">{Number(l.latencia_ms || 0)}ms</td>
                    <td className="px-6 py-4 text-center">
                      <span className={`px-2 py-1 rounded-lg text-[10px] font-black uppercase ${l.sucesso ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>
                        {l.sucesso ? 'sim' : 'não'}
                      </span>
                      {!l.sucesso && l.erro ? <div className="text-[10px] text-red-600 font-bold mt-1">{String(l.erro)}</div> : null}
                    </td>
                  </tr>
                );
              })}
              {logs.length === 0 && !loading ? (
                <tr><td className="px-6 py-6 text-gray-500 font-medium" colSpan={8}>Sem logs no período.</td></tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AdminIA;
