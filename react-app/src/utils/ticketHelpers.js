/**
 * tickets.json helpers. Gallery is read-only.
 */

export const extractYear = (ticket) => {
  if (ticket?.show_date_iso && /^\d{4}/.test(ticket.show_date_iso)) {
    return ticket.show_date_iso.slice(0, 4);
  }
  const raw = ticket?.show_date_raw || '';
  const match = raw.match(/\b(20\d{2})\b/);
  return match ? match[1] : null;
};

export const formatCurrency = (amount, currency = 'INR') => {
  if (amount === null || amount === undefined || amount === '') return '—';
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  if (Number.isNaN(num)) return '—';
  if (currency === 'INR' || !currency) {
    return `₹${num.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
  }
  return `${currency} ${num.toLocaleString('en-IN')}`;
};

export const formatSeats = (ticket) => {
  if (ticket?.seat_display) return ticket.seat_display;
  if (Array.isArray(ticket?.seats) && ticket.seats.length) {
    return ticket.seats.join(', ');
  }
  return '—';
};

export const formatShowDate = (ticket) => ticket?.show_date_raw || 'Date unknown';

export const cinemaLabel = (ticket) =>
  ticket?.cinema_name || ticket?.cinema_raw || 'Cinema unknown';

export const sortTickets = (tickets, sortBy) => {
  const copy = [...tickets];
  if (sortBy === 'amount') {
    return copy.sort((a, b) => (b.amount || 0) - (a.amount || 0));
  }
  if (sortBy === 'title') {
    return copy.sort((a, b) =>
      (a.movie_title || '').localeCompare(b.movie_title || '')
    );
  }
  if (sortBy === 'cinema') {
    return copy.sort((a, b) => cinemaLabel(a).localeCompare(cinemaLabel(b)));
  }
  return copy.sort((a, b) => {
    const left = a.show_date_iso || a.show_date_raw || '';
    const right = b.show_date_iso || b.show_date_raw || '';
    return right.localeCompare(left);
  });
};

export const uniqueValues = (tickets, getter) => {
  const values = new Set();
  tickets.forEach((ticket) => {
    const value = getter(ticket);
    if (value) values.add(value);
  });
  return Array.from(values).sort();
};

export const totalSpend = (tickets) =>
  tickets.reduce((sum, ticket) => sum + (Number(ticket.amount) || 0), 0);

export default {
  extractYear,
  formatCurrency,
  formatSeats,
  formatShowDate,
  cinemaLabel,
  sortTickets,
  uniqueValues,
  totalSpend,
};
