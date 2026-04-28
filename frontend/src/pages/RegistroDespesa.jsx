import React, { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api, { expenseService, configService, iaService } from '../services/api';
import { 
  DollarSign, 
  ArrowLeft, 
  Camera, 
  Upload, 
  X,
  CreditCard,
  FileText,
  CheckCircle,
  Sparkles
} from 'lucide-react';

const RegistroDespesa = () => {
  const { id, despesaId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [optimizing, setOptimizing] = useState(false);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [expensePhotoRequired, setExpensePhotoRequired] = useState(false);
  const [iaAvailable, setIaAvailable] = useState(false);
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
  const [iaLoading, setIaLoading] = useState(false);
  const [iaBannerActive, setIaBannerActive] = useState(false);
  const [iaLowConfidence, setIaLowConfidence] = useState({});
  const [iaToast, setIaToast] = useState('');

  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);
  const valorInputRef = useRef(null);
  
  const [formData, setFormData] = useState({
    valor: '',
    forma_pagamento: 'Cartão Corporativo',
    descricao: ''
  });

  const readAsDataURL = (blob) => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });

  const loadImageFromDataURL = (dataUrl) => new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = dataUrl;
  });

  const optimizeImage = async (inputFile) => {
    if (!inputFile?.type?.startsWith('image/')) return inputFile;

    const maxDimension = 1600;
    const quality = 0.8;

    const dataUrl = await readAsDataURL(inputFile);
    const img = await loadImageFromDataURL(dataUrl);

    const scale = Math.min(1, maxDimension / Math.max(img.width, img.height));
    const targetWidth = Math.max(1, Math.round(img.width * scale));
    const targetHeight = Math.max(1, Math.round(img.height * scale));

    const canvas = document.createElement('canvas');
    canvas.width = targetWidth;
    canvas.height = targetHeight;

    const ctx = canvas.getContext('2d');
    if (!ctx) return inputFile;

    ctx.drawImage(img, 0, 0, targetWidth, targetHeight);

    const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', quality));
    if (!(blob instanceof Blob)) return inputFile;

    const optimizedFile = new File(
      [blob],
      inputFile.name.replace(/\.[^.]+$/, '') + '.jpg',
      { type: 'image/jpeg', lastModified: Date.now() },
    );

    return optimizedFile.size < inputFile.size ? optimizedFile : inputFile;
  };

  const handleFileChange = async (e) => {
    const selected = e.target.files?.[0];
    if (!selected) return;

    setOptimizing(true);
    try {
      const processed = await optimizeImage(selected);
      setFile(processed);
      setPreview(await readAsDataURL(processed));
    } catch (err) {
      console.error(err);
      setFile(selected);
      setPreview(await readAsDataURL(selected));
    } finally {
      setOptimizing(false);
      e.target.value = '';
    }
  };

  const getComprovanteUrl = (path) => {
    if (!path) return null;
    const base = api.defaults.baseURL || '';
    const normalized = String(path).replace(/^\/+/, '');
    return `${base}/${normalized}`;
  };

  useEffect(() => {
    const fetchDespesa = async () => {
      if (!despesaId) return;
      try {
        const res = await expenseService.get(despesaId);
        const exp = res.data;
        setFormData({
          valor: String(exp.valor ?? ''),
          forma_pagamento: exp.forma_pagamento || 'Cartão Corporativo',
          descricao: exp.descricao || '',
        });
        setFile(null);
        setPreview(getComprovanteUrl(exp.comprovante_url));
      } catch (err) {
        console.error(err);
        alert('Erro ao carregar despesa');
      }
    };

    const fetchConfig = async () => {
      try {
        const res = await configService.get();
        setExpensePhotoRequired(!!res.data?.expense_photo_required);
        setIaAvailable(!!res.data?.anthropic_api_key_configured || !!res.data?.gemini_api_key_configured);
        setExpenseDescriptionOptions(
          Array.isArray(res.data?.expense_description_options) && res.data.expense_description_options.length
            ? res.data.expense_description_options
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
      } catch (err) {
        console.error(err);
      }
    };

    fetchDespesa();
    fetchConfig();
  }, [despesaId]);

  useEffect(() => {
    if (loading) return;
    const t = setTimeout(() => valorInputRef.current?.focus(), 0);
    return () => clearTimeout(t);
  }, [despesaId, loading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (expensePhotoRequired && !file && !preview) {
      alert('O comprovante é obrigatório.');
      return;
    }
    setLoading(true);
    try {
      const data = new FormData();
      data.append('valor', formData.valor);
      data.append('forma_pagamento', formData.forma_pagamento);
      data.append('forma_pagamento', formData.forma_pagamento);
      data.append('descricao', formData.descricao);
      if (file) data.append('file', file);

      if (despesaId) {
        await expenseService.update(despesaId, data);
      } else {
        await expenseService.create(id, data);
      }

      navigate(`/viagens/${id}`);
    } catch (err) {
      console.error(err);
      alert(err?.response?.data?.detail || (despesaId ? 'Erro ao atualizar despesa' : 'Erro ao registrar despesa'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8 animate-fade-in py-8 px-4">
      <div className="flex items-center gap-4">
        <button onClick={() => navigate(`/viagens/${id}`)} className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-500">
          <ArrowLeft size={24} />
        </button>
        <h1 className="text-2xl font-bold text-gray-800">{despesaId ? 'Editar Despesa' : 'Registrar Despesa'}</h1>
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-3xl shadow-xl shadow-emerald-100 border border-gray-100 overflow-hidden">
        <div className="p-8 space-y-8">
          {iaToast ? (
            <div className="bg-orange-50 border border-orange-100 text-orange-800 px-4 py-3 rounded-2xl text-sm font-bold">
              {iaToast}
            </div>
          ) : null}
          {iaBannerActive ? (
            <div className="bg-blue-50 border border-blue-100 text-blue-800 px-4 py-3 rounded-2xl text-sm font-bold">
              Dados extraídos pela IA — confira antes de salvar.
            </div>
          ) : null}
          {/* Amount Input */}
          <div className="text-center space-y-2">
            <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest">Valor da Despesa</label>
            <div className="relative inline-block">
              <span className="absolute left-0 top-1/2 -translate-y-1/2 text-3xl font-black text-gray-300">R$</span>
              <input 
                ref={valorInputRef}
                type="number" 
                step="0.01"
                required
                placeholder="0,00"
                title={iaLowConfidence.valor < 0.7 ? 'Verifique este campo' : undefined}
                className={`pl-12 pr-4 py-2 text-5xl font-black text-gray-800 outline-none w-full max-w-[250px] bg-transparent border-b-4 focus:border-emerald-500 transition-colors text-center ${iaLowConfidence.valor < 0.7 ? 'border-yellow-300' : 'border-gray-100'}`}
                value={formData.valor}
                onChange={(e) => {
                  setIaBannerActive(false);
                  setIaLowConfidence((prev) => ({ ...prev, valor: 1 }));
                  setFormData({...formData, valor: e.target.value});
                }}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <label className="flex items-center gap-2 text-sm font-bold text-gray-700 mb-2">
                  <CreditCard size={18} className="text-blue-500" /> Forma de Pagamento
                </label>
                <select 
                  title={iaLowConfidence.forma_pagamento < 0.7 ? 'Verifique este campo' : undefined}
                  className={`w-full px-4 py-3 bg-gray-50 border rounded-2xl outline-none focus:ring-2 focus:ring-blue-500 font-medium ${iaLowConfidence.forma_pagamento < 0.7 ? 'border-yellow-300' : 'border-gray-200'}`}
                  value={formData.forma_pagamento}
                  onChange={(e) => {
                    setIaBannerActive(false);
                    setIaLowConfidence((prev) => ({ ...prev, forma_pagamento: 1 }));
                    setFormData({...formData, forma_pagamento: e.target.value});
                  }}
                >
                  <option>Cartão Corporativo</option>
                  <option>Dinheiro / Reembolso</option>
                  <option>Faturado Empresa</option>
                </select>
              </div>

              <div>
                <label className="flex items-center gap-2 text-sm font-bold text-gray-700 mb-2">
                  <FileText size={18} className="text-blue-500" /> Descrição
                </label>
                <input
                  required
                  type="text"
                  list="expense-desc-options"
                  placeholder="Ex: Almoço, Estacionamento, Combustível..."
                  title={iaLowConfidence.descricao < 0.7 ? 'Verifique este campo' : undefined}
                  className={`w-full px-4 py-3 bg-gray-50 border rounded-2xl outline-none focus:ring-2 focus:ring-blue-500 font-medium ${iaLowConfidence.descricao < 0.7 ? 'border-yellow-300' : 'border-gray-200'}`}
                  value={formData.descricao}
                  onChange={(e) => {
                    setIaBannerActive(false);
                    setIaLowConfidence((prev) => ({ ...prev, descricao: 1 }));
                    setFormData({...formData, descricao: e.target.value});
                  }}
                />
                <datalist id="expense-desc-options">
                  {expenseDescriptionOptions.map((opt) => (
                    <option key={opt} value={opt} />
                  ))}
                </datalist>
              </div>

              {iaAvailable ? (
                <button
                  type="button"
                  disabled={!file || iaLoading || optimizing}
                  onClick={async () => {
                    if (!file) return;
                    setIaToast('');
                    setIaLoading(true);
                    try {
                      const res = await iaService.extrairComprovante(file);
                      const data = res.data || {};

                      const extractedValor = data.valor;
                      const extractedDescricao = data.descricao;
                      const extractedForma = data.forma_pagamento;
                      const hasAnyExtracted =
                        extractedValor !== null && extractedValor !== undefined ||
                        extractedDescricao !== null && extractedDescricao !== undefined ||
                        extractedForma !== null && extractedForma !== undefined;
                      if (!hasAnyExtracted) {
                        setIaToast('A IA não conseguiu extrair os campos desse comprovante. Preencha manualmente.');
                        setTimeout(() => setIaToast(''), 6000);
                        setIaLoading(false);
                        return;
                      }
                      const confianca = data.confianca || {};
                      const formaMap = {
                        DINHEIRO: 'Dinheiro / Reembolso',
                        CARTAO_CREDITO: 'Cartão Corporativo',
                        CARTAO_DEBITO: 'Cartão Corporativo',
                        PIX: 'Dinheiro / Reembolso',
                        OUTRO: 'Faturado Empresa',
                      };
                      const uiForma = extractedForma ? (formaMap[String(extractedForma)] || null) : null;

                      const currentHasAny =
                        String(formData.valor || '').trim() !== '' ||
                        String(formData.descricao || '').trim() !== '' ||
                        String(formData.forma_pagamento || '').trim() !== '';

                      if (currentHasAny) {
                        const ok = window.confirm('Preencher com dados do comprovante e sobrescrever os campos atuais?');
                        if (!ok) {
                          setIaLoading(false);
                          return;
                        }
                      }

                      setFormData((prev) => ({
                        ...prev,
                        valor: extractedValor === null || extractedValor === undefined ? prev.valor : String(extractedValor),
                        descricao: extractedDescricao === null || extractedDescricao === undefined ? prev.descricao : String(extractedDescricao),
                        forma_pagamento: uiForma === null || uiForma === undefined ? prev.forma_pagamento : String(uiForma),
                      }));
                      setIaLowConfidence({
                        valor: Number(confianca.valor ?? 0),
                        descricao: Number(confianca.descricao ?? 0),
                        forma_pagamento: Number(confianca.forma_pagamento ?? 0),
                      });
                      setIaBannerActive(true);
                      if (Array.isArray(data.avisos) && data.avisos.length) {
                        setIaToast(data.avisos.join(' '));
                        setTimeout(() => setIaToast(''), 6000);
                      }
                    } catch (err) {
                      console.error(err);
                      const detail = err?.response?.data?.detail;
                      setIaToast(detail ? String(detail) : 'Não foi possível ler o comprovante, preencha manualmente');
                      setTimeout(() => setIaToast(''), 6000);
                    } finally {
                      setIaLoading(false);
                    }
                  }}
                  className="w-full bg-white border border-gray-200 text-gray-700 px-4 py-3 rounded-2xl font-bold flex items-center justify-center gap-2 hover:bg-gray-50 transition-all shadow-sm disabled:opacity-50"
                >
                  <Sparkles size={18} /> {iaLoading ? 'Extraindo com IA…' : 'Extrair com IA'}
                </button>
              ) : null}
            </div>

            {/* File Upload UX */}
            <div className="space-y-4">
              <label className="flex items-center gap-2 text-sm font-bold text-gray-700 mb-2">
                <Camera size={18} className="text-blue-500" /> Comprovante / Foto {expensePhotoRequired ? '(obrigatório)' : '(opcional)'}
              </label>
              
              <div className="relative group">
                {!preview ? (
                  <div className="flex flex-col gap-3">
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={optimizing}
                        className="flex-1 bg-white border border-gray-200 text-gray-600 px-4 py-2 rounded-xl font-bold flex items-center justify-center gap-2 hover:bg-gray-50 transition-all shadow-sm disabled:opacity-50"
                      >
                        <Upload size={18} /> Anexar
                      </button>
                      <button
                        type="button"
                        onClick={() => cameraInputRef.current?.click()}
                        disabled={optimizing}
                        className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-xl font-bold flex items-center justify-center gap-2 transition-all shadow-lg shadow-blue-100 disabled:opacity-50"
                      >
                        <Camera size={18} /> Câmera
                      </button>
                    </div>

                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={optimizing}
                      className="flex flex-col items-center justify-center w-full h-[200px] md:h-[220px] border-4 border-dashed border-gray-100 rounded-3xl hover:border-blue-200 hover:bg-blue-50 transition-all cursor-pointer group disabled:opacity-50"
                    >
                      <div className="bg-blue-100 p-4 rounded-2xl text-blue-600 mb-3 group-hover:scale-110 transition-transform">
                        <Upload size={32} />
                      </div>
                      <p className="text-sm font-bold text-gray-500">Clique para anexar</p>
                      <p className="text-[10px] text-gray-400 font-medium mt-1 uppercase tracking-widest">PNG, JPG até 10MB</p>
                      <p className="text-[10px] text-gray-400 font-medium mt-1 uppercase tracking-widest">Otimizado automaticamente</p>
                      {optimizing && (
                        <p className="text-xs font-bold text-blue-600 mt-2">Otimizando imagem...</p>
                      )}
                    </button>

                    <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handleFileChange} />
                    <input ref={cameraInputRef} type="file" accept="image/*" capture="environment" className="hidden" onChange={handleFileChange} />
                  </div>
                ) : (
                  <div className="relative w-full h-[240px] md:h-[280px] rounded-3xl overflow-hidden border-4 border-emerald-100 shadow-inner bg-gray-100">
                    <img src={preview} alt="Preview" className="w-full h-full object-cover" />
                    <div className="absolute inset-0 bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <button 
                        type="button" 
                        onClick={() => { setFile(null); setPreview(null); }}
                        className="bg-white/90 p-3 rounded-2xl text-red-600 font-bold flex items-center gap-2 shadow-xl active:scale-95"
                      >
                        <X size={20} /> Remover
                      </button>
                    </div>
                    <div className="absolute bottom-4 left-4 bg-emerald-500 text-white px-3 py-1 rounded-full text-[10px] font-black uppercase flex items-center gap-1 shadow-lg">
                      <CheckCircle size={12} /> Arquivo Selecionado
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          <button 
            type="submit"
            disabled={loading || optimizing}
            className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-bold py-5 rounded-2xl shadow-xl shadow-emerald-200 transition-all active:scale-[0.98] text-lg flex items-center justify-center gap-3"
          >
            {loading ? 'Processando...' : optimizing ? 'Otimizando...' : (
              <>
                <DollarSign size={24} /> {despesaId ? 'Salvar Alterações' : 'Salvar Despesa'}
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default RegistroDespesa;
