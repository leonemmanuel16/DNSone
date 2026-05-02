import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DNS One",
  description: "CRM + ERP + Cotizaciones — Data Network Solutions",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
