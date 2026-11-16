/** Convert an ISO date to Django's Monday=0 ... Sunday=6 weekday convention. */
export function djangoWeekdayForDate(dateValue) {
  if (!dateValue) return null;
  const [year, month, day] = String(dateValue).slice(0, 10).split('-').map(Number);
  if (![year, month, day].every(Number.isFinite)) return null;
  const date = new Date(year, month - 1, day);
  return (date.getDay() + 6) % 7;
}

function minutesFromTime(value) {
  const [hours, minutes] = String(value).split(':').map(Number);
  return (hours * 60) + minutes;
}

function formatTime(minutes) {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}:00`;
}

/** Build candidate slots from active availability, excluding visible conflicts.
 * The Django booking endpoint performs the authoritative conflict check.
 */
export function buildAvailableSlots({ availability = [], appointments = [], doctorId, date }) {
  if (!doctorId || !date) return [];
  const weekday = djangoWeekdayForDate(date);
  const activeWindows = availability.filter((item) =>
    String(item.doctor) === String(doctorId) && Number(item.weekday) === weekday && item.is_active
  );
  const slots = [];

  activeWindows.forEach((window) => {
    const start = minutesFromTime(window.start_time);
    const end = minutesFromTime(window.end_time);
    const slotMinutes = Number(window.slot_minutes);
    if (!Number.isFinite(slotMinutes) || slotMinutes <= 0) return;

    for (let cursor = start; cursor + slotMinutes <= end; cursor += slotMinutes) {
      const slotStart = formatTime(cursor);
      const slotEnd = formatTime(cursor + slotMinutes);
      const occupied = appointments.some((appointment) =>
        String(appointment.doctor) === String(doctorId) &&
        appointment.appointment_date === date &&
        appointment.status !== 'CANCELLED' &&
        appointment.start_time < slotEnd && appointment.end_time > slotStart
      );
      if (!occupied) slots.push({ value: `${slotStart}|${slotEnd}`, start_time: slotStart, end_time: slotEnd });
    }
  });

  return slots;
}
