import React, { useState } from 'react';
import { Loader2, Ticket, RefreshCw, Store, UtensilsCrossed, Search } from 'lucide-react';
import KakaoMap from './KakaoMap';
import ShareButton from './ShareButton';

// 메뉴 카테고리 목록 (랜덤 뽑기용)
const MENU_CATEGORIES = [
    { name: '돈까스', emoji: '🍛' },
    { name: '냉면', emoji: '🍜' },
    { name: '파스타', emoji: '🍝' },
    { name: '삼겹살', emoji: '🥓' },
    { name: '초밥', emoji: '🍣' },
    { name: '짜장면', emoji: '🍜' },
    { name: '김치찌개', emoji: '🍲' },
    { name: '햄버거', emoji: '🍔' },
    { name: '치킨', emoji: '🍗' },
    { name: '쌀국수', emoji: '🍜' },
    { name: '라멘', emoji: '🍜' },
    { name: '비빔밥', emoji: '🍚' },
    { name: '떡볶이', emoji: '🌶️' },
    { name: '피자', emoji: '🍕' },
    { name: '샐러드', emoji: '🥗' },
    { name: '카레', emoji: '🍛' },
    { name: '칼국수', emoji: '🍜' },
    { name: '순대국', emoji: '🍲' },
    { name: '부대찌개', emoji: '🍲' },
    { name: '곱창', emoji: '🥘' },
];

