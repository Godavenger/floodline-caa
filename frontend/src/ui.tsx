import type { ReactNode } from 'react';
import { AlertCircle, ArrowUpRight, Check, Info } from 'lucide-react';
import { riskWord, time } from './api';
import type { Report, RiskLevel } from './types';

export function RiskTag({ level }: { level: RiskLevel }) { return <span className={`status risk-${level}`}><span className="status-dot" />{riskWord(level)}</span>; }
export function ReportTag({ status }: { status: Report['status'] }) { return <span className={`status report-${status}`}>{status === 'verified' ? <Check size={12} /> : null}{status.charAt(0).toUpperCase() + status.slice(1)}</span>; }
export function ErrorMessage({ children, retry }: { children: ReactNode; retry?: () => void }) { return <div className="inline-error" role="alert"><AlertCircle size={16} /><p>{children}</p>{retry && <button className="text-button" onClick={retry}>Retry</button>}</div>; }
export function Note({ children }: { children: ReactNode }) { return <p className="note"><Info size={14} /><span>{children}</span></p>; }
export function LoadingRows({ count = 3 }: { count?: number }) { return <div className="loading-rows" aria-label="Loading" role="status">{Array.from({ length: count }, (_, index) => <div className="loading-row" key={index}><span /><span /></div>)}</div>; }
export function EmptyState({ children, action }: { children: ReactNode; action?: ReactNode }) { return <div className="empty-state"><p>{children}</p>{action}</div>; }
export function TextLink({ children, onClick }: { children: ReactNode; onClick: () => void }) { return <button className="text-button link-action" onClick={onClick}>{children}<ArrowUpRight size={14} /></button>; }
export function Freshness({ at }: { at: string | null }) { return <span className="freshness">Observed {time(at)}</span>; }
