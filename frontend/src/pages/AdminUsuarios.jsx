import React, { useState, useEffect, useCallback } from 'react';
import { userService } from '../services/api';
import { Plus, X, Mail, Shield, User, Pencil, Trash2 } from 'lucide-react';

const AdminUsuarios = () => {
  const [users, setUsers] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [formData, setFormData] = useState({
    nome: '',
    email: '',
    senha: '',
    tipousuario: 'colaborador',
    tem_cnh: false
  });

  const fetchUsers = useCallback(async () => {
    try {
      const response = await userService.list();
      setUsers(response.data);
    } catch (err) {
      console.error(err);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const resetForm = () => {
    setFormData({ nome: '', email: '', senha: '', tipousuario: 'colaborador', tem_cnh: false });
  };

  const openCreate = () => {
    setEditingUser(null);
    resetForm();
    setShowModal(true);
  };

  const openEdit = (user) => {
    setEditingUser(user);
    setFormData({
      nome: user.nome || '',
      email: user.email || '',
      senha: '',
      tipousuario: user.tipousuario || 'colaborador',
      tem_cnh: !!user.tem_cnh,
    });
    setShowModal(true);
  };

  const handleDelete = async (user) => {
    const ok = window.confirm(`Excluir o usuário "${user.nome}"?`);
    if (!ok) return;

    try {
      await userService.remove(user.id);
      fetchUsers();
    } catch (err) {
      console.error(err);
      alert(err?.response?.data?.detail || 'Erro ao excluir usuário');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingUser) {
        const payload = { ...formData };
        if (!payload.senha) delete payload.senha;
        await userService.update(editingUser.id, payload);
      } else {
        await userService.create(formData);
      }

      setShowModal(false);
      setEditingUser(null);
      fetchUsers();
      resetForm();
    } catch (err) {
      console.error(err);
      alert(err?.response?.data?.detail || (editingUser ? 'Erro ao atualizar usuário' : 'Erro ao criar usuário'));
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Gerenciar Usuários</h1>
          <p className="text-gray-500 font-medium">Controle de acesso e perfis do sistema.</p>
        </div>
        <button 
          onClick={openCreate}
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-bold shadow-lg shadow-blue-200 flex items-center justify-center gap-2 w-full sm:w-auto"
        >
          <Plus size={20} /> Novo Usuário
        </button>
      </header>

      <div className="md:hidden space-y-3">
        {users.map((u) => (
          <div key={u.id} className="bg-white p-4 rounded-2xl shadow-sm border border-gray-100">
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600 font-bold uppercase shrink-0">
                  {u.nome?.[0]}
                </div>
                <div className="min-w-0">
                  <p className="font-bold text-gray-800 truncate">{u.nome}</p>
                  <p className="text-sm text-gray-500 truncate">{u.email}</p>
                </div>
              </div>
              <div className="flex gap-2 shrink-0">
                <button
                  type="button"
                  onClick={() => openEdit(u)}
                  className="p-2 rounded-xl border border-gray-200 text-gray-600 hover:bg-gray-50 hover:text-blue-600 transition-colors"
                  aria-label="Editar"
                >
                  <Pencil size={16} />
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(u)}
                  className="p-2 rounded-xl border border-gray-200 text-gray-600 hover:bg-red-50 hover:text-red-600 transition-colors"
                  aria-label="Excluir"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between gap-3 mt-4">
              <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider ${u.tipousuario === 'admin' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'}`}>
                {u.tipousuario}
              </span>
              {u.tem_cnh ? (
                <span className="bg-emerald-100 text-emerald-700 px-2 py-1 rounded-lg text-[10px] font-black uppercase">CNH: Sim</span>
              ) : (
                <span className="bg-gray-100 text-gray-400 px-2 py-1 rounded-lg text-[10px] font-black uppercase">CNH: Não</span>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="hidden md:block bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left min-w-[800px]">
            <thead className="bg-gray-50 text-gray-400 font-bold uppercase text-[10px] tracking-widest">
              <tr>
                <th className="px-6 py-4">Usuário</th>
                <th className="px-6 py-4">E-mail</th>
                <th className="px-6 py-4">Perfil</th>
                <th className="px-6 py-4 text-center">CNH</th>
                <th className="px-6 py-4 text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {users.map(user => (
                <tr key={user.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600 font-bold uppercase">
                        {user.nome[0]}
                      </div>
                      <span className="font-bold text-gray-700">{user.nome}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-gray-500 font-medium">{user.email}</td>
                  <td className="px-6 py-4">
                    <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider ${user.tipousuario === 'admin' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'}`}>
                      {user.tipousuario}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    {user.tem_cnh ? (
                      <span className="bg-emerald-100 text-emerald-700 px-2 py-1 rounded-lg text-[10px] font-black uppercase">Sim</span>
                    ) : (
                      <span className="bg-gray-100 text-gray-400 px-2 py-1 rounded-lg text-[10px] font-black uppercase">Não</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex justify-end gap-2">
                      <button
                        type="button"
                        onClick={() => openEdit(user)}
                        className="p-2 rounded-xl border border-gray-200 text-gray-600 hover:bg-gray-50 hover:text-blue-600 transition-colors"
                        aria-label="Editar"
                      >
                        <Pencil size={16} />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(user)}
                        className="p-2 rounded-xl border border-gray-200 text-gray-600 hover:bg-red-50 hover:text-red-600 transition-colors"
                        aria-label="Excluir"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl shadow-2xl max-w-md w-full animate-scale-up overflow-hidden">
            <div className="p-6 bg-blue-600 text-white flex justify-between items-center">
              <h2 className="text-xl font-bold">{editingUser ? 'Editar Usuário' : 'Novo Usuário'}</h2>
              <button onClick={() => { setShowModal(false); setEditingUser(null); }} className="hover:bg-white/20 p-2 rounded-lg transition-colors"><X size={24} /></button>
            </div>
            
            <form onSubmit={handleSubmit} className="p-8 space-y-6">
              <div className="space-y-4">
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                  <input 
                    type="text" required placeholder="Nome Completo"
                    className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500"
                    value={formData.nome}
                    onChange={(e) => setFormData({...formData, nome: e.target.value})}
                  />
                </div>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                  <input 
                    type="email" required placeholder="E-mail"
                    className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                  />
                </div>
                <div className="relative">
                  <Shield className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                  <input 
                    type="password" required={!editingUser} placeholder={editingUser ? 'Nova senha (opcional)' : 'Senha Inicial'}
                    className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500"
                    value={formData.senha}
                    onChange={(e) => setFormData({...formData, senha: e.target.value})}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Perfil</label>
                    <select 
                      className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500"
                      value={formData.tipousuario}
                      onChange={(e) => setFormData({...formData, tipousuario: e.target.value})}
                    >
                      <option value="colaborador">Colaborador</option>
                      <option value="admin">Administrador</option>
                    </select>
                  </div>
                  <div className="flex flex-col">
                    <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Possui CNH?</label>
                    <label className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl cursor-pointer border border-gray-200">
                      <input 
                        type="checkbox"
                        checked={formData.tem_cnh}
                        onChange={(e) => setFormData({...formData, tem_cnh: e.target.checked})}
                        className="rounded text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm font-bold text-gray-700">Sim</span>
                    </label>
                  </div>
                </div>
              </div>

              <button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-xl shadow-lg shadow-blue-200 transition-all active:scale-[0.98]">
                {editingUser ? 'Salvar Alterações' : 'Criar Usuário'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminUsuarios;