export default function RandomPicker({ items, userLocation, onSearchMenu }) {
    const [mode, setMode] = useState('restaurant'); // 'restaurant' | 'menu'
    const [selectedItem, setSelectedItem] = useState(null);
    const [selectedMenu, setSelectedMenu] = useState(null);
    const [isAnimating, setIsAnimating] = useState(false);

    // 가게 랜덤 뽑기
    const handlePickRestaurant = () => {
        if (!items || items.length === 0) return;

        setIsAnimating(true);
        setSelectedItem(null);

        let count = 0;
        const maxCount = 20;
        const interval = setInterval(() => {
            const randomIndex = Math.floor(Math.random() * items.length);
            setSelectedItem(items[randomIndex]);
            count++;

            if (count >= maxCount) {
                clearInterval(interval);
                setIsAnimating(false);
            }
        }, 100);
    };

    // 메뉴 랜덤 뽑기
    const handlePickMenu = () => {
        setIsAnimating(true);
        setSelectedMenu(null);

        let count = 0;
        const maxCount = 20;
        const interval = setInterval(() => {
            const randomIndex = Math.floor(Math.random() * MENU_CATEGORIES.length);
            setSelectedMenu(MENU_CATEGORIES[randomIndex]);
            count++;

            if (count >= maxCount) {
                clearInterval(interval);
                setIsAnimating(false);
            }
        }, 100);
    };

    // 선택된 메뉴로 검색
    const handleSearchWithMenu = () => {
        if (selectedMenu && onSearchMenu) {
            onSearchMenu(selectedMenu.name);
            setSelectedMenu(null);
        }
    };

    // 리셋
    const handleReset = () => {
        setSelectedItem(null);
        setSelectedMenu(null);
    };

    return (
        <div className="mb-4">
            {/* 탭 UI */}
            <div className="flex mb-3 bg-gray-100 rounded-lg p-1">
                <button
                    onClick={() => { setMode('restaurant'); handleReset(); }}
                    className={`flex-1 py-2 px-3 rounded-md text-sm font-bold flex items-center justify-center gap-1.5 transition-colors ${mode === 'restaurant'
                        ? 'bg-white text-orange-600 shadow-sm'
                        : 'text-gray-500 hover:text-gray-700'
                        }`}
                >
                    <Store className="w-4 h-4" />
                    가게 뽑기
                </button>
                <button
                    onClick={() => { setMode('menu'); handleReset(); }}
                    className={`flex-1 py-2 px-3 rounded-md text-sm font-bold flex items-center justify-center gap-1.5 transition-colors ${mode === 'menu'
                        ? 'bg-white text-orange-600 shadow-sm'
                        : 'text-gray-500 hover:text-gray-700'
                        }`}
                >
                    <UtensilsCrossed className="w-4 h-4" />
                    메뉴 뽑기
                </button>
            </div>

            {/* 가게 뽑기 모드 */}
            {mode === 'restaurant' && (
                <>
                    {!selectedItem && !isAnimating && (
                        <button
                            onClick={handlePickRestaurant}
                            disabled={!items.length}
                            className="w-full bg-gradient-to-r from-orange-500 to-amber-500 text-white py-3.5 rounded-2xl font-bold text-lg shadow-lg shadow-orange-500/20 hover:shadow-orange-500/40 hover:-translate-y-0.5 active:scale-[0.98] transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                        >
                            <Ticket className="w-5 h-5" />
                            랜덤 가게 뽑기
                        </button>
                    )}

                    {(selectedItem || isAnimating) && (
                        <div className="bg-white/95 backdrop-blur-md rounded-3xl shadow-xl shadow-black/5 border border-white p-7 text-center animate-in fade-in zoom-in-95 duration-400">
                            {isAnimating ? (
                                <div className="flex flex-col items-center justify-center py-4">
                                    <Loader2 className="w-8 h-8 text-orange-500 animate-spin mb-2" />
                                    <p className="text-orange-600 font-semibold text-lg" dangerouslySetInnerHTML={{ __html: selectedItem?.title || "가게 고르는 중..." }} />
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    <div className="text-sm text-orange-500 font-semibold uppercase tracking-wide">오늘의 추천!</div>
                                    <a
                                        href={selectedItem.link || `https://map.naver.com/v5/search/${encodeURIComponent(selectedItem.title.replace(/<[^>]*>?/gm, ''))}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-2xl font-bold text-gray-900 hover:text-orange-600 underline underline-offset-2 decoration-orange-300 transition-colors cursor-pointer"
                                        dangerouslySetInnerHTML={{ __html: selectedItem.title }}
                                    />
                                    <p className="text-gray-600 mb-4">{selectedItem.category}</p>

                                    {selectedItem.lat && selectedItem.lng && (
                                        <div className="rounded-2xl overflow-hidden shadow-sm border border-gray-100 mt-4 mb-5">
                                            <KakaoMap
                                                center={{ lat: selectedItem.lat, lng: selectedItem.lng }}
                                                userLocation={userLocation}
                                                items={[selectedItem]}
                                                className="w-full !h-40"
                                            />
                                        </div>
                                    )}

                                    <div className="flex gap-2 justify-center mt-4 pt-4 border-t border-gray-100">
                                        <button
                                            onClick={handleReset}
                                            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-bold flex items-center gap-1.5 transition-colors"
                                        >
                                            <RefreshCw className="w-4 h-4" />
                                            다시 뽑기
                                        </button>
                                        <ShareButton place={selectedItem} />
                                        {selectedItem.link && (
                                            <a
                                                href={selectedItem.link}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="px-4 py-2 bg-orange-600 text-white rounded-lg text-sm font-bold shadow-sm hover:bg-orange-700"
                                            >
                                                가게 보기
                                            </a>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </>
            )}

            {/* 메뉴 뽑기 모드 */}
            {mode === 'menu' && (
                <>
                    {!selectedMenu && !isAnimating && (
                        <button
                            onClick={handlePickMenu}
                            className="w-full bg-gradient-to-r from-pink-500 to-rose-500 text-white py-3.5 rounded-2xl font-bold text-lg shadow-lg shadow-pink-500/20 hover:shadow-pink-500/40 hover:-translate-y-0.5 active:scale-[0.98] transition-all flex items-center justify-center gap-2"
                        >
                            <UtensilsCrossed className="w-5 h-5" />
                            랜덤 메뉴 뽑기
                        </button>
                    )}

                    {(selectedMenu || isAnimating) && (
                        <div className="bg-white/95 backdrop-blur-md rounded-3xl shadow-xl shadow-black/5 border border-white p-7 text-center animate-in fade-in zoom-in-95 duration-400">
                            {isAnimating ? (
                                <div className="flex flex-col items-center justify-center py-4">
                                    <Loader2 className="w-8 h-8 text-pink-500 animate-spin mb-2" />
                                    <p className="text-pink-600 font-semibold text-lg">
                                        {selectedMenu ? `${selectedMenu.emoji} ${selectedMenu.name}` : "메뉴 고르는 중..."}
                                    </p>
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    <div className="text-sm text-pink-500 font-semibold uppercase tracking-wide">오늘의 메뉴!</div>
                                    <div className="text-5xl mb-2">{selectedMenu.emoji}</div>
                                    <div className="text-2xl font-bold text-gray-900">{selectedMenu.name}</div>

                                    <div className="flex gap-2 justify-center mt-4 pt-4 border-t border-gray-100">
                                        <button
                                            onClick={() => setSelectedMenu(null)}
                                            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-bold flex items-center gap-1.5 transition-colors"
                                        >
                                            <RefreshCw className="w-4 h-4" />
                                            다시 뽑기
                                        </button>
                                        <button
                                            onClick={handleSearchWithMenu}
                                            className="px-4 py-2 bg-pink-600 text-white rounded-lg text-sm font-bold shadow-sm hover:bg-pink-700 flex items-center gap-1.5"
                                        >
                                            <Search className="w-4 h-4" />
                                            이 메뉴 가게 찾기
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
