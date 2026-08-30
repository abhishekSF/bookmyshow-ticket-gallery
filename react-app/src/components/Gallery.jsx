import React, { useEffect, useMemo, useState } from 'react';
import TicketCard from './TicketCard.jsx';
import Loading from './Loading.jsx';
import {
  cinemaLabel,
  extractYear,
  formatCurrency,
  sortTickets,
  totalSpend,
  uniqueValues,
} from '../utils/ticketHelpers.js';

export default function Gallery() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [year, setYear] = useState('all');
  const [cinema, setCinema] = useState('all');
  const [city, setCity] = useState('all');
  const [sortBy, setSortBy] = useState('date');

  useEffect(() => {
    const load = async () => {
      try {
        const response = await fetch('/tickets.json');
        if (!response.ok) {
          throw new Error('Could not read tickets.json');
        }
        const data = await response.json();
        const list = Array.isArray(data) ? data : data.tickets || [];
        setTickets(list);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const years = useMemo(
    () => uniqueValues(tickets, extractYear),
    [tickets]
  );
  const cinemas = useMemo(
    () => uniqueValues(tickets, cinemaLabel),
    [tickets]
  );
  const cities = useMemo(
    () => uniqueValues(tickets, (ticket) => ticket.city),
    [tickets]
  );

  const visible = useMemo(() => {
    const filtered = tickets.filter((ticket) => {
      if (year !== 'all' && extractYear(ticket) !== year) return false;
      if (cinema !== 'all' && cinemaLabel(ticket) !== cinema) return false;
      if (city !== 'all' && ticket.city !== city) return false;
      return true;
    });
    return sortTickets(filtered, sortBy);
  }, [tickets, year, cinema, city, sortBy]);

  if (loading) {
    return <Loading />;
  }

  if (error) {
    return (
      <div className="min-h-screen bg-black text-zinc-200 flex items-center justify-center p-8">
        <p>{error}. Export tickets.json into react-app/public/.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-black via-zinc-950 to-neutral-950 text-zinc-100">
      <header className="border-b border-zinc-800 px-6 py-8">
        <div className="max-w-6xl mx-auto">
          <p className="text-xs uppercase tracking-[0.25em] text-amber-500 mb-2">
            Personal archive
          </p>
          <h1 className="text-3xl md:text-4xl font-semibold">Theatre gallery</h1>
          <p className="text-zinc-400 mt-2 max-w-2xl">
            Movie bookings from one mailbox. The gallery only reads tickets.json.
          </p>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <Stat label="Tickets" value={tickets.length} />
          <Stat label="On screen" value={visible.length} />
          <Stat label="Cities" value={cities.length} />
          <Stat
            label="Spend"
            value={formatCurrency(totalSpend(tickets))}
          />
        </div>

        <div className="flex flex-wrap gap-3 mb-8 items-center">
          <Filter
            label="Year"
            value={year}
            onChange={setYear}
            options={years}
          />
          <Filter
            label="Cinema"
            value={cinema}
            onChange={setCinema}
            options={cinemas}
          />
          <Filter
            label="City"
            value={city}
            onChange={setCity}
            options={cities}
          />
          <label className="text-sm text-zinc-400 flex items-center gap-2">
            Sort
            <select
              value={sortBy}
              onChange={(event) => setSortBy(event.target.value)}
              className="bg-zinc-900 border border-zinc-700 rounded px-2 py-1 text-zinc-100"
            >
              <option value="date">Date</option>
              <option value="amount">Amount</option>
              <option value="title">Title</option>
              <option value="cinema">Cinema</option>
            </select>
          </label>
        </div>

        {visible.length === 0 ? (
          <p className="text-zinc-500 py-16 text-center">No tickets match these filters.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {visible.map((ticket) => (
              <TicketCard
                key={ticket.booking_id || ticket.source_message_id}
                ticket={ticket}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
      <p className="text-[11px] uppercase tracking-wide text-zinc-500">{label}</p>
      <p className="text-2xl font-semibold mt-1">{value}</p>
    </div>
  );
}

function Filter({ label, value, onChange, options }) {
  return (
    <label className="text-sm text-zinc-400 flex items-center gap-2">
      {label}
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="bg-zinc-900 border border-zinc-700 rounded px-2 py-1 text-zinc-100 max-w-[12rem]"
      >
        <option value="all">All</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}
