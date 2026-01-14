import { useState } from 'react'
import axios from 'axios'
import { Search, MapPin, Star, Utensils, Sparkles } from 'lucide-react'
import AIView from './components/AIView'

function App() {
  const [activeTab, setActiveTab] = useState('search') // 'search' | 'ai'
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [location, setLocation] = useState(null) // {lat, lng}

  const handleSearch = async (e) => {
    if (e) e.preventDefault()
    if (!query && !location) return

    setLoading(true)
    try {
      const params = { query }
      if (location) {
        params.lat = location.lat
        params.lng = location.lng
      }

      const response = await axios.get('/api/v1/search', { params })
      setResults(response.data.items)
    } catch (error) {
      console.error("Search failed", error)
    } finally {
      setLoading(false)
    }
  }

  const handleLocationClick = () => {
    if (!navigator.geolocation) {
      alert("브라우저가 위치 정보를 지원하지 않습니다.")
      return
    }

    setLoading(true)
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords
        setLocation({ lat: latitude, lng: longitude })
        setQuery('')
        fetchWithLocation(latitude, longitude)
      },
      (error) => {
        console.error(error)
        setLoading(false)
        alert("위치를 가져올 수 없습니다. 권한을 확인해주세요.")
      }
    )
  }

  const fetchWithLocation = async (lat, lng) => {
    try {
      const response = await axios.get('/api/v1/search', {
        params: { lat, lng }
      })
      setResults(response.data.items)
    } catch (error) {
      console.error("Location search failed", error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans">
      {/* Hero Section */}
      <header className="bg-white shadow-sm sticky top-0 z-50">
        <div className="max-w-md mx-auto px-4 py-3 flex items-center justify-between">
          <h1 className="text-xl font-bold text-orange-600 flex items-center gap-2">
            <Utensils className="w-6 h-6" />
            오늘 뭐 먹지?
          </h1>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-100 max-w-md mx-auto">
          <button
            onClick={() => setActiveTab('search')}
            className={`flex-1 py-3 text-sm font-medium text-center border-b-2 transition-colors ${activeTab === 'search' ? 'border-orange-500 text-orange-600' : 'border-transparent text-gray-400 hover:text-gray-600'}`}
          >
            ⚡️ 빠른 검색
          </button>
          <button
            onClick={() => setActiveTab('ai')}
            className={`flex-1 py-3 text-sm font-medium text-center border-b-2 transition-colors ${activeTab === 'ai' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-400 hover:text-gray-600'}`}
          >
            ✨ AI 미식가
          </button>
        </div>
      </header>

      <main className="max-w-md mx-auto px-4 py-6 space-y-6">
        {activeTab === 'search' ? (
          <>
            {/* Location Button (Separate) */}
            <button
              onClick={handleLocationClick}
              className="w-full bg-white border border-orange-200 text-orange-600 font-medium py-3 px-4 rounded-xl flex items-center justify-center gap-2 hover:bg-orange-50 transition-colors shadow-sm"
            >
              <MapPin className="w-5 h-5" />
              현재 내 위치 주변 맛집 찾기
            </button>

            {/* Search Bar */}
            <form onSubmit={handleSearch} className="relative">
              <input
                type="text"
                placeholder="강남역 맛집, 오늘 뭐 먹지?"
                className="w-full pl-10 pr-16 py-3 rounded-xl border border-gray-200 shadow-sm focus:ring-2 focus:ring-orange-500 focus:border-transparent outline-none transition-all"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <Search className="absolute left-3 top-3.5 text-gray-400 w-5 h-5" />

              <button
                type="submit"
                disabled={loading}
                className="absolute right-2 top-2 bg-gray-900 text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-black transition-colors disabled:opacity-50"
              >
                검색
              </button>
            </form>

            {/* Results */}
            <div className="space-y-4">
              {results.map((place, index) => (
                <div key={index} className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex gap-4 hover:shadow-md transition-shadow cursor-pointer" onClick={() => window.open(place.link || `https://map.naver.com/v5/search/${place.title}`, '_blank')}>
                  <div className="flex-1">
                    <div className="flex justify-between items-start mb-1">
                      <div className="flex items-center gap-2 overflow-hidden">
                        <h3 className="font-bold text-lg text-gray-900 truncate" dangerouslySetInnerHTML={{ __html: place.title }} />
                        <span className="text-xs text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded-md whitespace-nowrap">{place.category}</span>
                      </div>
                      <span className="text-sm font-semibold text-orange-500 flex items-center gap-1 flex-shrink-0">
                        <Star className="w-4 h-4 fill-current" />
                        {place.adjusted_rating || place.userRating}
                      </span>
                    </div>

                    <div className="flex items-center gap-1 text-sm text-gray-500">
                      <MapPin className="w-3 h-3 flex-shrink-0" />
                      <span className="truncate">{place.roadAddress}</span>
                      {place.distance && (
                        <span className="text-xs text-orange-600 font-medium ml-1">
                          ({place.distance < 1000 ? `${Math.round(place.distance)}m` : `${(place.distance / 1000).toFixed(1)}km`})
                        </span>
                      )}
                    </div>

                    {place.lunch_score > 0 && (
                      <div className="mt-3 inline-flex items-center px-2 py-1 bg-green-50 text-green-700 text-xs rounded-md font-medium">
                        🍱 점심 추천도 {place.lunch_score}점
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {!loading && results.length === 0 && (
                <div className="text-center py-10 text-gray-400">
                  <p>주변 맛집을 검색해보세요!</p>
                </div>
              )}
            </div>
          </>
        ) : (
          <AIView location={location || query} />
        )}
      </main>
    </div>
  )
}

export default App
