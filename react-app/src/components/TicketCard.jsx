import React, { useState } from 'react';
import {
  cinemaLabel,
  formatCurrency,
  formatSeats,
  formatShowDate,
} from '../utils/ticketHelpers.js';

function FilmFallback() {
  return (
    <div
      className="w-full h-full min-h-[220px] flex items-center justify-center bg-gradient-to-br from-zinc-950 via-neutral-900 to-black"
      aria-hidden="true"
    >
      <svg
        viewBox="0 0 64 64"
        className="w-16 h-16 text-amber-200/80"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
      >
        <rect x="10" y="14" width="44" height="36" rx="4" />
        <circle cx="22" cy="32" r="6" />
        <path d="M32 24h18M32 32h18M32 40h12" />
      </svg>
    </div>
  );
}

export default function TicketCard({ ticket }) {
  const title = ticket.movie_title || 'Untitled screening';
  const [brokenPoster, setBrokenPoster] = useState(false);
  const showFallback =
    brokenPoster || !ticket.poster_url || ticket.poster_source === 'fallback';
  const city = ticket.city || '';

  return (
    <article className="overflow-hidden rounded-2xl bg-zinc-950 border border-zinc-800 hover:border-amber-700/60 transition-colors shadow-lg">
      <div className="relative aspect-[2/3] bg-black">
        {showFallback ? (
          <FilmFallback />
        ) : (
          <img
            src={ticket.poster_url}
            alt=""
            className="w-full h-full object-cover"
            onError={() => setBrokenPoster(true)}
          />
        )}
        {!ticket.complete && (
          <span className="absolute top-3 left-3 text-[10px] uppercase tracking-wide px-2 py-1 rounded bg-amber-900/80 text-amber-100">
            Review
          </span>
        )}
      </div>
      <div className="p-4 space-y-2">
        <p className="text-[10px] uppercase tracking-[0.2em] text-amber-500/80">Movie</p>
        <h2 className="text-lg font-semibold text-zinc-50 leading-snug">{title}</h2>
        {ticket.blurb && <p className="text-sm text-zinc-400">{ticket.blurb}</p>}
        <p className="text-sm text-zinc-300">{cinemaLabel(ticket)}</p>
        {city && <p className="text-xs text-zinc-500">{city}</p>}
        <p className="text-sm text-zinc-200">{formatShowDate(ticket)}</p>
        <div className="flex items-center justify-between pt-2 text-sm">
          <span className="text-zinc-400">{formatSeats(ticket)}</span>
          <span className="font-medium text-amber-200">
            {formatCurrency(ticket.amount, ticket.currency)}
          </span>
        </div>
      </div>
    </article>
  );
}
