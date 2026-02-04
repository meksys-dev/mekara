import React from "react";

interface BrowserOnlyProps {
  children: () => React.ReactNode;
  fallback?: React.ReactNode;
}

export default function BrowserOnly({ children }: BrowserOnlyProps) {
  return <>{children()}</>;
}
