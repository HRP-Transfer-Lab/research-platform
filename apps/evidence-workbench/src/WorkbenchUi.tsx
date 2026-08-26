import type { ReactNode } from 'react'
import { RefreshCw } from 'lucide-react'
import { bucketLabel, humanize } from './workbench'

export function NavButton({ active, onClick, icon, label }: { active: boolean; onClick: () => void; icon: ReactNode; label: string }) { return <button className={`nav-button ${active ? 'active' : ''}`} onClick={onClick}>{icon}<span>{label}</span></button> }
export function Metric({ icon, label, value, compact }: { icon: ReactNode; label: string; value: string | number; compact?: boolean }) { return <div className="metric-card"><div className="metric-icon">{icon}</div><div><div className={`metric-value ${compact ? 'compact-value' : ''}`}>{value}</div><div className="metric-label">{label}</div></div></div> }
export function BucketPill({ bucket }: { bucket: string }) { const cls = bucket.startsWith('A_') ? 'direct' : bucket.startsWith('B_') ? 'mechanism' : 'ai'; return <span className={`bucket-pill ${cls}`}>{bucketLabel(bucket)}</span> }
export function RoutePill({ route }: { route: string }) { return <span className="route-pill">{humanize(route)}</span> }
export function EvidenceRolePill({ role }: { role: string }) { return <span className="rung-pill">{humanize(role)}</span> }
export function ControllerPill({ controller }: { controller: string }) { return <span className="status-pill">{humanize(controller)}</span> }
export function DetailSection({ title, icon, action, children }: { title: string; icon: ReactNode; action?: ReactNode; children: ReactNode }) { return <section className="detail-section"><div className="section-heading"><div>{icon}<h3>{title}</h3></div>{action}</div>{children}</section> }
export function Info({ label, value }: { label: string; value?: string | number | null }) { return <div className="info-item"><span>{label}</span><strong>{value ?? 'Not extracted'}</strong></div> }
export function Dose({ label, value, max }: { label: string; value: number | null; max: number | null }) { const text = value == null ? '—' : max != null && max !== value ? `${value}–${max}` : String(value); return <div className="dose-chip"><span>{label}</span><strong>{text}</strong></div> }
export function EmptyLine({ children }: { children: ReactNode }) { return <div className="empty-line">{children}</div> }
export function EditInput({ label, value, onChange, type = 'text' }: { label: string; value: string; onChange: (v: string) => void; type?: string }) { return <label><span className="field-label">{label}</span><input className="text-input" type={type} value={value} onChange={(e) => onChange(e.target.value)} /></label> }
export function SelectField({ label, value, onChange, options }: { label: string; value: string; onChange: (v: string) => void; options: [string, string][] }) { return <label className="select-field"><span className="field-label">{label}</span><select className="select-input" value={value} onChange={(e) => onChange(e.target.value)}>{options.map(([v, l]) => <option value={v} key={v}>{l}</option>)}</select></label> }
export function CenteredLoader({ label }: { label: string }) { return <div className="center-loader"><RefreshCw className="spin" size={22} /><span>{label}</span></div> }
