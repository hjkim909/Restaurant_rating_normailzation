import React, { useState } from 'react';
import { Loader2, Ticket } from 'lucide-react';
import KakaoMap from './KakaoMap';

export default function RandomPicker({ items, userLocation }) {
    const [selectedItem, setSelectedItem] = useState(null);
    const [isAnimating, setIsAnimating] = useState(false);

    const handlePick = () => {
        if (!items || items.length === 0) return;

        setIsAnimating(true);
        setSelectedItem(null);

        // Simple animation effect
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

    return (
        <div className="mb-4">
            {!selectedItem && !isAnimating && (
                <button
                    onClick={handlePick}
                    disabled={!items.length}
                    className="w-full bg-gradient-to-r from-orange-500 to-amber-500 text-white py-3 rounded-xl font-bold text-lg shadow-lg active:scale-95 transition-transform flex items-center justify-center gap-2"
                >
                    <Ticket className="w-5 h-5" />
                    랜덤 메뉴 뽑기
                </button>
            )}

            {(selectedItem || isAnimating) && (
                <div className="bg-white rounded-xl shadow-lg border border-orange-100 p-6 text-center animate-in fade-in zoom-in duration-300">
                    {isAnimating ? (
                        <div className="flex flex-col items-center justify-center py-4">
                            <Loader2 className="w-8 h-8 text-orange-500 animate-spin mb-2" />
                            <p className="text-orange-600 font-semibold text-lg">{selectedItem?.title || "메뉴 고르는 중..."}</p>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            <div className="text-sm text-orange-500 font-semibold uppercase tracking-wide">오늘의 추천!</div>
                            <h3 className="text-2xl font-bold text-gray-900" dangerouslySetInnerHTML={{ __html: selectedItem.title }} />
                            <p className="text-gray-600 mb-4">{selectedItem.category}</p>

                            {/* Small Map View for Selected Item */}
                            {selectedItem.lat && selectedItem.lng && (
                                <div className="rounded-xl overflow-hidden shadow-inner border border-gray-200 mt-2 mb-4">
                                    <KakaoMap
                                        center={{ lat: selectedItem.lat, lng: selectedItem.lng }}
                                        userLocation={userLocation} // Show user location if available
                                        items={[selectedItem]} // Only show this item
                                        className="w-full !h-40" // Override height
                                    />
                                </div>
                            )}

                            <div className="flex gap-2 justify-center mt-4 pt-4 border-t border-gray-100">
                                <button
                                    onClick={() => setSelectedItem(null)}
                                    className="px-4 py-2 text-gray-500 hover:bg-gray-50 rounded-lg text-sm font-medium"
                                >
                                    다시 뽑기
                                </button>
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
        </div>
    );
}
