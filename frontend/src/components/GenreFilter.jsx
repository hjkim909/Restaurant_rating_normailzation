import React from 'react';

export default function GenreFilter({ categories, selectedCategory, onSelect }) {
    return (
        <div className="flex gap-2 overflow-x-auto pb-4 mb-2 touch-pan-x snap-x">
            <button
                onClick={() => onSelect(null)}
                className={`px-4 py-2 rounded-full whitespace-nowrap text-[15px] font-semibold transition-all duration-200 flex-shrink-0 snap-start shadow-sm outline-none ${selectedCategory === null
                    ? 'bg-gradient-to-r from-gray-800 to-gray-900 text-white shadow-gray-300'
                    : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50 hover:text-gray-900 hover:border-gray-300 active:scale-95'
                    }`}
            >
                전체
            </button>
            {categories.map((cat) => (
                <button
                    key={cat}
                    onClick={() => onSelect(cat)}
                    className={`px-4 py-2 rounded-full whitespace-nowrap text-[15px] font-semibold transition-all duration-200 flex-shrink-0 snap-start shadow-sm outline-none ${selectedCategory === cat
                        ? 'bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-orange-200 border-transparent'
                        : 'bg-white border border-gray-200 text-gray-600 hover:bg-orange-50 hover:text-orange-600 hover:border-orange-200 active:scale-95'
                        }`}
                >
                    {cat}
                </button>
            ))}
        </div>
    );
}
