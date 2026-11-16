import { describe, expect, it } from 'vitest';
import { buildAvailableSlots, djangoWeekdayForDate } from './schedule';

describe('doctor availability scheduling', () => {
  it('maps Monday through Sunday to Django weekday indexes 0 through 6', () => {
    expect(djangoWeekdayForDate('2026-11-16')).toBe(0); // Monday
    expect(djangoWeekdayForDate('2026-11-17')).toBe(1);
    expect(djangoWeekdayForDate('2026-11-22')).toBe(6); // Sunday
  });

  it('builds slots for the selected weekday and excludes overlapping bookings', () => {
    const availability = [{ doctor: 4, weekday: 6, start_time: '09:00:00', end_time: '10:00:00', slot_minutes: 30, is_active: true }];
    const appointments = [{ doctor: 4, appointment_date: '2026-11-22', start_time: '09:00:00', end_time: '09:30:00', status: 'CONFIRMED' }];
    const slots = buildAvailableSlots({ availability, appointments, doctorId: 4, date: '2026-11-22' });
    expect(slots).toEqual([{ value: '09:30:00|10:00:00', start_time: '09:30:00', end_time: '10:00:00' }]);
  });

  it('does not treat cancelled visits as slot conflicts', () => {
    const availability = [{ doctor: 4, weekday: 0, start_time: '09:00:00', end_time: '09:30:00', slot_minutes: 30, is_active: true }];
    const appointments = [{ doctor: 4, appointment_date: '2026-11-16', start_time: '09:00:00', end_time: '09:30:00', status: 'CANCELLED' }];
    expect(buildAvailableSlots({ availability, appointments, doctorId: 4, date: '2026-11-16' })).toHaveLength(1);
  });
});
