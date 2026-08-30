/**
 * Ticket Gallery Utilities
 * 
 * Helper functions for date formatting, category styling, etc.
 */

/**
 * Category colors for styling ticket cards
 * Each category has a background, text, and accent color
 */
export const CATEGORY_COLORS = {
  movie: {
    background: 'bg-primary-950',
    text: 'text-primary-50',
    border: 'border-primary-700',
    badge: 'bg-primary-700'
  },
  concert: {
    background: 'bg-yellow-950',
    text: 'text-yellow-50',
    border: 'border-yellow-700',
    badge: 'bg-yellow-700'
  },
  sports: {
    background: 'bg-orange-950',
    text: 'text-orange-50',
    border: 'border-orange-700',
    badge: 'bg-orange-700'
  },
  comedy: {
    background: 'bg-purple-950',
    text: 'text-purple-50',
    border: 'border-purple-700',
    badge: 'bg-purple-700'
  },
  play: {
    background: 'bg-pink-950',
    text: 'text-pink-50',
    border: 'border-pink-700',
    badge: 'bg-pink-700'
  },
  theatre: {
    background: 'bg-red-950',
    text: 'text-red-50',
    border: 'border-red-700',
    badge: 'bg-red-700'
  },
  uncategorized: {
    background: 'bg-gray-950',
    text: 'text-gray-50',
    border: 'border-gray-700',
    badge: 'bg-gray-700'
  }
};

/**
 * Get the display name for a category
 */
export const getCategoryDisplayName = (category) => {
  const displayNames = {
    movie: 'Movie',
    concert: 'Concert',
    sports: 'Sports',
    comedy: 'Comedy',
    play: 'Play',
    theatre: 'Theatre',
    uncategorized: 'Uncategorized'
  };
  return displayNames[category] || 'Unknown';
};

/**
 * Format date for display
 * @param {string} dateStr - Date string in format "DD Month YYYY" or "YYYY-MM-DD"
 * @param {string} timeStr - Time string (optional)
 * @returns {string} Formatted date string
 */
export const formatDate = (dateStr, timeStr = null) => {
  if (!dateStr) return '';
  
  // Handle various date formats
  if (dateStr.includes(' ')) {
    // Format: "15 January 2025"
    return dateStr;
  }
  
  // Format: "2025-01-15"
  const [year, month, day] = dateStr.split('-');
  const months = {
    '01': 'January', '02': 'February', '03': 'March', '04': 'April',
    '05': 'May', '06': 'June', '07': 'July', '08': 'August',
    '09': 'September', '10': 'October', '11': 'November', '12': 'December'
  };
  
  const monthName = months[month] || month;
  const formattedDate = `${day} ${monthName} ${year}`;
  
  if (timeStr) {
    return `${formattedDate} at ${timeStr}`;
  }
  
  return formattedDate;
};

/**
 * Format currency (INR)
 * @param {string|number} amount - Amount value
 * @returns {string} Formatted currency string
 */
export const formatCurrency = (amount) => {
  if (!amount) return '₹--';
  
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  if (isNaN(num)) return '₹--';
  
  return `₹${num.toLocaleString('en-IN', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  })}`;
};

/**
 * Format seats display
 * @param {string} seats - Seat string (e.g., "12", "A5", "12-15")
 * @returns {string} Formatted seats display
 */
export const formatSeats = (seats) => {
  if (!seats) return '--';
  
  if (seats.includes('-')) {
    return `Seats ${seats}`;
  }
  
  return `Seat ${seats}`;
};

/**
 * Format show date and time together
 * @param {string} dateStr - Date string
 * @param {string} timeStr - Time string
 * @returns {string} Combined date/time string
 */
export const formatDateTime = (dateStr, timeStr = null) => {
  const date = formatDate(dateStr, timeStr);
  return date;
};

/**
 * Validate ticket data structure
 * Returns an object with validation results
 */
export const validateTicket = (ticket) => {
  const issues = [];
  const requiredFields = ['booking_id', 'event_name', 'venue', 'show_date', 'amount_paid'];
  
  requiredFields.forEach(field => {
    if (!ticket[field] || ticket[field] === null || ticket[field] === undefined) {
      issues.push(`Missing ${field}`);
    }
  });
  
  const isValid = issues.length === 0;
  
  return {
    isValid,
    issues,
    confidence: ticket.confidence || 0
  };
};

