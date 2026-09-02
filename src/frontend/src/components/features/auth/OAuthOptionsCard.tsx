import type { ReactNode } from "react";

type OAuthOptionsCardProps = {
    title?: string;
    children: ReactNode;
};

export function OAuthOptionsCard({ title, children }: OAuthOptionsCardProps) {
    return (
        <section className="oauth-options-card">
            {title ? <p className="oauth-options-card__title">{title}</p> : null}
            <div className="oauth-options-card__body">{children}</div>
        </section>
    );
}
