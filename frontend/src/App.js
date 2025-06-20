import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { LocationProvider } from './contexts/LocationContext';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import MapView from './pages/MapView';
import VoiceAssistant from './pages/VoiceAssistant';
import ImageAnalyzer from './pages/ImageAnalyzer';
import './App.css';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }
  
  return user ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <AuthProvider>
      <LocationProvider>
        <Router>
          <div className="App min-h-screen bg-gray-50">
            <Navbar />
            <main className="container mx-auto px-4 py-8">
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="/dashboard" element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                } />
                <Route path="/map" element={
                  <ProtectedRoute>
                    <MapView />
                  </ProtectedRoute>
                } />
                <Route path="/voice" element={
                  <ProtectedRoute>
                    <VoiceAssistant />
                  </ProtectedRoute>
                } />
                <Route path="/analyze" element={
                  <ProtectedRoute>
                    <ImageAnalyzer />
                  </ProtectedRoute>
                } />
              </Routes>
            </main>
            <Toaster position="top-right" />
          </div>
        </Router>
      </LocationProvider>
    </AuthProvider>
  );
}

export default App;