/**
 * Get year from date string
 * @param {string} dateStr - Date string
 * @returns {string|null} Year or null
 */
export const getYear = (dateStr) => {
  if (!dateStr) return null;
  
  if (dateStr.includes(' ')) {
    const lastPart = dateStr.split(' ').pop();
    const yearMatch = lastPart.match(/^(\d{4})/);
    return yearMatch ? yearMatch[1] : null;
  }
  
  return dateStr.split('-')[0];
};

/**
 * Get time period (AM/PM) from time string
 * @param {string} timeStr - Time string
 * @returns {string|null} AM or PM or null
 */
export const getTimePeriod = (timeStr) => {
  if (!timeStr) return null;
  
  const periodMatch = timeStr.match(/[AaPp][Mm]/);
  return periodMatch ? periodMatch[0] : null;
};

/**
 * Check if date is in a given year
 * @param {string} dateStr - Date string
 * @param {number} year - Year to check against
 * @returns {boolean}
 */
export const isDateInYear = (dateStr, year) => {
  const extractedYear = getYear(dateStr);
  return extractedYear === String(year);
};

/**
 * Sort tickets by date (descending)
 * @param {Array} tickets - Array of ticket objects
 * @returns {Array} Sorted tickets
 */
export const sortTicketsByDate = (tickets) => {
  return [...tickets].sort((a, b) => {
    const dateA = new Date(a.show_date);
    const dateB = new Date(b.show_date);
    return dateB - dateA;
  });
};

/**
 * Sort tickets by amount (descending)
 * @param {Array} tickets - Array of ticket objects
 * @returns {Array} Sorted tickets
 */
export const sortTicketsByAmount = (tickets) => {
  return [...tickets].sort((a, b) => {
    const amountA = parseFloat(a.amount_paid) || 0;
    const amountB = parseFloat(b.amount_paid) || 0;
    return amountB - amountA;
  });
};

/**
 * Aggregate tickets by category
 * @param {Array} tickets - Array of ticket objects
 * @returns {Object} Category statistics
 */
export const aggregateByCategory = (tickets) => {
  const stats = {};
  
  tickets.forEach(ticket => {
    const category = ticket.category || 'uncategorized';
    if (!stats[category]) {
      stats[category] = {
        count: 0,
        totalAmount: 0,
        venues: new Set(),
        years: new Set()
      };
    }
    
    stats[category].count += 1;
    stats[category].totalAmount += parseFloat(ticket.amount_paid) || 0;
    if (ticket.venue && ticket.venue !== 'Unknown') {
      stats[category].venues.add(ticket.venue);
    }
    const year = getYear(ticket.show_date);
    if (year) {
      stats[category].years.add(year);
    }
  });
  
  // Convert Sets to arrays and calculate averages
  Object.keys(stats).forEach(key => {
    stats[key].venues = Array.from(stats[key].venues);
    stats[key].years = Array.from(stats[key].years);
    stats[key].averageAmount = stats[key].totalAmount / stats[key].count;
  });
  
  return stats;
};

/**
 * Aggregate tickets by venue
 * @param {Array} tickets - Array of ticket objects
 * @returns {Object} Venue statistics
 */
export const aggregateByVenue = (tickets) => {
  const stats = {};
  
  tickets.forEach(ticket => {
    const venue = ticket.venue || 'Unknown';
    if (!stats[venue]) {
      stats[venue] = {
        count: 0,
        totalAmount: 0,
        categories: new Set()
      };
    }
    
    stats[venue].count += 1;
    stats[venue].totalAmount += parseFloat(ticket.amount_paid) || 0;
    if (ticket.category) {
      stats[venue].categories.add(ticket.category);
    }
  });
  
  // Convert Sets to arrays and calculate averages
  Object.keys(stats).forEach(key => {
    stats[key].categories = Array.from(stats[key].categories);
    stats[key].averageAmount = stats[key].totalAmount / stats[key].count;
  });
  
  return stats;
};

export default {
  CATEGORY_COLORS,
  getCategoryDisplayName,
  formatDate,
  formatCurrency,
  formatSeats,
  formatDateTime,
  validateTicket,
  getYear,
  getTimePeriod,
  isDateInYear,
  sortTicketsByDate,
  sortTicketsByAmount,
  aggregateByCategory,
  aggregateByVenue
};