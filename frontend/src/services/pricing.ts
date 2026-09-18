/**
 * SpaceLoop Centralized Pricing & Duration Calculation Engine
 * 
 * Ensures the exact same numeric calculations and validation bounds (0.5 to 168 hours)
 * are used consistently across UI cards, detail pages, booking payloads, and backend verification.
 */

export interface PricingBreakdown {
  hours: number;
  hourlyRate: number;
  rentalSubtotal: number;
  platformFee: number;
  escrowDeposit: number;
  grandTotal: number;
  isValidDuration: boolean;
  validationError?: string;
}

export const MIN_BOOKING_HOURS = 0.5;
export const MAX_BOOKING_HOURS = 168.0; // 7 days maximum micro-lease
export const DEFAULT_BOOKING_HOURS = 2.0;
export const PLATFORM_FEE_PERCENT = 0.05; // 5% platform fee
export const UPI_ESCROW_DEPOSIT = 100.0; // Flat ₹100 automated UPI security escrow

export function validateDuration(hours: number | string): { isValid: boolean; normalizedHours: number; error?: string } {
  const num = typeof hours === 'string' ? parseFloat(hours) : hours;
  if (isNaN(num) || num < MIN_BOOKING_HOURS || num > MAX_BOOKING_HOURS) {
    return {
      isValid: false,
      normalizedHours: isNaN(num) ? DEFAULT_BOOKING_HOURS : num,
      error: `Invalid duration: hours must be between ${MIN_BOOKING_HOURS} and ${MAX_BOOKING_HOURS}.`,
    };
  }
  return {
    isValid: true,
    normalizedHours: Math.round(num * 10) / 10,
  };
}

export function calculateRentalPricing(hourlyRate: number, requestedHours: number | string): PricingBreakdown {
  const rate = Math.max(0, Number(hourlyRate) || 0);
  const validation = validateDuration(requestedHours);
  const hours = validation.normalizedHours;

  const rentalSubtotal = Math.round(rate * hours * 100) / 100;
  const platformFee = Math.round(rentalSubtotal * PLATFORM_FEE_PERCENT * 100) / 100;
  const escrowDeposit = UPI_ESCROW_DEPOSIT;
  const grandTotal = Math.round((rentalSubtotal + platformFee + escrowDeposit) * 100) / 100;

  return {
    hours,
    hourlyRate: rate,
    rentalSubtotal,
    platformFee,
    escrowDeposit,
    grandTotal,
    isValidDuration: validation.isValid,
    validationError: validation.error,
  };
}

export function safeParseDate(input: Date | string | number | null | undefined): Date | null {
  if (!input) return null;
  if (input instanceof Date) return isNaN(input.getTime()) ? null : input;
  if (typeof input === 'number') {
    const d = new Date(input);
    return isNaN(d.getTime()) ? null : d;
  }
  if (typeof input === 'string') {
    const trimmed = input.trim();
    if (!trimmed) return null;
    let d = new Date(trimmed);
    if (!isNaN(d.getTime())) return d;
    // Handle python strftime format e.g. "Sep 18, 2026 at 05:18 AM"
    d = new Date(trimmed.replace(/\s+at\s+/gi, ' '));
    if (!isNaN(d.getTime())) return d;
  }
  return null;
}

export function formatTimeWindow(
  startDate: Date | string | number | null | undefined,
  hours: number,
  explicitEndDate?: Date | string | number | null | undefined
): {
  startFormatted: string;
  endFormatted: string;
  durationFormatted: string;
  fullWindow: string;
} {
  const parsedStart = safeParseDate(startDate);
  const validStart = parsedStart || new Date();
  
  const parsedEnd = safeParseDate(explicitEndDate);
  const end = parsedEnd || new Date(validStart.getTime() + (Number(hours) || 2) * 3600 * 1000);

  const formatOpts: Intl.DateTimeFormatOptions = {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  };

  const timeOnlyOpts: Intl.DateTimeFormatOptions = {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  };

  const startFormatted = validStart.toLocaleDateString(undefined, formatOpts);
  const endFormatted = end.toLocaleDateString(undefined, formatOpts);
  const endTimeOnly = end.toLocaleTimeString(undefined, timeOnlyOpts);

  const durationFormatted =
    hours >= 1
      ? Number.isInteger(hours)
        ? `${hours} hr${hours > 1 ? 's' : ''}`
        : `${Math.floor(hours)} hr ${Math.round((hours % 1) * 60)} mins`
      : `${Math.round(hours * 60)} mins`;

  const fullWindow = `${startFormatted} → ${endTimeOnly} (${durationFormatted})`;

  return {
    startFormatted,
    endFormatted,
    durationFormatted,
    fullWindow,
  };
}

