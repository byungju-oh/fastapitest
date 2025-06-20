import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Home, Map, Mic, Camera, User, LogOut } from 'lucide-react';

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="bg-blue-600 text-white shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center">
              <span className="text-blue-600 font-bold">S</span>
            </div>
            <span className="text-xl font-bold">싱크홀 안전 서비스</span>
          </Link>

          <div className="flex items-center space-x-4">
            {user ? (
              <>
                <Link 
                  to="/dashboard" 
                  className={`flex items-center space-x-1 px-3 py-2 rounded-md transition-colors ${
                    isActive('/dashboard') ? 'bg-blue-700' : 'hover:bg-blue-500'
                  }`}
                >
                  <Home size={18} />
                  <span>대시보드</span>
                </Link>
                
                <Link 
                  to="/map" 
                  className={`flex items-center space-x-1 px-3 py-2 rounded-md transition-colors ${
                    isActive('/map') ? 'bg-blue-700' : 'hover:bg-blue-500'
                  }`}
                >
                  <Map size={18} />
                  <span>지도</span>
                </Link>
                
                <Link 
                  to="/voice" 
                  className={`flex items-center space-x-1 px-3 py-2 rounded-md transition-colors ${
                    isActive('/voice') ? 'bg-blue-700' : 'hover:bg-blue-500'
                  