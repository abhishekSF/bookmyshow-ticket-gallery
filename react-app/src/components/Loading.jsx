import React from 'react';
import { CATEGORY_COLORS } from '../utils/ticketHelpers.js';

/**
 * Loading Component - Skeleton card for loading state
 * Displays animated placeholder content while tickets are loading
 */
export default function Loading() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-black py-8 px-4 md:px-8">
      {/* Header */}
      <header className="max-w-7xl mx-auto mb-12">
        <div className="animate-pulse">
          <div className="h-10 bg-gray-700 rounded w-48 mb-2"></div>
          <div className="h-4 bg-gray-800 rounded w-32"></div>
        </div>
      </header>

      {/* Stats Skeleton */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-gray-900 rounded-lg p-4 border border-gray-800">
              <div className="h-3 bg-gray-800 rounded w-20 mb-2"></div>
              <div className="h-8 bg-gray-700 rounded w-12"></div>
            </div>
          ))}
        </div>
      </div>

      {/* Filter Skeleton */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex flex-wrap gap-4 items-center">
          <div className="flex flex-wrap gap-2">
            {[...Array(10)].map((_, i) => (
              <div key={i} className="h-8 w-16 bg-gray-800 rounded-full"></div>
            ))}
          </div>
          <select className="hidden">
            <option>Sort by Date</option>
          </select>
        </div>
      </div>

      {/* Gallery Skeleton */}
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {[...Array(8)].map((_, i) => (
            <SkeletonTicketCard key={i} category={i % 7} />
          ))}
        </div>
      </div>
    </div>
  );
}

/**
 * Individual skeleton ticket card
 */
function SkeletonTicketCard({ category }) {
  const colors = CATEGORY_COLORS[category] || CATEGORY_COLORS.uncategorized;
  
  return (
    <div className={`
      relative overflow-hidden rounded-2xl bg-white
      animate-pulse border border-gray-800
    `}>
      {/* Poster placeholder */}
      <div className="w-full md:w-32 aspect-[3/4] bg-gray-800"></div>

      {/* Content placeholder */}
      <div className="flex-1 p-5">
        <div className="mb-3">
          <div className="h-5 bg-gray-700 rounded w-40 mb-2"></div>
          <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${colors.badge}`}>
            <span className="h-2 w-10 bg-gray-600 rounded-full"></span>
          </span>
        </div>
        
        <div className="space-y-2 mb-4">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-gray-800 rounded"></div>
            <div className="h-4 bg-gray-700 rounded w-24"></div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-gray-800 rounded"></div>
            <div className="h-4 bg-gray-700 rounded w-20"></div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-gray-800 rounded"></div>
            <div className="h-4 bg-gray-700 rounded w-16"></div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-gray-800 rounded"></div>
            <div className="h-5 bg-gray-700 rounded w-12 font-bold"></div>
          </div>
        </div>
      </div>

      {/* Footer placeholder */}
      <div className="mt-3 pt-3 border-t border-gray-800">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-gray-800 rounded-full"></div>
          <div className="h-4 bg-gray-800 rounded w-32"></div>
        </div>
      </div>
    </div>
  );
}