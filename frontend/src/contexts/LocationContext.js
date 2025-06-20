import React, { createContext, useContext, useState, useEffect } from 'react';
import toast from 'react-hot-toast';

const LocationContext = createContext();

export const useLocation = () => {
  const context = useContext(LocationContext);
  if (!context) {
    throw new Error('useLocation must be used within a LocationProvider');
  }
  return context;
};

export const LocationProvider = ({ children }) => {
  const [currentLocation, setCurrentLocation] = useState(null);
  const [locationPermission, setLocationPermission] = useState('prompt');
  const [loading, setLoading] = useState(false);

  const getCurrentLocation = () => {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation is not supported'));
        return;
      }

      setLoading(true);
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const location = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy
          };
          setCurrentLocation(location);
          setLocationPermission('granted');
          setLoading(false);
          resolve(location);
        },
        (error) => {
          setLocationPermission('denied');
          setLoading(false);
          let message = '위치 정보를 가져올 수 없습니다.';
          
          switch (error.code) {
            case error.PERMISSION_DENIED:
              message = '위치 권한이 거부되었습니다.';
              break;
            case error.POSITION_UNAVAILABLE:
              message = '위치 정보를 사용할 수 없습니다.';
              break;
            case error.TIMEOUT:
              message = '위치 요청 시간이 초과되었습니다.';
              break;
          }
          
          toast.error(message);
          reject(new Error(message));
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 300000
        }
      );
    });
  };

  const watchLocation = (callback) => {
    if (!navigator.geolocation) {
      toast.error('위치 서비스가 지원되지 않습니다.');
      return null;
    }

    return navigator.geolocation.watchPosition(
      (position) => {
        const location = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy
        };
        setCurrentLocation(location);
        callback(location);
      },
      (error) => {
        console.error('Location watch error:', error);
      },
      {
        enableHighAccuracy: true,
        timeout: 5000,
        maximumAge: 60000
      }
    );
  };

  useEffect(() => {
    // 컴포넌트 마운트 시 위치 권한 확인
    if (navigator.permissions) {
      navigator.permissions.query({ name: 'geolocation' }).then((result) => {
        setLocationPermission(result.state);
        
        if (result.state === 'granted') {
          getCurrentLocation().catch(() => {});
        }
      });
    }
  }, []);

  const value = {
    currentLocation,
    locationPermission,
    loading,
    getCurrentLocation,
    watchLocation
  };

  return (
    <LocationContext.Provider value={value}>
      {children}
    </LocationContext.Provider>
  );
};