import { useState } from 'react'
import axios from 'axios'
import { Sparkles, MessageSquare, ThumbsUp } from 'lucide-react'

// 상황 프리셋 목록
const CONTEXT_PRESETS = [
    { emoji: '🍱', label: '혼밥', context: '혼자 편하게 먹을 수 있는 곳 추천해줘. 1인 식사 가능한 곳으로.' },
    { emoji: '🥗', label: '다이어트', context: '칼로리 낮고 건강한 음식 먹고 싶어. 샐러드나 저칼로리 메뉴 위주로.' },
    { emoji: '🍲', label: '해장', context: '속이 안 좋아서 해장음식 필요해. 국물 있고 따뜻한 음식으로.' },
    { emoji: '👥', label: '회식', context: '동료들과 단체 회식할 건데, 분위기 좋고 다양한 메뉴 있는 곳.' },
    { emoji: '💑', label: '데이트', context: '연인과 데이트하는데 분위기 좋고 맛있는 곳 추천해줘.' },
    { emoji: '💰', label: '가성비', context: '저렴하고 양 많은 가성비 좋은 맛집 찾아줘.' },
    { emoji: '🌶️', label: '매운맛', context: '오늘 매운 거 땡기는데 맵고 자극적인 음식 추천해줘.' },
    { emoji: '☕', label: '가볍게', context: '간단하게 가볍게 먹을 수 있는 브런치나 카페 추천해줘.' },
];

