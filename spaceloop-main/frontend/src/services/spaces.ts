export async function scanSpace(payload: any) {
  const res = await fetch('/api/spaces/ai-scan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return res.json();
}
