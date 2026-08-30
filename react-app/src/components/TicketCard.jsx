import React from 'react';
import {
  CATEGORY_COLORS,
  getCategoryDisplayName,
  formatDateTime,
  formatCurrency,
  formatSeats,
  validateTicket
} from '../utils/ticketHelpers.js';

/**
 * TicketCard - Displays a single ticket booking in a card layout
 * @param {Object} ticket - Ticket object with all fields
 * @param {boolean} showValidation - Whether to show validation status
 */
export default function TicketCard({ ticket, showValidation = false }) {
  const {
    booking_id,
    event_name,
    venue,
    show_date,
    show_time,
    seats,
    amount_paid,
    poster_url,
    category,
    confidence_score,
    parsing_notes,
    extracted_at
  } = ticket;

  const isLowConfidence = confidence_score < 70;
  const isValid = validateTicket(ticket);
  const categoryColors = CATEGORY_COLORS[category] || CATEGORY_COLORS.uncategorized;

  return (
    <div className={`
      relative overflow-hidden rounded-2xl bg-white
      transition-all duration-300 hover:shadow-xl hover:-translate-y-1
      ${isValid.isValid ? 'shadow-lg' : 'border border-red-300 opacity-90'}
    `}>
      {/* Validation Badge */}
      {showValidation && (
        <div className={`absolute top-2 right-2 px-3 py-1 rounded-full text-xs font-medium ${
          isValid.isValid 
            ? 'bg-green-100 text-green-800' 
            : 'bg-red-100 text-red-800'
        }`}>
          {isValid.isValid ? (
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-green-600"></span>
              Valid
            </span>
          ) : (
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-red-600"></span>
              Issues
            </span>
          )}
        </div>
      )}

      {/* Confidence Badge */}
      {isLowConfidence && (
        <div className="absolute top-2 left-2 px-2 py-1 rounded bg-yellow-100 text-yellow-800 text-xs font-medium">
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-yellow-600"></span>
            {confidence_score:.0f}% Confidence
          </span>
        </div>
      )}

      {/* Ticket Content */}
      <div className="flex flex-col md:flex-row">
        {/* Poster Image */}
        <div className="relative w-full md:w-32 aspect-[3/4] overflow-hidden">
          {poster_url ? (
            <img 
              src={poster_url} 
              alt={event_name}
              className="w-full h-full object-cover transition-transform hover:scale-110"
              onError={(e) => {
                e.target.style.display = 'none';
                e.target.nextElementSibling.classList.add('flex');
              }}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-purple-500 to-blue-600">
              <span className="text-white/80 text-xs text-center">
                {getCategoryDisplayName(category)}
              </span>
            </div>
          )}
        </div>

        {/* Ticket Details */}
        <div className="flex-1 p-5 flex flex-col justify-between">
          {/* Event Header */}
          <div>
            <h3 className={`font-bold text-lg mb-1 ${categoryColors.text}`}>
              {event_name}
            </h3>
            
            {category && category !== 'uncategorized' && (
              <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${categoryColors.badge} mb-2`}>
                {getCategoryDisplayName(category)}
              </span>
            )}
          </div>

          {/* Venue */}
          <div className="flex items-center gap-2 mb-2">
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span className="text-gray-700 font-medium text-sm">{venue}</span>
          </div>

          {/* Date & Time */}
          <div className="flex items-center gap-2 mb-2">
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span className="text-gray-700 font-medium text-sm">
              {formatDateTime(show_date, show_time)}
            </span>
          </div>

          {/* Seats */}
          <div className="flex items-center gap-2 mb-3">
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 10l4.588 4.588a2 2 0 002.929-2.929L17 7.5l3-3-3-3 4.588 4.588a2 2 0 012.929 2.929L22 7.5l-3-3-3 3-4.588 4.588z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 12h14" />
            </svg>
            <span className="text-gray-700 font-medium text-sm">{formatSeats(seats)}</span>
          </div>

          {/* Amount */}
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 13a2 2 0 110-4 2 2 0 010 4zm9-8h-2" />
            </svg>
            <span className={`text-xl font-bold ${categoryColors.text}`}>
              {formatCurrency(amount_paid)}
            </span>
          </div>
        </div>
      </div>

      {/* Parsing Info Footer */}
      {parsing_notes && (
        <div className={`mt-3 pt-3 border-t ${isValid.isValid ? 'border-gray-200' : 'border-red-200'}`}>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span className={`px-2 py-0.5 rounded ${isValid.isValid ? 'bg-gray-100' : 'bg-red-100'}`}>
              {isValid.isValid ? '✓' : '⚠'}
              {parsing_notes}
            </span>
          </div>
          {isLowConfidence && (
            <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800">
              ⚠️ Low confidence - venue/category was cleaned by Ollama
            </div>
          )}
        </div>
      )}
    </div>
  );
}