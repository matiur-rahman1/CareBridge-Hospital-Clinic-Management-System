import { describe, expect, it } from 'vitest';
import { initials, statusTone, titleCase, timeLabel } from './format';

describe('CareBridge display formatters', () => {
  it('builds initials from a full name', () => {
    expect(initials('Ayesha Rahman')).toBe('AR');
  });
  it('maps workflow states to readable status tones', () => {
    expect(statusTone('PARTIALLY_PAID')).toBe('warning');
    expect(statusTone('COMPLETED')).toBe('success');
  });
  it('formats enum labels', () => {
    expect(titleCase('BANK_TRANSFER')).toBe('Bank Transfer');
  });
  it('formats 24-hour appointment times', () => {
    expect(timeLabel('14:30:00')).toMatch(/2:30/);
  });
});
