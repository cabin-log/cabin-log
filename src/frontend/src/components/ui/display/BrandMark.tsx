type BrandMarkProps = {
    className?: string;
};

export function BrandMark({ className }: BrandMarkProps) {
    const nextClassName = className ? `brand-mark ${className}` : "brand-mark";

    return <span className={nextClassName} aria-hidden="true" />;
}
