"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { UserButton } from "@clerk/nextjs";

const LINKS = [
  { href: "/", label: "People" },
  { href: "/settings", label: "Settings" },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="sidebar">
      <div className="brand">
        Artificial People<span className="dot">.</span>
      </div>
      {LINKS.map((l) => {
        const active = l.href === "/" ? pathname === "/" : pathname?.startsWith(l.href);
        return (
          <Link
            key={l.href}
            href={l.href}
            className={`sidebar-link${active ? " active" : ""}`}
          >
            {l.label}
          </Link>
        );
      })}
      <div className="sidebar-footer">
        <UserButton afterSignOutUrl="/sign-in" />
      </div>
    </aside>
  );
}
