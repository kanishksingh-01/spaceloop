export async function calculateYield(payload: any) {
  const res = await fetch('/api/calculate-yield', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return res.json();
}
