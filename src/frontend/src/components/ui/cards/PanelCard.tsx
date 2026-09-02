import type { ReactNode } from "react";

type PanelCardProps = {
    children: ReactNode;
    className?: string;
    subtitle?: string;
    top?: ReactNode;
    title?: string;
};

export function PanelCard({ children, className, subtitle, top, title }: PanelCardProps) {
    const nextClassName = className ? `panel ${className}` : "panel";

    return (
        <section className={nextClassName}>
            {top ? <div className="panel-card__top">{top}</div> : null}
            {title ? <h1>{title}</h1> : null}
            {subtitle ? <p className="muted">{subtitle}</p> : null}
            {children}
        </section>
    );
}
