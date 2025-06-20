import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useForm } from 'react-hook-form';
import { Mail, Lock, User, Eye, EyeOff } from 'lucide-react';

const Register = () => {
  const { register: registerUser } = useAuth();
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  const { register, handleSubmit, formState: { errors }, watch } = useForm();
  const password = watch('password');

  const onSubmit = async (data) => {
    setIsLoading(true);
    const result = await registerUser({
      email: data.email,
      username: data.username,
      full_name: data.fullName,
      password: data.password
    });
    
    if (result.success) {
      navigate('/dashboard');
    }
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 bg-blue-600 rounded-full flex items-center justify-center">
            <span className="text-white font-bold text-xl">S</span>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            새 계정 만들기
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            또는{' '}
            <Link to="/login" className="font-medium text-blue-600 hover:text-blue-500">
              기존 계정으로 로그인
            </Link>
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
          <div className="space-y-4">
            <div>
              <label htmlFor="fullName" className="block text-sm font-medium text-gray-700 mb-1">
                이름
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  {...register('fullName', { required: '이름을 입력해주세요.' })}
                  type="text"
                  className="appearance-none rounded-md relative block w-full pl-10 pr-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="이름"
                />
              </div>
              {errors.fullName && (
                <p className="text-gray-600 mt-1">
              오늘도 안전한 하루 되세요. 실시간 위험도를 확인해보세요.
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={handleGetLocation}
              className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              <MapPin size={18} />
              <span>현재 위치</span>
            </button>
          </div>
        </div>
      </div>

      {/* 현재 위치 위험도 */}
      {currentLocation && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
            <Activity className="mr-2" size={20} />
            현재 위치 위험도
          </h2>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <div className="flex items-center space-x-2 mb-2">
                <MapPin size={16} className="text-gray-500" />
                <span className="text-sm text-gray-600">
                  위도: {currentLocation.latitude.toFixed(6)}, 
                  경도: {currentLocation.longitude.toFixed(6)}
                </span>
              </div>
              
              {currentRisk && (
                <div className="mt-4">
                  <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(currentRisk.probability)}`}>
                    <AlertTriangle size={16} className="mr-1" />
                    위험도: {getRiskText(currentRisk.probability)} ({(currentRisk.probability * 100).toFixed(1)}%)
                  </div>
                  
                  {currentRisk.factors && (
                    <div className="mt-4">
                      <h4 className="font-medium text-gray-900 mb-2">위험 요소:</h4>
                      <ul className="space-y-1">
                        {currentRisk.factors.map((factor, index) => (
                          <li key={index} className="text-sm text-gray-600 flex items-center">
                            <div className="w-2 h-2 bg-gray-400 rounded-full mr-2"></div>
                            {factor}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
            
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-medium text-gray-900 mb-2">안전 수칙</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• 도로 상태를 주의 깊게 살펴보세요</li>
                <li>• 의심스러운 균열이나 침하를 발견하면 신고하세요</li>
                <li>• 위험지역은 우회해서 이동하세요</li>
                <li>• 비 온 후에는 특히 주의하세요</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* 통계 카드들 */}
      <div className="grid md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">총 검색 횟수</p>
              <p className="text-2xl font-bold text-gray-900">
                {dashboardData?.recent_searches?.length || 0}
              </p>
            </div>
            <TrendingUp className="h-8 w-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">이미지 분석</p>
              <p className="text-2xl font-bold text-gray-900">
                {dashboardData?.reports?.length || 0}
              </p>
            </div>
            <Camera className="h-8 w-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">평균 위험도</p>
              <p className="text-2xl font-bold text-gray-900">
                {dashboardData?.recent_searches?.length > 0 
                  ? (dashboardData.recent_searches.reduce((sum, search) => sum + (search.risk_probability || 0), 0) / dashboardData.recent_searches.length * 100).toFixed(1)
                  : 0}%
              </p>
            </div>
            <AlertTriangle className="h-8 w-8 text-orange-500" />
          </div>
        </div>
      </div>

      {/* 최근 검색 기록 */}
      <div className="grid lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
            <Clock className="mr-2" size={20} />
            최근 검색 기록
          </h2>
          
          {dashboardData?.recent_searches?.length > 0 ? (
            <div className="space-y-3">
              {dashboardData.recent_searches.slice(0, 5).map((search) => (
                <div key={search.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {search.latitude.toFixed(4)}, {search.longitude.toFixed(4)}
                    </div>
                    <div className="text-xs text-gray-500">
                      {new Date(search.searched_at).toLocaleString('ko-KR')}
                    </div>
                  </div>
                  <div className={`px-2 py-1 rounded text-xs font-medium ${getRiskColor(search.risk_probability || 0)}`}>
                    {getRiskText(search.risk_probability || 0)}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">검색 기록이 없습니다.</p>
          )}
        </div>

        {/* 이미지 분석 기록 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
            <Camera className="mr-2" size={20} />
            이미지 분석 기록
          </h2>
          
          {dashboardData?.reports?.length > 0 ? (
            <div className="space-y-3">
              {dashboardData.reports.map((report) => (
                <div key={report.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      분석 ID: {report.id}
                    </div>
                    <div className="text-xs text-gray-500">
                      {new Date(report.created_at).toLocaleString('ko-KR')}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`px-2 py-1 rounded text-xs font-medium ${getRiskColor(report.confidence || 0)}`}>
                      신뢰도: {((report.confidence || 0) * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      상태: {report.status === 'pending' ? '대기중' : 
                             report.status === 'verified' ? '확인됨' : '오탐지'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">분석 기록이 없습니다.</p>
          )}
        </div>
      </div>

      {/* 긴급 연락처 */}
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-red-800 mb-4 flex items-center">
          <AlertTriangle className="mr-2" size={20} />
          긴급 연락처
        </h2>
        
        <div className="grid md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg p-4 text-center">
            <h3 className="font-semibold text-red-800 mb-1">서울시 다산콜센터</h3>
            <p className="text-2xl font-bold text-red-600">120</p>
            <p className="text-sm text-gray-600">일반 신고</p>
          </div>
          <div className="bg-white rounded-lg p-4 text-center">
            <h3 className="font-semibold text-red-800 mb-1">소방서</h3>
            <p className="text-2xl font-bold text-red-600">119</p>
            <p className="text-sm text-gray-600">응급상황</p>
          </div>
          <div className="bg-white rounded-lg p-4 text-center">
            <h3 className="font-semibold text-red-800 mb-1">경찰서</h3>
            <p className="text-2xl font-bold text-red-600">112</p>
            <p className="text-sm text-gray-600">교통통제</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;