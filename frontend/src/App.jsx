import { useState, useMemo, useEffect } from 'react'
import axios from 'axios'
import { Search, MapPin, Star, Utensils, Map as MapIcon, List as ListIcon } from 'lucide-react'
import AIView from './components/AIView'
import GenreFilter from './components/GenreFilter'
import RandomPicker from './components/RandomPicker'
import KakaoMap from './components/KakaoMap'

// Set API Base URL for production
if (import.meta.env.VITE_API_BASE_URL) {
  axios.defaults.baseURL = import.meta.env.VITE_API_BASE_URL
}

function App() {
  const [activeTab, setActiveTab] = useState('search') // 'search' | 'ai'
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [location, setLocation] = useState(null) // {lat, lng}

  // New State for Features
  const [viewMode, setViewMode] = useState('list') // 'list' | 'map'
  const [selectedCategory, setSelectedCategory] = useState(null)

  // Auto-search on mount
  useEffect(() => {
    handleLocationClick(true);
  }, []);

  const handleSearch = async (e) => {
    if (e) e.preventDefault()
    if (!query && !location) return

    setLoading(true)
    setSelectedCategory(null) // Reset filter on new search
    setResults([]) // Clear previous results

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

  const handleLocationClick = (isAuto = false) => {
    if (!navigator.geolocation) {
      if (!isAuto) alert("브라우저가 위치 정보를 지원하지 않습니다.")
      return
    }

    setLoading(true)
    setSelectedCategory(null)

    const options = isAuto ? { timeout: 5000, maximumAge: 0 } : {};

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
        if (!isAuto) alert("위치를 가져올 수 없습니다. 권한을 확인해주세요.")
      },
      options
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

  // 메뉴 뽑기 후 검색
  const handleMenuSearch = async (menuName) => {
    setLoading(true)
    setSelectedCategory(null)
    setQuery(menuName)

    try {
      const params = { query: menuName }
      if (location) {
        params.lat = location.lat
        params.lng = location.lng
      }

      const response = await axios.get('/api/v1/search', { params })
      setResults(response.data.items)
    } catch (error) {
      console.error("Menu search failed", error)
    } finally {
      setLoading(false)
    }
  }

  // Extract Categories
  const categories = useMemo(() => {
    if (!results.length) return [];
    const cats = new Set();
    results.forEach(item => {
      if (!item.category) return;
      // Naver categories are often "Food > Korean > BBQ". We extract the last meaningful part.
      const parts = item.category.split('>');
      if (parts.length > 0) {
        // Clean whitespace
        cats.add(parts[parts.length - 1].trim());
      }
    });
    return Array.from(cats).sort();
  }, [results]);

  // Filter Results
  const filteredResults = useMemo(() => {
    if (!selectedCategory) return results;
    return results.filter(item => item.category && item.category.includes(selectedCategory));
  }, [results, selectedCategory]);

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans pb-20">
      {/* Hero Section */}
      <header className="bg-white shadow-sm sticky top-0 z-50">
        <div className="max-w-md mx-auto px-4 py-3 flex items-center justify-between">
          <h1 className="text-xl font-bold text-orange-600 flex items-center gap-2">
            <Utensils className="w-6 h-6" />
            Mechu
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

      <main className="max-w-md mx-auto px-4 py-6 space-y-4">
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

            {/* View Toggle & Filters (Only show if results exist) */}
            {results.length > 0 && (
              <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-500">
                    총 {filteredResults.length}개의 맛집
                  </span>
                  <button
                    onClick={() => setViewMode(viewMode === 'list' ? 'map' : 'list')}
                    className="flex items-center gap-1.5 bg-white border border-gray-200 text-gray-700 px-3 py-1.5 rounded-lg text-sm font-medium shadow-sm hover:bg-gray-50"
                  >
                    {viewMode === 'list' ? <MapIcon className="w-4 h-4" /> : <ListIcon className="w-4 h-4" />}
                    {viewMode === 'list' ? '지도 보기' : '리스트 보기'}
                  </button>
                </div>

                <GenreFilter
                  categories={categories}
                  selectedCategory={selectedCategory}
                  onSelect={setSelectedCategory}
                />

                {/* Random Picker */}
                <RandomPicker items={filteredResults} userLocation={location} onSearchMenu={handleMenuSearch} />

                {/* Content Area */}
                {viewMode === 'list' ? (
                  <div className="space-y-4">
                    {filteredResults.map((place, index) => (
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
                  </div>
                ) : (
                  <KakaoMap
                    center={location}
                    userLocation={location} // Pass userLocation explicitly
                    items={filteredResults}
                    className="w-full shadow-md"
                  />
                )}
              </div>
            )}

            {!loading && results.length === 0 && (
              <div className="text-center py-10 text-gray-400">
                <p>주변 맛집을 검색해보세요!</p>
              </div>
            )}

            {loading && (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500 mx-auto mb-4"></div>
                <p className="text-gray-500">맛집 정보를 불러오는 중...</p>
              </div>
            )}
          </>
        ) : (
          <AIView location={location || query} />
        )}
      </main>
    </div>
  )
}

export default App
