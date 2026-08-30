import React, { useState, useMemo } from 'react';
import {
  CATEGORY_COLORS,
  getCategoryDisplayName,
  sortTicketsByDate,
  sortTicketsByAmount,
  aggregateByCategory
} from '../utils/ticketHelpers.js';
import TicketCard from './TicketCard.jsx';

/**
 * Gallery - Displays tickets in a responsive grid with filtering and sorting
 */
export default function Gallery() {
  // State management
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    categories: [],
    years: []
  });
  const [sortBy, setSortBy] = useState('date'); // date | amount | name | alphabet

  // Load tickets from public/tickets.json
  React.useEffect(() => {
    const loadTickets = async () => {
      try {
        const response = await fetch('/tickets.json');
        if (!response.ok) {
          throw new Error('Failed to load tickets');
        }
        const data = await response.json();
        setTickets(data);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    loadTickets();
  }, []);

  // Filtering and sorting logic
  const filteredAndSortedTickets = useMemo(() => {
    let result = [...tickets];

    // Filter by category
    if (filters.categories.length > 0) {
      result = result.filter(t => 
        filters.categories.includes(t.category) || 
        filters.categories.includes(t.category?.replace('theatre', 'play')) // group play with theatre
      );
    }

    // Filter by year
    if (filters.years.length > 0) {
      result = result.filter(t => {
        const year = t.show_date?.split('-')[0];
        return filters.years.includes(parseInt(year));
      });
    }

    // Sort
    if (sortBy === 'date') {
      result = sortTicketsByDate(result);
    } else if (sortBy === 'amount') {
      result = sortTicketsByAmount(result);
    } else if (sortBy === 'name') {
      result.sort((a, b) => a.event_name.localeCompare(b.event_name));
    }

    return result;
  }, [tickets, filters, sortBy]);

  // Statistics
  const stats = useMemo(() => {
    const allCategories = new Set(tickets.map(t => t.category));
    const allYears = new Set(tickets.map(t => t.show_date?.split('-')[0]));
    return {
      total: tickets.length,
      categories: Array.from(allCategories),
      years: Array.from(allYears).sort((a, b) => b - a)
    };
  }, [tickets]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-black">
      {/* Header */}
      <header className="bg-gray-950 border-b border-gray-800 py-6 px-4 md:px-8">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">
            🎟️ BookMyShow Ticket Gallery
          </h1>
          <p className="text-gray-400 text-sm">
            Personal bookings from my Gmail — scraped, enriched, and displayed
          </p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-4 md:p-6">
        {/* Loading State */}
        {loading && (
          <div className="py-12 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-primary-500 border-t-transparent"></div>
            <p className="mt-4 text-gray-400">Loading your tickets...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="py-12 text-center">
            <div className="inline-block text-red-500 mb-4">
              <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.66 1.752-3.075l-3.75-8.25A2 2 0 006.938 6h10.624c1.54 0 2.502 1.66 1.752 3.075l-3.75 8.25A2 2 0 0012 17z" />
              </svg>
            </div>
            <p className="text-red-400 text-sm">{error}</p>
            <p className="mt-2 text-gray-500 text-xs">Make sure public/tickets.json exists</p>
          </div>
        )}

        {/* Results */}
        {!loading && !error && (
          <>
            {/* Stats Bar */}
            <div className="mb-6 grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
                <p className="text-gray-400 text-xs uppercase">Total Tickets</p>
                <p className="text-2xl font-bold text-white">{stats.total}</p>
              </div>
              <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
                <p className="text-gray-400 text-xs uppercase">Categories</p>
                <p className="text-2xl font-bold text-white">{stats.categories.length}</p>
              </div>
              <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
                <p className="text-gray-400 text-xs uppercase">Years</p>
                <p className="text-2xl font-bold text-white">{stats.years.length}</p>
              </div>
              <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
                <p className="text-gray-400 text-xs uppercase">Est. Total Spend</p>
                <p className="text-2xl font-bold text-primary-500">
                  ₹{tickets.reduce((sum, t) => sum + (parseFloat(t.amount_paid) || 0), 0).toLocaleString('en-IN')}
                </p>
              </div>
            </div>

            {/* Filter Controls */}
            <div className="mb-6 flex flex-wrap gap-4 items-center">
              {/* Category Filter */}
              <div className="flex flex-wrap gap-2">
                <span className="text-gray-400 text-sm uppercase font-medium">Category:</span>
                <button
                  onClick={() => {
                    const newFilters = { ...filters, categories: filters.categories.length === 7 ? [] : [...filters.categories, 'all'] };
                    setFilters(newFilters);
                    setFilteredAndSortedTickets((prev) => prev);
                  }}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                    filters.categories.length === 7
                      ? 'bg-white text-black'
                      : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                  }`}
                >
                  All
                </button>
                {stats.categories.map(cat => (
                  <button
                    key={cat}
                    onClick={() => {
                      const newFilters = { ...filters };
                      const catIndex = newFilters.categories.indexOf(cat);
                      if (catIndex === -1) {
                        newFilters.categories.push(cat);
                      } else {
                        newFilters.categories.splice(catIndex, 1);
                      }
                      setFilters(newFilters);
                      setFilteredAndSortedTickets(prev => prev);
                    }}
                    className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                      filters.categories.includes(cat)
                        ? CATEGORY_COLORS[cat]?.badge || 'bg-gray-700'
                        : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>

              <span className="text-gray-400 text-sm uppercase font-medium">Sort by:</span>
              <select
                value={sortBy}
                onChange={(e) => {
                  setSortBy(e.target.value);
                  setFilteredAndSortedTickets(prev => prev);
                }}
                className="bg-gray-900 border border-gray-700 text-white text-sm rounded px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="date">Date (Newest)</option>
                <option value="amount">Amount (High)</option>
                <option value="name">Name (A-Z)</option>
                <option value="alphabet">Alphabetical</option>
              </select>
            </div>

            {/* Ticket Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {filteredAndSortedTickets.length === 0 ? (
                <div className="col-span-full py-12 text-center text-gray-500">
                  No tickets matching your filters
                </div>
              ) : (
                filteredAndSortedTickets.map((ticket) => (
                  <TicketCard key={ticket.booking_id} ticket={ticket} />
                ))
              )}
            </div>

            {/* Category Breakdown */}
            <div className="mt-8 pt-6 border-t border-gray-800">
              <h2 className="text-xl font-bold text-gray-200 mb-4">Category Breakdown</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(aggregateByCategory(tickets)).map(([category, data]) => (
                  <div
                    key={category}
                    className="bg-gray-900 rounded-lg p-4 border border-gray-800 hover:border-gray-700 transition-colors"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <div className={`w-3 h-3 rounded-full ${CATEGORY_COLORS[category]?.background || 'bg-gray-700'}`}></div>
                      <span className="text-gray-300 font-medium">{category}</span>
                    </div>
                    <div className="text-sm text-gray-400">
                      <p>Count: <span className="text-white">{data.count}</span></p>
                      <p>Avg Amount: <span className="text-primary-400">{formatCurrency(data.averageAmount)}</span></p>
                      <p>Years: {data.years.join(', ')}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}