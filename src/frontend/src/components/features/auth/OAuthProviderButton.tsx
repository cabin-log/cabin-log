import { Button } from "../../ui";
import { getApiBase } from "../../../utils/apiBase";

type OAuthProviderButtonProps = {
    provider: "google" | "github";
    label: string;
    startPath: string;
    disabled?: boolean;
    hideLabel?: boolean;
};

const PROVIDER_LOGOS: Record<
    OAuthProviderButtonProps["provider"],
    { light: string; dark: string }
> = {
    google: {
        light: "/icons/google-mark-light.svg",
        dark: "/icons/google-mark-dark.svg",
    },
    github: {
        light: "/icons/github-mark-light.svg",
        dark: "/icons/github-mark-dark.svg",
    },
};

export function OAuthProviderButton({
    provider,
    label,
    startPath,
    disabled = false,
    hideLabel = false,
}: OAuthProviderButtonProps) {
    const onClick = () => {
        const oauthStartUrl = new URL(startPath, `${getApiBase()}/`).toString();
        window.location.assign(oauthStartUrl);
    };
    const logos = PROVIDER_LOGOS[provider];

    return (
        <Button type="button" disabled={disabled} onClick={onClick} aria-label={label}>
            <span className="oauth-provider-button__content">
                <span className="oauth-provider-button__logo-wrap" aria-hidden="true">
                    <img
                        src={logos.dark}
                        alt=""
                        className={`oauth-provider-button__logo oauth-provider-button__logo--dark oauth-provider-button__logo--${provider}`}
                    />
                    <img
                        src={logos.light}
                        alt=""
                        className={`oauth-provider-button__logo oauth-provider-button__logo--light oauth-provider-button__logo--${provider}`}
                    />
                </span>
                {hideLabel ? null : <span className="oauth-provider-button__label">{label}</span>}
            </span>
        </Button>
    );
}
