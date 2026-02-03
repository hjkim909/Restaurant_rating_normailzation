import React, { useState } from 'react';
import { Share2, Check, Copy } from 'lucide-react';

/**
 * 공유 버튼 컴포넌트
 * - Web Share API 지원 시: 네이티브 공유 시트
 * - 미지원 시: 클립보드 복사
 */
export default function ShareButton({ place, className = '' }) {
    const [copied, setCopied] = useState(false);

    // HTML 태그 제거
    const cleanTitle = place?.title?.replace(/<[^>]*>?/gm, '') || '맛집';

    const shareText = `🍽️ ${cleanTitle}
📍 ${place?.roadAddress || place?.address || ''}
⭐ ${place?.adjusted_rating || place?.userRating || ''}점
🔗 Mechu에서 추천받음!`;

    const shareData = {
        title: cleanTitle,
        text: shareText,
        url: place?.link || `https://map.naver.com/v5/search/${encodeURIComponent(cleanTitle)}`
    };

    const handleShare = async (e) => {
        e.stopPropagation(); // 부모 클릭 이벤트 방지

        // Web Share API 지원 시 (주로 모바일)
        if (navigator.share) {
            try {
                await navigator.share(shareData);
                return;
            } catch (err) {
                // 사용자가 취소한 경우는 무시
                if (err.name === 'AbortError') return;
            }
        }

        // 클립보드 복사 fallback
        try {
            await navigator.clipboard.writeText(shareText);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            // 구형 브라우저 fallback
            const textarea = document.createElement('textarea');
            textarea.value = shareText;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    if (!place) return null;

    return (
        <button
            onClick={handleShare}
            className={`px-4 py-2 bg-blue-50 hover:bg-blue-100 text-blue-600 rounded-lg text-sm font-bold flex items-center gap-1.5 transition-colors ${className}`}
            title="공유하기"
        >
            {copied ? (
                <>
                    <Check className="w-4 h-4" />
                    복사됨!
                </>
            ) : (
                <>
                    <Share2 className="w-4 h-4" />
                    공유
                </>
            )}
        </button>
    );
}
