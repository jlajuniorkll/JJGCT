import React, { useMemo, useState } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  CartesianGrid,
} from 'recharts';

const COLORS = ['#2563eb', '#16a34a', '#f97316', '#a855f7', '#ef4444', '#0ea5e9', '#84cc16', '#f59e0b'];

const toCSV = (rows) => {
  if (!Array.isArray(rows) || rows.length === 0) return '';
  const cols = Array.from(new Set(rows.flatMap((r) => Object.keys(r || {}))));
  const escape = (v) => {
    if (v === null || v === undefined) return '';
    const s = typeof v === 'object' ? JSON.stringify(v) : String(v);
    const needsQuote = /[",\n;]/.test(s);
    const safe = s.replaceAll('"', '""');
    return needsQuote ? `"${safe}"` : safe;
  };
  const header = cols.map(escape).join(';');
  const lines = rows.map((r) => cols.map((c) => escape(r?.[c])).join(';'));
  return [header, ...lines].join('\n');
};

const downloadTextFile = ({ filename, content, mime }) => {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
};

const formatPeriodo = (periodo) => {
  if (!periodo || typeof periodo !== 'object') return '';
  const ini = periodo.inicio ? String(periodo.inicio) : '';
  const fim = periodo.fim ? String(periodo.fim) : '';
  if (ini && fim) return `${ini} → ${fim}`;
  if (ini) return `a partir de ${ini}`;
  if (fim) return `até ${fim}`;
  return '';
};

const buildPrintHTML = ({ titulo, periodo, resumo, dados, totais, secoes }) => {
  const rows = Array.isArray(dados) ? dados : [];
  const cols = Array.from(new Set(rows.flatMap((r) => Object.keys(r || {}))));
  const showResumo = !!secoes?.resumo;
  const showTotais = !!secoes?.totais;
  const showTabela = !!secoes?.tabela;
  const escapeHtml = (s) => String(s ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');

  const tableHead = cols.map((c) => `<th style="text-align:left;border-bottom:1px solid #ddd;padding:6px 8px">${escapeHtml(c)}</th>`).join('');
  const tableBody = rows.map((r) => {
    const tds = cols.map((c) => `<td style="border-bottom:1px solid #f0f0f0;padding:6px 8px;vertical-align:top">${escapeHtml(r?.[c])}</td>`).join('');
    return `<tr>${tds}</tr>`;
  }).join('');

  const totaisLines = showTotais && totais && typeof totais === 'object'
    ? Object.entries(totais).map(([k, v]) => `<div><b>${escapeHtml(k)}:</b> ${escapeHtml(v)}</div>`).join('')
    : '';

  return `
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>${escapeHtml(titulo)}</title>
  </head>
  <body style="font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto; color:#111; padding:24px;">
    <h1 style="margin:0 0 8px 0; font-size:20px;">${escapeHtml(titulo)}</h1>
    ${periodo ? `<div style="color:#555; margin-bottom:8px;">Período: ${escapeHtml(periodo)}</div>` : ''}
    ${showResumo && resumo ? `<div style="margin:8px 0 16px 0;">${escapeHtml(resumo)}</div>` : ''}
    ${totaisLines ? `<div style="margin:8px 0 16px 0; padding:10px 12px; border:1px solid #eee; border-radius:10px;">${totaisLines}</div>` : ''}
    ${showTabela ? `<table style="border-collapse:collapse; width:100%; font-size:12px;">
      <thead><tr>${tableHead}</tr></thead>
      <tbody>${tableBody}</tbody>
    </table>` : ''}
  </body>
</html>
  `.trim();
};

const RelatorioIA = ({ relatorio }) => {
  const safe = relatorio && typeof relatorio === 'object' ? relatorio : {};
  const titulo = String(safe.titulo || 'Relatório');
  const grafico = String(safe.grafico_sugerido || 'tabela');
  const periodo = formatPeriodo(safe.periodo);
  const resumo = safe.resumo_textual ? String(safe.resumo_textual) : '';
  const emptyRows = useMemo(() => [], []);
  const dados = Array.isArray(safe.dados) ? safe.dados : emptyRows;
  const totais = safe.totais && typeof safe.totais === 'object' ? safe.totais : null;

  const [secoes, setSecoes] = useState({ resumo: true, totais: true, grafico: true, tabela: true });
  const toggleSecao = (k) => setSecoes((prev) => ({ ...prev, [k]: !prev?.[k] }));

  const hasChart = useMemo(() => ['barra', 'pizza', 'linha'].includes(grafico), [grafico]);
  const showChart = hasChart && secoes.grafico;
  const showTable = (!hasChart || grafico === 'tabela') && secoes.tabela;
  const showResumo = secoes.resumo && !!resumo;
  const showTotais = secoes.totais && !!totais;

  const normalized = useMemo(() => {
    return dados.map((d, idx) => ({
      ...d,
      label: d?.label ?? `Item ${idx + 1}`,
      valor: Number.isFinite(Number(d?.valor)) ? Number(d.valor) : 0,
    }));
  }, [dados]);

  return (
    <div className="mt-3 rounded-2xl border border-gray-200 bg-white p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-black text-gray-800">{titulo}</p>
          {periodo ? <p className="text-[11px] font-bold text-gray-500 truncate">Período: {periodo}</p> : null}
          {showResumo ? <p className="mt-2 text-xs font-medium text-gray-700 whitespace-pre-wrap">{resumo}</p> : null}
        </div>
        <div className="flex flex-col gap-2">
          <button
            type="button"
            onClick={() => {
              const csv = toCSV(dados);
              downloadTextFile({
                filename: `${titulo.replaceAll(/[\\/:*?"<>|]/g, '_')}.csv`,
                content: csv,
                mime: 'text/csv;charset=utf-8',
              });
            }}
            className="px-3 py-2 rounded-xl bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 text-xs font-black"
          >
            Exportar CSV
          </button>
          <button
            type="button"
            onClick={() => {
              const html = buildPrintHTML({ titulo, periodo, resumo, dados, totais, secoes: { resumo: secoes.resumo, totais: secoes.totais, tabela: secoes.tabela } });
              const w = window.open('', '_blank', 'noopener,noreferrer,width=900,height=700');
              if (!w) return;
              w.document.open();
              w.document.write(html);
              w.document.close();
              w.focus();
              w.print();
            }}
            className="px-3 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-black"
          >
            Exportar PDF
          </button>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-3 text-[11px] font-bold text-gray-600">
        <label className="flex items-center gap-2 cursor-pointer select-none">
          <input type="checkbox" checked={!!secoes.resumo} onChange={() => toggleSecao('resumo')} />
          Resumo
        </label>
        <label className="flex items-center gap-2 cursor-pointer select-none">
          <input type="checkbox" checked={!!secoes.totais} onChange={() => toggleSecao('totais')} />
          Totais
        </label>
        {hasChart ? (
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input type="checkbox" checked={!!secoes.grafico} onChange={() => toggleSecao('grafico')} />
            Gráfico
          </label>
        ) : null}
        <label className="flex items-center gap-2 cursor-pointer select-none">
          <input type="checkbox" checked={!!secoes.tabela} onChange={() => toggleSecao('tabela')} />
          Tabela
        </label>
      </div>

      {showTotais ? (
        <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2">
          {Object.entries(totais).map(([k, v]) => (
            <div key={k} className="rounded-xl border border-gray-200 bg-gray-50 px-3 py-2">
              <div className="text-[10px] font-black text-gray-500 uppercase tracking-wider">{k}</div>
              <div className="text-sm font-bold text-gray-800 break-all">{String(v)}</div>
            </div>
          ))}
        </div>
      ) : null}

      <div className="mt-4">
        {grafico === 'barra' && showChart ? (
          <div className="h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={normalized}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="label" tick={{ fontSize: 10 }} interval={0} height={60} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip />
                <Bar dataKey="valor" fill={COLORS[0]} radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : null}

        {grafico === 'linha' && showChart ? (
          <div className="h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={normalized}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="label" tick={{ fontSize: 10 }} interval={0} height={60} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip />
                <Line type="monotone" dataKey="valor" stroke={COLORS[0]} strokeWidth={2} dot={{ r: 2 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : null}

        {grafico === 'pizza' && showChart ? (
          <div className="h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Tooltip />
                <Pie data={normalized} dataKey="valor" nameKey="label" outerRadius={90} label>
                  {normalized.map((_, idx) => (
                    <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
        ) : null}

        {showTable ? (
          <div className="overflow-auto rounded-2xl border border-gray-200">
            <table className="min-w-full text-xs">
              <thead className="bg-gray-50">
                <tr>
                  {Array.from(new Set(dados.flatMap((r) => Object.keys(r || {})))).map((c) => (
                    <th key={c} className="text-left px-3 py-2 font-black text-gray-600 whitespace-nowrap">{c}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {dados.map((r, idx) => (
                  <tr key={idx} className="bg-white">
                    {Array.from(new Set(dados.flatMap((x) => Object.keys(x || {})))).map((c) => (
                      <td key={c} className="px-3 py-2 font-medium text-gray-800 whitespace-nowrap">{String(r?.[c] ?? '')}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {dados.length === 0 ? (
          <div className="mt-3 text-xs font-bold text-gray-500">Sem dados para exibir.</div>
        ) : null}
      </div>
    </div>
  );
};

export default RelatorioIA;
