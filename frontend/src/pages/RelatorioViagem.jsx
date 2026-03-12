import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api, { tripService } from '../services/api';
import { 
  FileText, 
  ArrowLeft, 
  Download, 
  Printer, 
  MapPin, 
  Users, 
  Car, 
  Clock, 
  DollarSign,
  Briefcase
} from 'lucide-react';
import { format, differenceInSeconds } from 'date-fns';
import { ptBR } from 'date-fns/locale';

const RelatorioViagem = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const response = await tripService.getReport(id);
        setReport(response.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchReport();
  }, [id]);

  if (loading) return <div className="p-8 text-center animate-pulse text-gray-500">Gerando relatório...</div>;
  if (!report) return <div className="p-8 text-center">Relatório não encontrado.</div>;

  const { viagem, distancia_percorrida_km, total_horas_trabalhadas, total_despesas } = report;

  const getComprovanteUrl = (path) => {
    if (!path) return null;
    const base = api.defaults.baseURL || '';
    const normalized = String(path).replace(/^\/+/, '');
    return `${base}/${normalized}`;
  };

  const isImageUrl = (url) => /\.(png|jpe?g|gif|webp)$/i.test(url);

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fade-in py-8 px-4 print:py-0 print:px-0">
      <div className="flex items-center justify-between gap-4 print:hidden">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate(`/viagens/${id}`)} className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-500">
            <ArrowLeft size={24} />
          </button>
          <h1 className="text-2xl font-bold text-gray-800">Relatório Consolidado</h1>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={handlePrint}
            className="bg-white border border-gray-200 text-gray-600 px-4 py-2 rounded-xl font-bold flex items-center gap-2 hover:bg-gray-50 transition-all shadow-sm"
          >
            <Printer size={18} /> Imprimir
          </button>
          <button className="bg-blue-600 text-white px-4 py-2 rounded-xl font-bold flex items-center gap-2 hover:bg-blue-700 transition-all shadow-lg shadow-blue-100">
            <Download size={18} /> PDF
          </button>
        </div>
      </div>

      <div className="bg-white rounded-3xl shadow-xl border border-gray-100 overflow-hidden print:shadow-none print:border-none">
        {/* Header Relatório */}
        <div className="bg-gray-800 p-8 text-white flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-blue-400 font-black uppercase tracking-widest text-xs">
              <Briefcase size={14} /> Viagem Corporativa
            </div>
            <h2 className="text-3xl font-black">{viagem.cliente}</h2>
            <p className="text-gray-400 font-medium">{viagem.motivo}</p>
          </div>
          <div className="text-right">
            <p className="text-xs font-bold text-gray-500 uppercase tracking-widest">ID da Viagem</p>
            <p className="text-2xl font-black text-white">#{viagem.id}</p>
            <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mt-2">Data Emissão</p>
            <p className="text-sm font-bold text-gray-300">{format(new Date(), 'dd/MM/yyyy HH:mm')}</p>
          </div>
        </div>

        <div className="p-8 space-y-10">
          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="p-4 bg-gray-50 rounded-2xl border border-gray-100">
              <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">Distância</p>
              <p className="text-xl font-black text-gray-800">{distancia_percorrida_km} <span className="text-xs font-bold text-gray-400">KM</span></p>
            </div>
            <div className="p-4 bg-gray-50 rounded-2xl border border-gray-100">
              <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">Horas Trab.</p>
              <p className="text-xl font-black text-gray-800">{total_horas_trabalhadas.split('.')[0]}</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-2xl border border-gray-100">
              <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">Despesas</p>
              <p className="text-xl font-black text-emerald-600">R$ {total_despesas.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-2xl border border-gray-100">
              <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">Status</p>
              <p className="text-sm font-black text-blue-600 uppercase tracking-tight">{viagem.status.replace('_', ' ')}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
            {/* Itinerary */}
            <div className="space-y-4">
              <h3 className="text-sm font-black text-gray-800 uppercase tracking-widest flex items-center gap-2">
                <MapPin size={16} className="text-blue-600" /> Itinerário Real
              </h3>
              <div className="space-y-6 relative before:absolute before:left-[11px] before:top-2 before:bottom-2 before:w-0.5 before:bg-blue-100">
                <div className="relative pl-8">
                  <div className="absolute left-0 top-1 w-6 h-6 rounded-full bg-blue-100 border-4 border-white shadow-sm flex items-center justify-center z-10">
                    <div className="w-2 h-2 rounded-full bg-blue-600"></div>
                  </div>
                  <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">Partida</p>
                  <p className="text-sm font-bold text-gray-800">{viagem.local_partida}</p>
                  <p className="text-xs font-medium text-gray-500">
                    {viagem.data_hora_real_saida 
                      ? format(new Date(viagem.data_hora_real_saida), "dd MMM, HH:mm'h'", { locale: ptBR })
                      : 'Não registrada'}
                  </p>
                </div>
                <div className="relative pl-8">
                  <div className="absolute left-0 top-1 w-6 h-6 rounded-full bg-emerald-100 border-4 border-white shadow-sm flex items-center justify-center z-10">
                    <div className="w-2 h-2 rounded-full bg-emerald-600"></div>
                  </div>
                  <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">Chegada</p>
                  <p className="text-sm font-bold text-gray-800">{viagem.local_chegada}</p>
                  <p className="text-xs font-medium text-gray-500">
                    {viagem.data_hora_real_chegada 
                      ? format(new Date(viagem.data_hora_real_chegada), "dd MMM, HH:mm'h'", { locale: ptBR })
                      : 'Não registrada'}
                  </p>
                </div>
              </div>
            </div>

            {/* Team */}
            <div className="space-y-4">
              <h3 className="text-sm font-black text-gray-800 uppercase tracking-widest flex items-center gap-2">
                <Users size={16} className="text-blue-600" /> Equipe Participante
              </h3>
              <div className="grid grid-cols-1 gap-3">
                {viagem.participantes?.map(p => (
                  <div key={p.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-2xl border border-gray-100">
                    <div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center text-blue-600 font-bold shadow-sm">
                      {p.nome[0]}
                    </div>
                    <div>
                      <p className="text-sm font-bold text-gray-800">{p.nome}</p>
                      <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">{p.tipousuario}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-sm font-black text-gray-800 uppercase tracking-widest flex items-center gap-2">
              <Car size={16} className="text-blue-600" /> Detalhamento de Transporte
            </h3>
            <div className="bg-gray-50 rounded-3xl border border-gray-100 p-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                <div className="p-4 bg-white rounded-2xl border border-gray-100">
                  <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">Meio</p>
                  <p className="text-sm font-black text-gray-800 capitalize">{viagem.meio_transporte || '--'}</p>
                </div>

                <div className="p-4 bg-white rounded-2xl border border-gray-100 lg:col-span-2">
                  <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">Veículo</p>
                  <p className="text-sm font-black text-gray-800">{viagem.transporte?.veiculo?.modelo || '--'}</p>
                  <p className="text-xs font-bold text-gray-500">{viagem.transporte?.veiculo?.placa || '--'}</p>
                </div>

                <div className="p-4 bg-white rounded-2xl border border-gray-100">
                  <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">Motorista</p>
                  <p className="text-sm font-black text-gray-800">{viagem.transporte?.motorista?.nome || '--'}</p>
                </div>

                <div className="p-4 bg-white rounded-2xl border border-gray-100">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">KM Inicial</p>
                      <p className="text-sm font-black text-gray-800">{viagem.transporte?.km_saida ?? '--'}</p>
                    </div>
                    <div>
                      <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">KM Final</p>
                      <p className="text-sm font-black text-gray-800">{viagem.transporte?.km_chegada ?? '--'}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Activities Table */}
          <div className="space-y-4">
            <h3 className="text-sm font-black text-gray-800 uppercase tracking-widest flex items-center gap-2">
              <Clock size={16} className="text-blue-600" /> Detalhamento de Atividades
            </h3>
            <div className="overflow-hidden border border-gray-100 rounded-3xl">
              <table className="w-full text-sm text-left">
                <thead className="bg-gray-50 text-gray-400 font-bold uppercase text-[10px] tracking-widest">
                  <tr>
                    <th className="px-6 py-4">Atividade</th>
                    <th className="px-6 py-4 text-center">Início</th>
                    <th className="px-6 py-4 text-center">Fim</th>
                    <th className="px-6 py-4 text-right">Duração</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {viagem.atividades?.map(atv => (
                    <tr key={atv.id}>
                      <td className="px-6 py-4 font-bold text-gray-700">{atv.descricao}</td>
                      <td className="px-6 py-4 text-center text-gray-500">{atv.inicio ? format(new Date(atv.inicio), 'HH:mm') : '--'}</td>
                      <td className="px-6 py-4 text-center text-gray-500">{atv.fim ? format(new Date(atv.fim), 'HH:mm') : '--'}</td>
                      <td className="px-6 py-4 text-right font-black text-gray-800">
                        {atv.inicio && atv.fim 
                          ? formatTimeDiff(new Date(atv.inicio), new Date(atv.fim), atv.pausas)
                          : '--'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Expenses Table */}
          <div className="space-y-4">
            <h3 className="text-sm font-black text-gray-800 uppercase tracking-widest flex items-center gap-2">
              <DollarSign size={16} className="text-blue-600" /> Detalhamento de Despesas
            </h3>
            <div className="overflow-hidden border border-gray-100 rounded-3xl">
              <table className="w-full text-sm text-left">
                <thead className="bg-gray-50 text-gray-400 font-bold uppercase text-[10px] tracking-widest">
                  <tr>
                    <th className="px-6 py-4">Descrição</th>
                    <th className="px-6 py-4">Pagamento</th>
                    <th className="px-6 py-4 text-right">Valor</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {viagem.despesas?.map(exp => (
                    <tr key={exp.id}>
                      <td className="px-6 py-4 font-bold text-gray-700">{exp.descricao}</td>
                      <td className="px-6 py-4 text-gray-500">{exp.forma_pagamento}</td>
                      <td className="px-6 py-4 text-right font-black text-gray-800">
                        R$ {exp.valor.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="bg-gray-50 font-black">
                  <tr>
                    <td colSpan="2" className="px-6 py-4 text-gray-800 uppercase tracking-widest text-xs text-right">Total Consolidado</td>
                    <td className="px-6 py-4 text-right text-emerald-600 text-lg">
                      R$ {total_despesas.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-sm font-black text-gray-800 uppercase tracking-widest flex items-center gap-2">
              <FileText size={16} className="text-blue-600" /> Anexos de Despesas
            </h3>

            {viagem.despesas?.some((exp) => exp.comprovante_url) ? (
              <div className="grid grid-cols-1 gap-6">
                {viagem.despesas
                  .filter((exp) => exp.comprovante_url)
                  .map((exp) => {
                    const url = getComprovanteUrl(exp.comprovante_url);
                    if (!url) return null;

                    return (
                      <div key={exp.id} className="bg-gray-50 rounded-3xl border border-gray-100 p-6 space-y-4">
                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <p className="text-sm font-black text-gray-800">{exp.descricao}</p>
                            <p className="text-xs font-bold text-gray-500">
                              {exp.forma_pagamento} • R$ {exp.valor.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                            </p>
                          </div>
                          <a
                            href={url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-xs font-black text-blue-600 hover:underline print:hidden"
                          >
                            Abrir
                          </a>
                        </div>

                        {isImageUrl(url) ? (
                          <img
                            src={url}
                            alt={`Comprovante - ${exp.descricao}`}
                            className="w-full max-h-[520px] object-contain bg-white rounded-2xl border border-gray-100"
                            loading="lazy"
                          />
                        ) : (
                          <div className="p-4 bg-white rounded-2xl border border-gray-100">
                            <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">Arquivo</p>
                            <a href={url} target="_blank" rel="noreferrer" className="text-sm font-black text-blue-600 break-all">
                              {url}
                            </a>
                          </div>
                        )}
                      </div>
                    );
                  })}
              </div>
            ) : (
              <p className="text-sm text-gray-500 bg-gray-50 p-6 rounded-2xl text-center border border-gray-100">
                Nenhum anexo de despesa disponível.
              </p>
            )}
          </div>
        </div>

        {/* Footer print */}
        <div className="hidden print:block p-8 border-t border-gray-100 text-center space-y-4">
          <div className="grid grid-cols-2 gap-20 px-20 pt-10">
            <div className="border-t border-gray-400 pt-2 text-xs font-bold text-gray-500 uppercase tracking-widest">Assinatura do Colaborador</div>
            <div className="border-t border-gray-400 pt-2 text-xs font-bold text-gray-500 uppercase tracking-widest">Assinatura Gestoria</div>
          </div>
          <p className="text-[10px] text-gray-400 pt-10 font-medium italic">Documento gerado eletronicamente pelo sistema Corporate Travel.</p>
        </div>
      </div>
    </div>
  );
};

const formatTimeDiff = (start, end, pausas = []) => {
  const safeSecondsBetween = (a, b) => Math.max(0, differenceInSeconds(a, b));

  let diff = safeSecondsBetween(end, start);

  pausas.forEach((p) => {
    if (p.inicio && p.fim) {
      diff -= safeSecondsBetween(new Date(p.fim), new Date(p.inicio));
    }
  });

  diff = Math.max(0, diff);

  const hrs = Math.floor(diff / 3600);
  const mins = Math.floor((diff % 3600) / 60);
  return `${hrs}h ${mins}m`;
};

export default RelatorioViagem;
