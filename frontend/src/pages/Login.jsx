import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { authService } from '../services/api';
import { MapPin, Mail, Lock, AlertCircle } from 'lucide-react';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await authService.login(email, password);
      login(response.data);
      navigate('/');
    } catch (error) {
      console.error(error);
      if (error?.response?.status === 401) {
        setError('E-mail ou senha inválidos.');
      } else {
        setError('Erro ao conectar com o servidor.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8">
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center text-white mb-4 shadow-lg shadow-blue-200">
            <MapPin size={32} />
          </div>
          <h1 className="text-2xl font-bold text-gray-800">Corporate Travel</h1>
          <p className="text-gray-500">Acesse sua conta para continuar</p>
        </div>

        {error && (
          <div className="bg-red-50 text-red-600 p-4 rounded-lg mb-6 flex items-center gap-3 border border-red-100 animate-shake">
            <AlertCircle size={20} />
            <span className="text-sm font-medium">{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">E-mail</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-gray-800"
                placeholder="seu@email.com"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">Senha</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-gray-800"
                placeholder="••••••••"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-xl shadow-lg shadow-blue-200 transition-all active:scale-[0.98] disabled:opacity-50"
          >
            {loading ? 'Carregando...' : 'Entrar'}
          </button>
        </form>

        <p className="mt-8 text-center text-sm text-gray-500">
          Não tem uma conta? <span className="text-blue-600 font-bold">Contate o administrador</span>
        </p>
      </div>
    </div>
  );
};

export default Login;
