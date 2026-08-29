import Link from "next/link";
import type { ReactNode } from "react";

import type { PresentationState, WorkspaceId } from "../foundation/types";
import { workspaceById } from "../foundation/workspaces";
import { LanguageSelector } from "./language-selector";

export function Button({ children, variant = "primary", disabled = false, type = "button", onClick }: { children: ReactNode; variant?: "primary" | "secondary" | "quiet" | "destructive"; disabled?: boolean; type?: "button" | "submit"; onClick?: () => void; }) { return <button className={`button button--${variant}`} disabled={disabled} onClick={onClick} type={type}>{children}</button>; }
export function LinkButton({ children, href, variant = "secondary" }: { children: ReactNode; href: string; variant?: "primary" | "secondary" | "quiet"; }) { return <Link className={`button button--${variant}`} href={href}>{children}</Link>; }
export function StatusBadge({ state, children }: { state: PresentationState; children?: ReactNode; }) { return <span className={`status-badge status-badge--${state}`} data-state={state}><span aria-hidden="true" className="status-badge__marker" />{children ?? state.replaceAll("_", " ")}</span>; }
export function Breadcrumb({ items }: { items: readonly { label: string; href?: string }[]; }) { return <nav aria-label="Brotkrümelnavigation" className="breadcrumb"><ol>{items.map((item,index)=><li aria-current={index===items.length-1?"page":undefined} key={item.label}>{item.href?<Link href={item.href}>{item.label}</Link>:item.label}</li>)}</ol></nav>; }
export function PageHeader({ title, description, actions }: { title:string; description?:string; actions?:ReactNode; }) { return <header className="page-header"><div><h1>{title}</h1>{description?<p>{description}</p>:null}</div>{actions?<div className="page-actions">{actions}</div>:null}</header>; }
export function Card({ title, children }: { title?:string; children:ReactNode; }) { return <section className="card">{title?<h2 className="card-title">{title}</h2>:null}{children}</section>; }
export function MetricCard({ value, label }: { value:string; label:string; }) { return <div className="card metric-card"><strong className="metric-number">{value}</strong><span className="metric-label">{label}</span></div>; }
export function Notice({ kind="information", title, children }: { kind?:"information"|"warning"|"danger"|"authority"|"scope"|"legal"; title:string; children:ReactNode; }) { const id=`notice-${title.replaceAll(" ","-")}`; return <section aria-labelledby={id} className={`notice notice--${kind}`}><h2 id={id}>{title}</h2><div>{children}</div></section>; }
export function StatePanel({ state,title,children }: { state:PresentationState; title:string; children:ReactNode; }) { const live=state==="loading"||state==="error"; return <section aria-atomic={live||undefined} aria-live={live?"polite":undefined} className="state-panel" data-state={state}><StatusBadge state={state}/><h2>{title}</h2><div>{children}</div></section>; }
export function FormField({ id,label,hint,error,children }: { id:string; label:string; hint?:string; error?:string; children:ReactNode; }) { const describedBy=[hint?`${id}-hint`:null,error?`${id}-error`:null].filter(Boolean).join(" "); return <div className="form-field"><label htmlFor={id}>{label}</label>{hint?<p id={`${id}-hint`}>{hint}</p>:null}<div data-describedby={describedBy||undefined}>{children}</div>{error?<p className="validation-message" id={`${id}-error`} role="alert">{error}</p>:null}</div>; }
export function SecondaryNavigation({ label,items }: { label:string; items:readonly {label:string;href:string;current?:boolean}[]; }) { return <nav aria-label={label} className="secondary-navigation">{items.map(item=><Link aria-current={item.current?"page":undefined} href={item.href} key={item.label}>{item.label}</Link>)}</nav>; }
export function BackLink({ href,children }: { href:string; children:ReactNode; }) { return <Link className="back-link" href={href}><span aria-hidden="true">←</span> {children}</Link>; }
export function MetadataList({ items }: { items:readonly {term:string;description:ReactNode}[]; }) { return <dl className="metadata-list">{items.map(item=><div key={item.term}><dt>{item.term}</dt><dd>{item.description}</dd></div>)}</dl>; }
export function StructuredList({children}:{children:ReactNode}) { return <ul className="structured-list">{children}</ul>; }
export function AccessibleTableContainer({label,children}:{label:string;children:ReactNode}) { return <div aria-label={label} className="table-container" role="region" tabIndex={0}>{children}</div>; }
export function SearchField({id,label,placeholder}:{id:string;label:string;placeholder?:string}) { return <div className="form-field search-field"><label htmlFor={id}>{label}</label><input id={id} name={id} placeholder={placeholder} type="search" /></div>; }
export function FilterGroup({legend,children}:{legend:string;children:ReactNode}) { return <fieldset className="filter-group"><legend>{legend}</legend>{children}</fieldset>; }
export function RestrictedContentNotice({children}:{children:ReactNode}) { return <Notice kind="authority" title="Eingeschränkter Inhalt">{children}</Notice>; }
export function StaleDataWarning({children}:{children:ReactNode}) { return <Notice kind="warning" title="Daten möglicherweise veraltet">{children}</Notice>; }
export function CandidateBanner({source}:{source?:string}) { return <aside className="candidate-banner" aria-label="Candidate-Hinweis"><strong>FRONT-00 Implementation Candidate</strong><span>Nicht produktiv · nicht mit einem Backend verbunden{source?` · visuelle Migration von ${source}`:""}</span></aside>; }
export function ProvenancePanel({source,version,correctionHref}:{source:string;version:string;correctionHref:string}) { return <aside className="provenance" aria-label="Herkunft und Korrekturen"><dl><div><dt>Quelle</dt><dd>{source}</dd></div><div><dt>Version</dt><dd>{version}</dd></div></dl><Link href={correctionHref}>Korrektur melden</Link></aside>; }
export function Tabs({items}:{items:readonly {label:string;href:string;current?:boolean}[]}) { return <nav aria-label="Bereiche" className="tabs">{items.map(item=><Link aria-current={item.current?"page":undefined} className="tab" href={item.href} key={item.href}>{item.label}</Link>)}</nav>; }
export function Pagination({current,total}:{current:number;total:number}) { return <nav aria-label="Seitennavigation" className="pagination"><Button disabled={current<=1} variant="quiet">Zurück</Button><span aria-live="polite">Seite {current} von {total}</span><Button disabled={current>=total} variant="quiet">Weiter</Button></nav>; }

export function WorkspaceShell({ workspaceId, children }: { workspaceId: WorkspaceId; children: ReactNode; }) {
  const workspace = workspaceById(workspaceId);
  return (
    <div className={`app-shell app-shell--${workspace.shell}`} data-workspace={workspace.id}>
      <a className="skip-link" href="#main-content">Zum Inhalt springen</a>
      <header className="site-header">
        <Link className="logo" href="/">EPD²</Link>
        <div className="workspace-heading"><span>{workspace.name}</span><StatusBadge state={workspace.activation === "planned" ? "planned" : "prototype"} /></div>
        <nav aria-label="Hauptnavigation" className="primary-navigation"><Link href="/foundation">Foundation</Link><Link href="/foundation/examples/public">Beispiele</Link></nav>
        <LanguageSelector />
      </header>
      <main className="main" id="main-content" tabIndex={-1}>{children}</main>
      <footer className="footer"><span>EPD² Civic OS</span><span>FRONT-02 Implementation Candidate — nicht akzeptiert · keine Produktionsverbindung</span></footer>
    </div>
  );
}
