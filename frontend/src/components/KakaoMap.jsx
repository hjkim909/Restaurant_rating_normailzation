import React, { useState } from 'react';
import { Map, MapMarker, CustomOverlayMap, useKakaoLoader } from 'react-kakao-maps-sdk';
import { AlertTriangle } from 'lucide-react';

export default function KakaoMap({ center, items, className, userLocation }) {
    // Try to load the script. 
    // NOTE: This might fail if the key is missing in .env
    const [loading, error] = useKakaoLoader({
        appkey: import.meta.env.VITE_KAKAO_JS_KEY || "YOUR_KAKAO_JS_KEY_HERE",
        libraries: ["services", "clusterer"],
    });

    const [selectedMarker, setSelectedMarker] = useState(null);

    const isKakaoReady = typeof window !== 'undefined' && window.kakao && window.kakao.maps;

    if (!import.meta.env.VITE_KAKAO_JS_KEY && !isKakaoReady) {
        return (
            <div className={`flex flex-col items-center justify-center bg-gray-100 rounded-xl p-6 text-center shadow-inner border border-gray-200 ${className}`} style={{ height: '300px' }}>
                <AlertTriangle className="w-10 h-10 text-yellow-500 mb-2" />
                <h3 className="text-lg font-bold text-gray-800">지도를 불러올 수 없습니다</h3>
                <p className="text-sm text-gray-600 mt-1">.env 파일에 VITE_KAKAO_JS_KEY를 설정해주세요.</p>
            </div>
        );
    }

    if (loading && !isKakaoReady) return <div className={`bg-gray-100 animate-pulse rounded-2xl ${className}`} style={{ height: '300px' }} />;
    if (error && !isKakaoReady) {
        console.error("Kakao Map Load Error:", error);
        return (
            <div className={`flex flex-col items-center justify-center bg-gray-100 rounded-xl p-6 text-center ${className}`} style={{ height: '300px' }}>
                <p className="text-red-500">지도를 로드하는 중 오류가 발생했습니다.</p>
                <p className="text-xs text-red-400 mt-2">브라우저 콘솔(F12)을 확인해주세요.</p>
            </div>
        );
    }

    return (
        <Map
            center={center || { lat: 37.5665, lng: 126.9780 }}
            style={{ width: "100%", height: "300px", borderRadius: "16px" }}
            level={3}
            className={className}
        >
            {items.map((item) => (
                item.lat && item.lng ? (
                    <MapMarker
                        key={`${item.title}-${item.lat}-${item.lng}`}
                        position={{ lat: item.lat, lng: item.lng }}
                        onClick={() => setSelectedMarker(item)}
                        clickable={true}
                    >
                        {selectedMarker === item && (
                            <a
                                href={item.link || `https://map.naver.com/v5/search/${encodeURIComponent(item.title.replace(/<[^>]*>?/gm, ''))}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                onClick={(e) => e.stopPropagation()}
                                style={{ padding: "8px 12px", color: "#ea580c", fontWeight: "bold", display: "block", textDecoration: "underline" }}
                            >
                                {item.title.replace(/<[^>]*>?/gm, '')} →
                            </a>
                        )}
                    </MapMarker>
                ) : null
            ))}

            {/* Current Location Marker */}
            {/* Current Location Marker (Modern Style) */}
            {userLocation && (
                <CustomOverlayMap position={userLocation} yAnchor={0.5} zIndex={100}>
                    <div className="relative flex items-center justify-center w-8 h-8">
                        {/* Pulse Effect */}
                        <div className="absolute w-full h-full bg-blue-500 rounded-full opacity-30 animate-ping"></div>
                        {/* Core Dot */}
                        <div className="relative w-4 h-4 bg-blue-600 border-2 border-white rounded-full shadow-md"></div>
                        {/* Label */}
                        <div className="absolute top-6 left-1/2 -translate-x-1/2 whitespace-nowrap bg-gray-900/80 text-white text-[10px] px-2 py-0.5 rounded-full font-bold backdrop-blur-sm">
                            내 위치
                        </div>
                    </div>
                </CustomOverlayMap>
            )}
        </Map>
    );
}
