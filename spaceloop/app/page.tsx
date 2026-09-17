import Link from "next/link";
export default function Home() {
  return (
    <main className="flex flex-col items-center justify-center min-h-screen px-4 text-center">
      <h1 className="text-5xl font-black mb-4">SpaceLoop</h1>
      <p className="text-gray-600 max-w-md mb-8">Match unused spaces with temporary seekers instantly using AI.</p>
      <div className="flex gap-4">
        <Link href="/search" className="bg-black text-white px-6 py-3 rounded-lg font-medium">Find a Space</Link>
      </div>
    </main>
  );
}