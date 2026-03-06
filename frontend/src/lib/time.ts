export function currentMinuteIso(): string {
  const now = new Date();
  now.setSeconds(0, 0);
  return now.toISOString();
}
