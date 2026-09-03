import Link from "next/link";
import type { ReactNode } from "react";
import type { Verdict } from "@/lib/types";

/* Small presentational primitives shared by every screen. No state, no data. */

export function PageHeader({
  eyebrow,
  title,
  sub,
  subClassName,
}: {
  eyebrow?: string;
  title: string;
  sub?: ReactNode;
  subClassName?: string;
}) {
  return (
    <>
      {eyebrow && <p className="eyebrow">{eyebrow}</p>}
      <h2 className="h2">{title}</h2>
      {sub && <p className={`sub ${subClassName ?? ""}`}>{sub}</p>}
    </>
  );
}

export function Card({ children, className, style }: { children: ReactNode; className?: string; style?: React.CSSProperties }) {
  return (
    <div className={`card ${className ?? ""}`} style={style}>
      {children}
    </div>
  );
}

export function SectionHead({ children, aside }: { children: ReactNode; aside?: ReactNode }) {
  return (
    <div className="secthead">
      <span>{children}</span>
      {aside && <span style={{ fontWeight: 400, color: "var(--ink3)" }}>{aside}</span>}
    </div>
  );
}

export function Tag({ verdict, children, large }: { verdict: Verdict; children: ReactNode; large?: boolean }) {
  return (
    <span className={`tag ${verdict}`} style={large ? { fontSize: 12.5, padding: "5px 11px" } : undefined}>
      <i className="dot" />
      {children}
    </span>
  );
}

type ButtonVariant = { ghost?: boolean; sm?: boolean };

function btnClass({ ghost, sm }: ButtonVariant) {
  return ["btn", ghost && "ghost", sm && "sm"].filter(Boolean).join(" ");
}

export function ButtonLink({ href, children, ghost, sm, style }: ButtonVariant & { href: string; children: ReactNode; style?: React.CSSProperties }) {
  return (
    <Link href={href} className={btnClass({ ghost, sm })} style={style}>
      {children}
    </Link>
  );
}

export function Button({
  children,
  ghost,
  sm,
  onClick,
  disabled,
  style,
  type = "button",
}: ButtonVariant & {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  style?: React.CSSProperties;
  type?: "button" | "submit";
}) {
  return (
    <button type={type} className={btnClass({ ghost, sm })} onClick={onClick} disabled={disabled} style={style}>
      {children}
    </button>
  );
}

export function Nav({ children }: { children: ReactNode }) {
  return <div className="nav">{children}</div>;
}

export function Highlight({ children }: { children: ReactNode }) {
  return (
    <div className="mono">
      <span className="mark">{children}</span>
    </div>
  );
}

export const VERDICT_COLORS: Record<Verdict, [string, string]> = {
  v: ["var(--verify-bg)", "var(--verify)"],
  c: ["var(--caution-bg)", "var(--caution)"],
  b: ["var(--block-bg)", "var(--block)"],
};
