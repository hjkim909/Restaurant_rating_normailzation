import React from 'react';

export default function GenreFilter({ categories, selectedCategory, onSelect }) {
    return (
        <div className="flex gap-2 overflow-x-auto pb-4 mb-2 touch-pan-x snap-x">
            <button
                onClick={() => onSelect(null)}
                className={`px-4 py-2 rounded-full whitespace-nowrap text-sm font-medium transition-colors flex-shrink-0 snap-start ${selectedCategory === null
                    ? 'bg-orange-600 text-white shadow-md'
                    : 'bg-white border border-gray-200 text-gray-600 hover:bg-orange-50 hover:text-orange-600'
                    }`}
            >
                전체
            </button>
            {categories.map((cat) => (
                <button
                    key={cat}
                    onClick={() => onSelect(cat)}
                    className={`px-4 py-2 rounded-full whitespace-nowrap text-sm font-medium transition-colors flex-shrink-0 snap-start ${selectedCategory === cat
                        ? 'bg-orange-600 text-white shadow-md'
                        : 'bg-white border border-gray-200 text-gray-600 hover:bg-orange-50 hover:text-orange-600'
                        }`}
                >
                    {cat}
                </button>
            ))}
        </div>
    );
}
