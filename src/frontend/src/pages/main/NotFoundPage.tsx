import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { Button, PanelCard } from "../../components/ui";

export function NotFoundPage() {
    const navigate = useNavigate();
    const { t } = useTranslation();

    return (
        <section className="page-content">
            <PanelCard title={t("notFound.title")} subtitle={t("notFound.subtitle")}>
                <div className="not-found__actions">
                    <Button type="button" onClick={() => navigate("/cabin", { replace: true })}>
                        {t("notFound.backToCabin")}
                    </Button>
                </div>
            </PanelCard>
        </section>
    );
}
