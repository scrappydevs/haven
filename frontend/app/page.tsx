'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to dashboard on load
    router.replace('/dashboard');
  }, [router]);

  return (
    <div className="h-screen flex items-center justify-center bg-background">
      <div className="text-center">
        <h1 className="text-2xl font-light text-neutral-950 mb-2">Haven</h1>
        <p className="text-sm font-light text-neutral-500">Loading...</p>
      </div>
    </div>
  );
}
