import { useTranslation } from "react-i18next";
import type { GameState } from "../../../hooks/api/game/useGameApi";

type RewardProgressProps = {
    entry?: NonNullable<GameState["collection"]["furniture"]>[number];
};

export function RewardProgress({ entry }: RewardProgressProps) {
    const { t, i18n } = useTranslation();
    const progress = entry?.progress;
    if (!progress || progress.status === "no_next_level") return null;
    if (progress.status === "maximum") {
        return (
            <p className="cabin-reward-progress__status">
                {t(`cabin.progress.${progress.status}`)}
            </p>
        );
    }
    const format = (value: number) =>
        new Intl.NumberFormat(i18n.resolvedLanguage, { maximumFractionDigits: 3 }).format(value);
    return (
        <section className="cabin-reward-progress" aria-label={t("cabin.progress.title")}>
            <header className="cabin-reward-progress__header">
                <strong>
                    {entry?.owned
                        ? t("cabin.progress.next", { level: progress.next_level })
                        : t("cabin.progress.unlock")}
                </strong>
            </header>
            {progress.metrics?.map((metric) => {
                const scale =
                    metric.unit === "bytes" ? (metric.target >= 1_000_000 ? 1_000_000 : 1000) : 1;
                const unit =
                    metric.unit === "bytes"
                        ? scale === 1_000_000
                            ? "MB"
                            : "KB"
                        : t(`cabin.progress.units.${metric.unit}`);
                return (
                    <div className="cabin-reward-progress__metric" key={metric.key}>
                        <label>
                            <span className="cabin-reward-progress__line">
                                <span>{t(`cabin.progress.metrics.${metric.key}`)}</span>
                                <span
                                    title={`${format(metric.current)} / ${format(metric.target)} ${t(`cabin.progress.units.${metric.unit}`)}`}
                                >
                                    {metric.remaining === 0 ? "✓ " : ""}
                                    {t("cabin.progress.values", {
                                        current: format(
                                            Math.min(metric.current, metric.target) / scale,
                                        ),
                                        target: format(metric.target / scale),
                                        unit,
                                    })}
                                </span>
                            </span>
                            <progress
                                max={metric.target}
                                value={Math.min(metric.current, metric.target)}
                            />
                        </label>
                    </div>
                );
            })}
        </section>
    );
}
