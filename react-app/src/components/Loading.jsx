import React from 'react';

export default function Loading() {
  return (
    <div className="min-h-screen bg-black py-8 px-6">
      <div className="max-w-6xl mx-auto animate-pulse">
        <div className="h-8 bg-zinc-800 rounded w-64 mb-8" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[0, 1, 2, 3].map((key) => (
            <div key={key} className="h-20 bg-zinc-900 rounded-xl border border-zinc-800" />
          ))}
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[0, 1, 2, 3, 4, 5, 6, 7].map((key) => (
            <div key={key} className="rounded-2xl overflow-hidden border border-zinc-800">
              <div className="aspect-[2/3] bg-gradient-to-br from-zinc-950 via-neutral-900 to-black" />
              <div className="p-4 space-y-2">
                <div className="h-4 bg-zinc-800 rounded w-3/4" />
                <div className="h-3 bg-zinc-900 rounded w-1/2" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
