import type { ReactNode } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";

type ModalProps = {
    children?: ReactNode;
    className?: string;
    closeLabel?: string;
    description?: string;
    footer?: ReactNode;
    onClose: () => void;
    open: boolean;
    title: string;
};

export function Modal({
    children,
    className,
    closeLabel = "Close modal",
    description,
    footer,
    onClose,
    open,
    title,
}: ModalProps) {
    if (!open || typeof document === "undefined") {
        return null;
    }

    const modalClassName = className ? `ui-modal ${className}` : "ui-modal";

    return createPortal(
        <div className={modalClassName} role="dialog" aria-modal="true" aria-label={title}>
            <button
                type="button"
                className="ui-modal__backdrop"
                aria-label={closeLabel}
                onClick={onClose}
            />
            <section className="ui-modal__panel">
                <header className="ui-modal__header">
                    <div>
                        <h2>{title}</h2>
                        {description ? <p>{description}</p> : null}
                    </div>
                    <button
                        type="button"
                        className="ui-modal__close"
                        onClick={onClose}
                        aria-label={closeLabel}
                    >
                        <X aria-hidden="true" />
                    </button>
                </header>
                {children ? <div className="ui-modal__body">{children}</div> : null}
                {footer ? <footer className="ui-modal__footer">{footer}</footer> : null}
            </section>
        </div>,
        document.body,
    );
}