export default function AIView({ location }) {
    const [context, setContext] = useState('')
    const [partySize, setPartySize] = useState(null) // 인원 수 (null = 미설정)
    const [loading, setLoading] = useState(false)
    const [aiResult, setAiResult] = useState(null)

    const handleAnalyze = async () => {
        if (!context && !partySize) {
            alert("상황을 선택하거나 입력해주세요!")
            return
        }
        if (!location) {
            alert("위치를 먼저 설정하거나 검색해주세요!")
            return
        }

        setLoading(true)
        setAiResult(null) // 이전 결과 초기화
        try {
            // 인원 수가 설정되면 context에 추가
            let fullContext = context
            if (partySize && !context.includes('명')) {
                fullContext = context ? `${context} (${partySize}명)` : `${partySize}명이서 먹을 곳 추천해줘`
            }

            const payload = {
                user_context: fullContext,
                location: typeof location === 'string' ? location : '강남역',
                lat: location.lat || null,
                lng: location.lng || null,
                party_size: partySize
            }

            const response = await axios.post('/api/v1/recommend', payload)
            setAiResult(response.data)
        } catch (error) {
            console.error("AI Analysis failed", error)
            // Why: 에러 상황별로 사용자에게 친절한 안내
            if (error.code === 'ECONNABORTED') {
                alert("서버 응답에 시간이 오래 걸리고 있어요. 잠시 후 다시 시도해주세요! (서버 부팅 중일 수 있습니다)")
            } else if (error.response?.status === 422) {
                alert("위치 정보가 필요합니다. '빠른 검색' 탭에서 위치를 먼저 설정해주세요!")
            } else {
                alert("AI 분석 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
            }
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="space-y-6">
            <div className="bg-gradient-to-br from-indigo-50/80 via-white/80 to-purple-50/80 backdrop-blur-md p-6 rounded-3xl border border-indigo-100/50 shadow-lg shadow-indigo-900/5">
                <div className="flex items-center gap-2 mb-5">
                    <Sparkles className="w-6 h-6 text-indigo-500" />
                    <h2 className="font-extrabold text-xl bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-purple-600">AI 미식가</h2>
                </div>

                {/* 상황 프리셋 버튼 */}
                <div className="mb-4">
                    <p className="text-xs text-gray-500 mb-2 font-medium">💡 빠른 선택</p>
                    <div className="flex gap-2 overflow-x-auto pb-2 -mx-1 px-1">
                        {CONTEXT_PRESETS.map((preset, idx) => (
                            <button
                                key={idx}
                                onClick={() => setContext(preset.context)}
                                className={`flex-shrink-0 px-4 py-2 rounded-2xl text-[15px] font-semibold transition-all duration-200 active:scale-95 ${context === preset.context
                                    ? 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-md shadow-indigo-200 border-transparent'
                                    : 'bg-white/80 backdrop-blur-sm border border-gray-200 text-gray-700 hover:border-indigo-300 hover:bg-indigo-50/80 hover:text-indigo-700 hover:shadow-sm'
                                    }`}
                            >
                                {preset.emoji} {preset.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* 인원 수 선택 */}
                <div className="mb-4">
                    <p className="text-xs text-gray-500 mb-2 font-medium">👥 인원 수</p>
                    <div className="flex gap-2 flex-wrap">
                        {[1, 2, 3, 4, 5, 6, 7, 8].map((num) => (
                            <button
                                key={num}
                                onClick={() => setPartySize(partySize === num ? null : num)}
                                className={`w-11 h-11 rounded-2xl text-[15px] font-bold transition-all duration-200 active:scale-95 flex items-center justify-center ${partySize === num
                                    ? 'bg-gradient-to-br from-indigo-500 to-purple-500 text-white shadow-md shadow-indigo-200 border-transparent'
                                    : 'bg-white/80 backdrop-blur-sm border border-gray-200 text-gray-700 hover:border-indigo-300 hover:bg-indigo-50/80 hover:text-indigo-700 hover:shadow-sm'
                                    }`}
                            >
                                {num}
                            </button>
                        ))}
                        <span className="flex items-center text-xs text-gray-400 ml-1">명</span>
                    </div>
                </div>

                <textarea
                    className="w-full p-4 rounded-2xl border border-indigo-200 focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-400 outline-none resize-none bg-white/80 backdrop-blur-sm text-gray-800 h-28 shadow-sm transition-all duration-300"
                    placeholder="상황을 자유롭게 설명하거나 위의 빠른 선택을 눌러보세요!"
                    value={context}
                    onChange={(e) => setContext(e.target.value)}
                />

                <div className="mt-4 flex justify-end">
                    <button
                        onClick={handleAnalyze}
                        disabled={loading || (!context && !partySize)}
                        className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-8 py-3.5 rounded-2xl font-bold hover:shadow-lg hover:shadow-indigo-500/30 hover:-translate-y-0.5 active:scale-[0.98] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                        {loading ? (
                            <>
                                <span className="animate-spin text-xl">✨</span>
                                분석 중...
                            </>
                        ) : (
                            <>
                                <Sparkles className="w-5 h-5" />
                                AI 분석 시작
                            </>
                        )}
                    </button>
                </div>
            </div>

            {aiResult && (
                <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    {/* Conversational Response */}
                    <div className="bg-white/90 backdrop-blur-sm p-5 rounded-3xl border border-indigo-100 shadow-lg shadow-indigo-900/5 flex gap-4 my-2">
                        <div className="min-w-[44px] h-[44px] rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center shadow-inner shadow-white/30">
                            <MessageSquare className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <p className="text-gray-800 leading-relaxed font-medium">
                                {aiResult.conversational_response}
                            </p>
                        </div>
                    </div>

                    {/* Recommendations */}
                    <div className="space-y-5">
                        {aiResult.recommendations.map((rec, idx) => (
                            <div key={idx} className="bg-white/90 backdrop-blur-sm p-6 rounded-3xl border border-transparent shadow-lg shadow-gray-200/50 hover:shadow-xl hover:shadow-indigo-500/10 hover:-translate-y-1 hover:border-indigo-100 transition-all duration-300 group">
                                <div className="flex justify-between items-start mb-4">
                                    <h3 className="text-xl font-extrabold text-gray-900 flex items-center gap-2">
                                        <span className="text-transparent bg-clip-text bg-gradient-to-br from-indigo-500 to-purple-500">#{idx + 1}</span>
                                        {rec.menu}
                                    </h3>
                                    <span className="bg-gradient-to-r from-emerald-50 to-teal-50 text-emerald-700 border border-emerald-100 px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-sm">
                                        <ThumbsUp className="w-3 h-3" />
                                        신뢰도 {Math.round(rec.confidence * 100)}%
                                    </span>
                                </div>

                                <div className="bg-gray-50/80 p-5 rounded-2xl text-[15px] text-gray-700 mb-5 leading-relaxed border border-gray-100/50">
                                    <p className="font-bold text-indigo-900 mb-2 flex items-center gap-1.5">
                                        <Sparkles className="w-4 h-4 text-indigo-500" />
                                        추천 이유
                                    </p>
                                    {rec.reasoning}
                                </div>

                                {rec.restaurants.length > 0 && (
                                    <div className="space-y-2">
                                        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">추천 식당</p>
                                        {rec.restaurants.map((rest, rIdx) => (
                                            <div key={rIdx} className="flex justify-between items-center text-sm p-2 hover:bg-gray-50 rounded-lg cursor-pointer border border-transparent hover:border-gray-100 transition-colors" onClick={() => window.open(`https://map.naver.com/v5/search/${rest.title}`, '_blank')}>
                                                <span className="font-medium text-gray-800" dangerouslySetInnerHTML={{ __html: rest.title }}></span>
                                                <span className="text-gray-400 text-xs">{rest.category}</span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}
