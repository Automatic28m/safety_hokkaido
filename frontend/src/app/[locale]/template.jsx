'use client';

export default function Template({ children }) {
  return (
    <div className="animate-fade-in-up opacity-0">
      {children}
    </div>
  );
}
