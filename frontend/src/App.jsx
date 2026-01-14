import { useState } from 'react'
import axios from 'axios'
import { Search, MapPin, Star, Utensils } from 'lucide-react'

function App() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query) return

    setLoading(true)
    try {
      const response = await axios.get('/api/v1/search', {
        params: { query }
      })
      setResults(response.data.items)
    } catch (error) {
      console.error("Search failed", error)
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
      </header>

      <main className="max-w-md mx-auto px-4 py-6 space-y-6">
        {/* Search Bar */}
        <form onSubmit={handleSearch} className="relative">
          <input
            type="text"
            placeholder="강남역 맛집, 오늘 뭐 먹지?"
            className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 shadow-sm focus:ring-2 focus:ring-orange-500 focus:border-transparent outline-none transition-all"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <Search className="absolute left-3 top-3.5 text-gray-400 w-5 h-5" />
          <button
            type="submit"
            disabled={loading}
            className="absolute right-2 top-2 bg-orange-500 text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-orange-600 transition-colors disabled:opacity-50"
          >
            {loading ? '검색중...' : '검색'}
          </button>
        </form>

        {/* Results */}
        <div className="space-y-4">
          {results.map((place, index) => (
            <div key={index} className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex gap-4 hover:shadow-md transition-shadow">
              <div className="flex-1">
                <div className="flex justify-between items-start">
                  <h3 className="font-bold text-lg text-gray-900 truncate" dangerouslySetInnerHTML={{ __html: place.title }} />
                  <span className="text-sm font-semibold text-orange-500 flex items-center gap-1">
                    <Star className="w-4 h-4 fill-current" />
                    {place.adjusted_rating || place.userRating}
                  </span>
                </div>
                <p className="text-sm text-gray-500 mt-1">{place.category}</p>
                <div className="flex items-center gap-1 mt-2 text-xs text-gray-400">
                  <MapPin className="w-3 h-3" />
                  <span className="truncate">{place.roadAddress}</span>
                </div>
                {place.lunch_score > 0 && (
                  <div className="mt-2 inline-flex items-center px-2 py-1 bg-green-50 text-green-700 text-xs rounded-md">
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
      </main>
    </div>
  )
}

export default App
