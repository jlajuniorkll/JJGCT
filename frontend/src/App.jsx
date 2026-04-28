import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { useAuth } from './hooks/useAuth';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Viagens from './pages/Viagens';
import DetalhesViagem from './pages/DetalhesViagem';
import EditarViagem from './pages/EditarViagem';
import RegistroSaida from './pages/RegistroSaida';
import RegistroChegada from './pages/RegistroChegada';
import ControleTempo from './pages/ControleTempo';
import RegistroDespesa from './pages/RegistroDespesa';
import AdminUsuarios from './pages/AdminUsuarios';
import AdminVeiculos from './pages/AdminVeiculos';
import AdminIA from './pages/AdminIA';
import RelatorioViagem from './pages/RelatorioViagem';
import Configuracoes from './pages/Configuracoes';

const PrivateRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <div>Carregando...</div>;
  return user ? <Layout>{children}</Layout> : <Navigate to="/login" />;
};

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
          <Route path="/viagens" element={<PrivateRoute><Viagens /></PrivateRoute>} />
          <Route path="/viagens/:id" element={<PrivateRoute><DetalhesViagem /></PrivateRoute>} />
          <Route path="/viagens/:id/editar" element={<PrivateRoute><EditarViagem /></PrivateRoute>} />
          <Route path="/viagens/:id/saida" element={<PrivateRoute><RegistroSaida /></PrivateRoute>} />
          <Route path="/viagens/:id/chegada" element={<PrivateRoute><RegistroChegada /></PrivateRoute>} />
          <Route path="/viagens/:id/tempo" element={<PrivateRoute><ControleTempo /></PrivateRoute>} />
          <Route path="/viagens/:id/tempo/:atividadeId" element={<PrivateRoute><ControleTempo /></PrivateRoute>} />
          <Route path="/viagens/:id/despesa" element={<PrivateRoute><RegistroDespesa /></PrivateRoute>} />
          <Route path="/viagens/:id/despesa/:despesaId" element={<PrivateRoute><RegistroDespesa /></PrivateRoute>} />
          <Route path="/viagens/:id/relatorio" element={<PrivateRoute><RelatorioViagem /></PrivateRoute>} />
          <Route path="/admin/usuarios" element={<PrivateRoute><AdminUsuarios /></PrivateRoute>} />
          <Route path="/admin/veiculos" element={<PrivateRoute><AdminVeiculos /></PrivateRoute>} />
          <Route path="/admin/ia" element={<PrivateRoute><AdminIA /></PrivateRoute>} />
          <Route path="/admin/configuracoes" element={<PrivateRoute><Configuracoes /></PrivateRoute>} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
