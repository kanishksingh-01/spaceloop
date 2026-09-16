export async function verifyStudent(payload: any) {
  const res = await fetch('/api/verify/student', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return res.json();
}

export async function verifyHost(payload: any) {
  const res = await fetch('/api/verify/host', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return res.json();
}
