import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { useAuth } from './hooks/useAuth';
import Layout from './components/Layout';
import Login from './pages/Login';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const Viagens = lazy(() => import('./pages/Viagens'));
const DetalhesViagem = lazy(() => import('./pages/DetalhesViagem'));
const EditarViagem = lazy(() => import('./pages/EditarViagem'));
const RegistroSaida = lazy(() => import('./pages/RegistroSaida'));
const RegistroChegada = lazy(() => import('./pages/RegistroChegada'));
const ControleTempo = lazy(() => import('./pages/ControleTempo'));
const RegistroDespesa = lazy(() => import('./pages/RegistroDespesa'));
const AdminUsuarios = lazy(() => import('./pages/AdminUsuarios'));
const AdminVeiculos = lazy(() => import('./pages/AdminVeiculos'));
const AdminIA = lazy(() => import('./pages/AdminIA'));
const RelatorioViagem = lazy(() => import('./pages/RelatorioViagem'));
const Configuracoes = lazy(() => import('./pages/Configuracoes'));

const PrivateRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <div>Carregando...</div>;
  return user ? <Layout>{children}</Layout> : <Navigate to="/login" />;
};

const AppRoutes = () => {
  const { iaEnabled } = useAuth();
  return (
    <Suspense fallback={<div>Carregando...</div>}>
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
        {iaEnabled ? <Route path="/admin/ia" element={<PrivateRoute><AdminIA /></PrivateRoute>} /> : null}
        <Route path="/admin/configuracoes" element={<PrivateRoute><Configuracoes /></PrivateRoute>} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Suspense>
  );
};

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  );
}

export default App;
