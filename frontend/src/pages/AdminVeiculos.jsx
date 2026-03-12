import React, { useState, useEffect, useCallback } from 'react';
import { vehicleService } from '../services/api';
import { Car, Plus, X, Tag, Hash, Calendar, Pencil, Trash2 } from 'lucide-react';

const AdminVeiculos = () => {
  const [vehicles, setVehicles] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [editingVehicle, setEditingVehicle] = useState(null);
  const [formData, setFormData] = useState({
    placa: '',
    modelo: '',
    marca: '',
    ano: new Date().getFullYear()
  });

  const fetchVehicles = useCallback(async () => {
    try {
      const response = await vehicleService.list();
      setVehicles(response.data);
    } catch (err) {
      console.error(err);
    }
  }, []);

  useEffect(() => {
    fetchVehicles();
  }, [fetchVehicles]);

  const resetForm = () => {
    setFormData({ placa: '', modelo: '', marca: '', ano: new Date().getFullYear() });
  };

  const openCreate = () => {
    setEditingVehicle(null);
    resetForm();
    setShowModal(true);
  };

  const openEdit = (vehicle) => {
    setEditingVehicle(vehicle);
    setFormData({
      placa: vehicle.placa || '',
      modelo: vehicle.modelo || '',
      marca: vehicle.marca || '',
      ano: vehicle.ano || new Date().getFullYear(),
    });
    setShowModal(true);
  };

  const handleDelete = async (vehicle) => {
    const ok = window.confirm(`Excluir o veículo "${vehicle.placa}"?`);
    if (!ok) return;

    try {
      await vehicleService.remove(vehicle.id);
      fetchVehicles();
    } catch (err) {
      console.error(err);
      alert(err?.response?.data?.detail || 'Erro ao excluir veículo');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingVehicle) {
        await vehicleService.update(editingVehicle.id, formData);
      } else {
        await vehicleService.create(formData);
      }

      setShowModal(false);
      setEditingVehicle(null);
      fetchVehicles();
      resetForm();
    } catch (err) {
      console.error(err);
      alert(err?.response?.data?.detail || (editingVehicle ? 'Erro ao atualizar veículo' : 'Erro ao cadastrar veículo'));
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Frota de Veículos</h1>
          <p className="text-gray-500 font-medium">Gestão de veículos disponíveis para viagens.</p>
        </div>
        <button 
          onClick={openCreate}
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-bold shadow-lg shadow-blue-200 flex items-center gap-2"
        >
          <Plus size={20} /> Novo Veículo
        </button>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {vehicles.map(vehicle => (
          <div key={vehicle.id} className="bg-white p-6 rounded-3xl shadow-sm border border-gray-100 flex items-start gap-4 hover:shadow-md transition-shadow group">
            <div className="p-4 bg-gray-50 rounded-2xl text-gray-400 group-hover:bg-blue-50 group-hover:text-blue-600 transition-colors">
              <Car size={32} />
            </div>
            <div className="flex-1">
              <div className="flex justify-between items-start mb-1 gap-3">
                <div>
                  <h3 className="font-black text-gray-800 text-lg uppercase tracking-tight">{vehicle.placa}</h3>
                  <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">{vehicle.ano}</p>
                </div>
                <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    type="button"
                    onClick={() => openEdit(vehicle)}
                    className="p-2 rounded-xl border border-gray-200 text-gray-600 hover:bg-gray-50 hover:text-blue-600 transition-colors"
                    aria-label="Editar"
                  >
                    <Pencil size={16} />
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDelete(vehicle)}
                    className="p-2 rounded-xl border border-gray-200 text-gray-600 hover:bg-red-50 hover:text-red-600 transition-colors"
                    aria-label="Excluir"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
              <p className="text-sm font-bold text-gray-600">{vehicle.modelo}</p>
              <p className="text-xs text-gray-400 font-medium">{vehicle.marca}</p>
            </div>
          </div>
        ))}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl shadow-2xl max-w-md w-full animate-scale-up overflow-hidden">
            <div className="p-6 bg-blue-600 text-white flex justify-between items-center">
              <h2 className="text-xl font-bold">{editingVehicle ? 'Editar Veículo' : 'Novo Veículo'}</h2>
              <button onClick={() => { setShowModal(false); setEditingVehicle(null); }} className="hover:bg-white/20 p-2 rounded-lg transition-colors"><X size={24} /></button>
            </div>
            
            <form onSubmit={handleSubmit} className="p-8 space-y-6">
              <div className="space-y-4">
                <div className="relative">
                  <Hash className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                  <input 
                    type="text" required placeholder="Placa (Ex: ABC-1234)"
                    className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500 uppercase font-bold"
                    value={formData.placa}
                    onChange={(e) => setFormData({...formData, placa: e.target.value})}
                  />
                </div>
                <div className="relative">
                  <Tag className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                  <input 
                    type="text" required placeholder="Modelo (Ex: Corolla)"
                    className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500"
                    value={formData.modelo}
                    onChange={(e) => setFormData({...formData, modelo: e.target.value})}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="relative">
                    <Car className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                    <input 
                      type="text" required placeholder="Marca"
                      className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500"
                      value={formData.marca}
                      onChange={(e) => setFormData({...formData, marca: e.target.value})}
                    />
                  </div>
                  <div className="relative">
                    <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                    <input 
                      type="number" required placeholder="Ano"
                      className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500"
                      value={formData.ano}
                      onChange={(e) => setFormData({...formData, ano: parseInt(e.target.value)})}
                    />
                  </div>
                </div>
              </div>

              <button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-xl shadow-lg shadow-blue-200 transition-all active:scale-[0.98]">
                {editingVehicle ? 'Salvar Alterações' : 'Cadastrar Veículo'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminVeiculos;
