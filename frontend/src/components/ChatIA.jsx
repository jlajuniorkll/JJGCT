import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { iaService } from '../services/api';
import { Paperclip, Send, Sparkles, X } from 'lucide-react';
import RelatorioIA from './RelatorioIA';

const toBase64 = (file) => new Promise((resolve, reject) => {
  const reader = new FileReader();
  reader.onload = () => {
    const result = String(reader.result || '');
    const comma = result.indexOf(',');
    resolve(comma >= 0 ? result.slice(comma + 1) : result);
  };
  reader.onerror = reject;
  reader.readAsDataURL(file);
});

const friendlyActionName = (toolName) => {
  if (toolName === 'criar_despesa') return 'Criar despesa';
  if (toolName === 'criar_atividade') return 'Criar atividade';
  if (toolName === 'iniciar_atividade') return 'Iniciar atividade';
  if (toolName === 'pausar_atividade') return 'Pausar atividade';
  if (toolName === 'finalizar_pausa') return 'Retomar atividade';
  if (toolName === 'finalizar_viagem') return 'Finalizar viagem';
  return 'Ação pendente';
};

const formatBRL = (value) => {
  const n = Number(value);
  if (!Number.isFinite(n)) return String(value ?? '');
  return `R$ ${n.toFixed(2).replace('.', ',')}`;
};

const formatFieldValue = (key, value) => {
  if (key === 'valor') return formatBRL(value);
  if (value === null || value === undefined) return '';
  if (typeof value === 'boolean') return value ? 'Sim' : 'Não';
  if (typeof value === 'number') return String(value);
  if (typeof value === 'string') return value;
  return JSON.stringify(value);
};

