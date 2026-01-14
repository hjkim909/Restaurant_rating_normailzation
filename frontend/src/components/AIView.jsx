import { useState } from 'react'
import axios from 'axios'
import { Sparkles, MessageSquare, ThumbsUp } from 'lucide-react'

export default function AIView({ location }) {
    const [context, setContext] = useState('')
    const [loading, setLoading] = useState(false)
    const [aiResult, setAiResult] = useState(null)

    const handleAnalyze = async () => {
        if (!context) return
        if (!location) {
            alert("위치를 먼저 설정하거나 검색해주세요!")
            return
        }

        setLoading(true)
        try {
            const payload = {
                user_context: context,
                location: typeof location === 'string' ? location : '강남역', // Simple fallback
                lat: location.lat || null,
                lng: location.lng || null
            }

            const response = await axios.post('/api/v1/recommend', payload)
            setAiResult(response.data)
        } catch (error) {
            console.error("AI Analysis failed", error)
            alert("AI 분석 중 오류가 발생했습니다.")
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="space-y-6">
            <div className="bg-gradient-to-br from-indigo-50 to-purple-50 p-6 rounded-2xl border border-indigo-100">
                <div className="flex items-center gap-2 mb-4">
                    <Sparkles className="w-5 h-5 text-indigo-600" />
                    <h2 className="font-bold text-lg text-gray-800">AI 미식가</h2>
                </div>

                <textarea
                    className="w-full p-4 rounded-xl border border-indigo-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none resize-none bg-white text-gray-800 h-32"
                    placeholder="예: '오늘 속이 좀 안 좋은데 부드러운 음식 없을까?', '친구랑 가는데 분위기 좋은 곳 추천해줘'"
                    value={context}
                    onChange={(e) => setContext(e.target.value)}
                />

                <div className="mt-4 flex justify-end">
                    <button
                        onClick={handleAnalyze}
                        disabled={loading || !context}
                        className="bg-indigo-600 text-white px-6 py-2.5 rounded-xl font-medium hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-sm shadow-indigo-200"
                    >
                        {loading ? (
                            <>
                                <span className="animate-spin text-xl">✨</span>
                                분석 중...
                            </>
                        ) : (
                            <>
                                <Sparkles className="w-4 h-4" />
                                AI 분석 시작
                            </>
                        )}
                    </button>
                </div>
            </div>

            {aiResult && (
                <div className="space-y-6 animate-fade-in">
                    {/* Conversational Response */}
                    <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex gap-4">
                        <div className="min-w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center">
                            <MessageSquare className="w-5 h-5 text-indigo-600" />
                        </div>
                        <div>
                            <p className="text-gray-800 leading-relaxed font-medium">
                                {aiResult.conversational_response}
                            </p>
                        </div>
                    </div>

                    {/* Recommendations */}
                    <div className="space-y-4">
                        {aiResult.recommendations.map((rec, idx) => (
                            <div key={idx} className="bg-white p-5 rounded-2xl border border-gray-100 shadow-md hover:shadow-lg transition-shadow">
                                <div className="flex justify-between items-start mb-3">
                                    <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                                        <span className="text-indigo-600">#{idx + 1}</span>
                                        {rec.menu}
                                    </h3>
                                    <span className="bg-green-50 text-green-700 px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1">
                                        <ThumbsUp className="w-3 h-3" />
                                        신뢰도 {Math.round(rec.confidence * 100)}%
                                    </span>
                                </div>

                                <div className="bg-gray-50 p-4 rounded-xl text-sm text-gray-700 mb-4 leading-relaxed">
                                    <p className="font-medium text-indigo-900 mb-1">💡 추천 이유</p>
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