const ChatIA = () => {
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const [history, setHistory] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [attachment, setAttachment] = useState(null);
  const [actionLoading, setActionLoading] = useState({});
  const fileInputRef = useRef(null);
  const listRef = useRef(null);
  const historyRef = useRef([]);

  const viagemId = useMemo(() => {
    const path = String(location?.pathname || '');
    const parts = path.split('/').filter(Boolean);
    if (parts[0] !== 'viagens') return null;
    const maybeId = parts[1];
    const n = Number(maybeId);
    return Number.isFinite(n) && n > 0 ? n : null;
  }, [location?.pathname]);

  useEffect(() => {
    if (!open) return;
    const t = setTimeout(() => {
      listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' });
    }, 0);
    return () => clearTimeout(t);
  }, [open, history, sending]);

  useEffect(() => {
    historyRef.current = history;
  }, [history]);

  const sendText = async ({ text, includeAttachment }) => {
    const safeText = String(text || '').trim();
    const includeFile = Boolean(includeAttachment && attachment);
    if (!safeText && !includeFile) return;
    if (sending) return;

    const userMsg = {
      id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      role: 'user',
      content: safeText || (includeFile ? 'Enviei um anexo.' : ''),
    };

    const nextHistory = [...(historyRef.current || []), userMsg];
    setHistory(nextHistory);
    setInput('');
    setSending(true);

    try {
      const payload = {
        historico: nextHistory.map((m) => ({ role: m.role === 'user' ? 'user' : 'assistant', content: String(m.content || '') })),
        mensagem: safeText || '',
        anexos: includeFile
          ? [{ nome: attachment.name, base64: attachment.base64, mime: attachment.mime }]
          : undefined,
        contexto: viagemId ? { viagem_id: viagemId } : undefined,
      };

      const res = await iaService.chatIA(payload);
      const data = res.data || {};
      const assistantMsg = {
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        role: 'assistant',
        content: String(data.mensagem || ''),
        tools: Array.isArray(data.ferramentas_chamadas) ? data.ferramentas_chamadas : [],
        pendingActions: Array.isArray(data.acoes_pendentes) ? data.acoes_pendentes : [],
        relatorios: Array.isArray(data.relatorios) ? data.relatorios : [],
        isError: false,
      };
      setHistory((prev) => [...prev, assistantMsg]);
      if (includeFile) {
        setAttachment(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
      }
    } catch {
      const assistantMsg = {
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        role: 'assistant',
        content: 'Não consegui responder agora, tente novamente.',
        tools: [],
        pendingActions: [],
        isError: true,
      };
      setHistory((prev) => [...prev, assistantMsg]);
    } finally {
      setSending(false);
    }
  };

  const confirmAction = async (idProposta) => {
    const pid = String(idProposta || '').trim();
    if (!pid) return;
    if (actionLoading[pid]) return;

    setActionLoading((prev) => ({ ...prev, [pid]: true }));
    try {
      const res = await iaService.confirmarAcaoIA(pid);
      const data = res.data || {};
      const created = data.registro_criado || {};
      const tipo = created.tipo ? String(created.tipo) : 'registro';
      const rid = created.id ? String(created.id) : '';
      const msg = `✅ ${tipo} criado${rid ? ` — id ${rid}` : ''}`;

      try {
        const viagemIdCreated = created.viagem_id ? Number(created.viagem_id) : null;
        window.dispatchEvent(new CustomEvent('jjg_viagem:ia_acao_confirmada', {
          detail: {
            tipo,
            id: created.id ?? null,
            viagem_id: Number.isFinite(viagemIdCreated) ? viagemIdCreated : null,
          },
        }));
      } catch {
        0;
      }

      setHistory((prev) => prev.map((m) => {
        if (m.role !== 'assistant') return m;
        if (!Array.isArray(m.pendingActions) || m.pendingActions.length === 0) return m;
        const next = m.pendingActions.filter((a) => String(a?.id_proposta || '') !== pid);
        if (next.length === m.pendingActions.length) return m;
        return { ...m, pendingActions: next };
      }).concat([{
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        role: 'assistant',
        content: msg,
        tools: [],
        pendingActions: [],
        isError: false,
      }]));
    } catch (err) {
      const detail = err?.response?.data?.detail ? String(err.response.data.detail) : 'Não consegui confirmar agora.';
      setHistory((prev) => [...prev, {
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        role: 'assistant',
        content: detail,
        tools: [],
        pendingActions: [],
        isError: true,
      }]);
    } finally {
      setActionLoading((prev) => ({ ...prev, [pid]: false }));
    }
  };

  const cancelAction = async (idProposta) => {
    const pid = String(idProposta || '').trim();
    if (!pid) return;
    if (actionLoading[pid]) return;

    setActionLoading((prev) => ({ ...prev, [pid]: true }));
    try {
      await iaService.cancelarAcaoIA(pid);
      setHistory((prev) => prev.map((m) => {
        if (m.role !== 'assistant') return m;
        if (!Array.isArray(m.pendingActions) || m.pendingActions.length === 0) return m;
        const next = m.pendingActions.filter((a) => String(a?.id_proposta || '') !== pid);
        if (next.length === m.pendingActions.length) return m;
        return { ...m, pendingActions: next };
      }));
      await sendText({ text: 'cancelei a criação', includeAttachment: false });
    } catch (err) {
      const detail = err?.response?.data?.detail ? String(err.response.data.detail) : 'Não consegui cancelar agora.';
      setHistory((prev) => [...prev, {
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        role: 'assistant',
        content: detail,
        tools: [],
        pendingActions: [],
        isError: true,
      }]);
    } finally {
      setActionLoading((prev) => ({ ...prev, [pid]: false }));
    }
  };

  return (
    <div className="print:hidden">
      {open ? (
        <button
          type="button"
          className="fixed inset-0 bg-black/30 z-[80] md:hidden"
          onClick={() => setOpen(false)}
          aria-label="Fechar chat"
        />
      ) : null}

      <div
        className={`fixed top-0 right-0 h-full w-full md:w-[400px] bg-white border-l border-gray-200 shadow-2xl z-[90] transform transition-transform ${
          open ? 'translate-x-0' : 'translate-x-full'
        }`}
        role="dialog"
        aria-label="Chat com IA"
      >
        <div className="h-full flex flex-col">
          <div className="p-4 border-b border-gray-100 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                <Sparkles size={18} />
              </div>
              <div className="min-w-0">
                <p className="font-black text-gray-800 leading-tight">Chat com IA</p>
                <p className="text-xs text-gray-500 font-bold truncate">
                  {viagemId ? `Contexto: Viagem #${viagemId}` : 'Sem contexto de viagem'}
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="p-2 rounded-xl hover:bg-gray-50 text-gray-500"
              aria-label="Fechar"
            >
              <X size={18} />
            </button>
          </div>

          <div ref={listRef} className="flex-1 overflow-auto p-4 space-y-3 bg-gray-50">
            {history.length === 0 ? (
              <div className="bg-white border border-gray-100 rounded-2xl p-4 text-sm text-gray-600 font-medium">
                Pergunte sobre viagens, despesas e métricas. Ex: “Quais minhas viagens em andamento?”
              </div>
            ) : null}

            {history.map((m) => (
              <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm font-medium whitespace-pre-wrap ${
                    m.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : m.isError
                        ? 'bg-red-50 border border-red-100 text-red-700'
                        : 'bg-white border border-gray-100 text-gray-800'
                  }`}
                >
                  {m.content}
                  {m.role === 'assistant' && Array.isArray(m.relatorios) && m.relatorios.length ? (
                    <div className="mt-3 space-y-3">
                      {m.relatorios.map((r, idx) => (
                        <RelatorioIA key={`${r?.tipo || 'rel'}-${idx}`} relatorio={r} />
                      ))}
                    </div>
                  ) : null}
                  {m.role === 'assistant' && Array.isArray(m.tools) && m.tools.length ? (
                    <div className="mt-3 space-y-1">
                      {m.tools.map((t, idx) => (
                        <div key={`${t.nome || 'tool'}-${idx}`} className="text-[11px] text-gray-400 font-bold">
                          🔧 {t.resultado_resumo || t.nome}
                        </div>
                      ))}
                    </div>
                  ) : null}
                  {m.role === 'assistant' && Array.isArray(m.pendingActions) && m.pendingActions.length ? (
                    <div className="mt-3 space-y-2">
                      {m.pendingActions.map((a) => {
                        const idProposta = String(a?.id_proposta || '');
                        const toolName = String(a?.ferramenta || '');
                        const args = a?.args_validados && typeof a.args_validados === 'object' ? a.args_validados : {};
                        const rows = Object.entries(args);
                        const loading = Boolean(actionLoading[idProposta]);

                        return (
                          <div key={idProposta} className="rounded-2xl border border-gray-200 bg-gray-50 p-3">
                            <div className="flex items-start justify-between gap-3">
                              <div className="min-w-0">
                                <p className="text-xs font-black text-gray-800">{friendlyActionName(toolName)}</p>
                                <p className="text-[11px] font-bold text-gray-500 truncate">{idProposta}</p>
                              </div>
                            </div>

                            {rows.length ? (
                              <div className="mt-2 overflow-hidden rounded-xl border border-gray-200 bg-white">
                                <div className="divide-y divide-gray-100">
                                  {rows.map(([k, v]) => (
                                    <div key={k} className="flex items-start justify-between gap-3 px-3 py-2">
                                      <div className="text-[11px] font-black text-gray-600">{k}</div>
                                      <div className="text-[11px] font-bold text-gray-800 text-right break-all">
                                        {formatFieldValue(k, v)}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            ) : null}

                            {a?.resumo_legivel ? (
                              <div className="mt-2 text-[11px] font-medium text-gray-600 whitespace-pre-wrap">
                                {String(a.resumo_legivel)}
                              </div>
                            ) : null}

                            <div className="mt-3 flex gap-2">
                              <button
                                type="button"
                                onClick={() => confirmAction(idProposta)}
                                disabled={loading}
                                className="flex-1 px-3 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-black"
                              >
                                {loading ? 'Confirmando…' : 'Confirmar'}
                              </button>
                              <button
                                type="button"
                                onClick={() => cancelAction(idProposta)}
                                disabled={loading}
                                className="flex-1 px-3 py-2 rounded-xl bg-white border border-gray-200 hover:bg-gray-50 disabled:opacity-50 text-gray-700 text-xs font-black"
                              >
                                Cancelar
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : null}
                </div>
              </div>
            ))}

            {sending ? (
              <div className="flex justify-start">
                <div className="max-w-[85%] rounded-2xl px-4 py-3 text-sm font-bold bg-white border border-gray-100 text-gray-500">
                  digitando…
                </div>
              </div>
            ) : null}
          </div>

          <div className="p-4 border-t border-gray-100 bg-white space-y-3">
            {attachment ? (
              <div className="flex items-center justify-between gap-3 bg-gray-50 border border-gray-100 rounded-2xl px-3 py-2">
                <div className="min-w-0">
                  <p className="text-xs font-black text-gray-700 truncate">{attachment.name}</p>
                  <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">{attachment.mime}</p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setAttachment(null);
                    if (fileInputRef.current) fileInputRef.current.value = '';
                  }}
                  className="p-2 rounded-xl hover:bg-gray-100 text-gray-500"
                  aria-label="Remover anexo"
                >
                  <X size={16} />
                </button>
              </div>
            ) : null}

            <div className="flex items-end gap-2">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="p-3 rounded-2xl border border-gray-200 text-gray-600 hover:bg-gray-50"
                aria-label="Anexar imagem"
                disabled={sending}
              >
                <Paperclip size={18} />
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={async (e) => {
                  const f = e.target.files?.[0];
                  if (!f) return;
                  try {
                    const b64 = await toBase64(f);
                    setAttachment({ name: f.name, mime: f.type || 'image/*', base64: b64 });
                  } catch {
                    setAttachment(null);
                  }
                }}
              />

              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendText({ text: input, includeAttachment: true });
                  }
                }}
                placeholder="Escreva sua mensagem…"
                rows={2}
                className="flex-1 resize-none px-4 py-3 rounded-2xl border border-gray-200 bg-gray-50 outline-none focus:ring-2 focus:ring-blue-500 font-medium"
                disabled={sending}
              />

              <button
                type="button"
                onClick={() => sendText({ text: input, includeAttachment: true })}
                disabled={sending || (!String(input || '').trim() && !attachment)}
                className="p-3 rounded-2xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white shadow-lg shadow-blue-200"
                aria-label="Enviar"
              >
                <Send size={18} />
              </button>
            </div>
            <div className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">
              Enter envia • Shift+Enter quebra linha
            </div>
          </div>
        </div>
      </div>

      {!open ? (
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="fixed bottom-6 right-6 z-[95] w-14 h-14 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white shadow-2xl shadow-blue-200 flex items-center justify-center active:scale-95 transition-transform"
          aria-label="Abrir chat com IA"
        >
          <Sparkles size={22} />
        </button>
      ) : null}
    </div>
  );
};

export default ChatIA;
