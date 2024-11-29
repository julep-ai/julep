import "../common";

using Common;

namespace Tools;

/** Setup parameters for Email integration */
model EmailSetup {
    /** The host of the email server */
    host: string;

    /** The port of the email server */
    port: int32;

    /** The username of the email server */
    user: string;

    /** The password of the email server */
    password: string;
}

/** Arguments for Email sending */
model EmailArguments {
    /** The email address to send the email to */
    to: string;

    /** The email address to send the email from */
    from: string;

    /** The subject of the email */
    subject: string;

    /** The body of the email */
    body: string;
}

/** Email integration definition */
model EmailIntegrationDef extends BaseIntegrationDef {
    /** The provider must be "email" */
    provider: "email" = "email";
    
    /** The specific method of the integration to call */
    method?: string;
    
    /** The setup parameters for Email */
    setup?: EmailSetup;
    
    /** The arguments for Email sending */
    arguments?: EmailArguments;
}

/** Email Provider Card */
model EmailProviderCard extends BaseProviderCard {
    provider: "email" = "email";
    setup: EmailSetup;
    methods: ProviderMethod<EmailArguments, EmailOutput>[] = #[
        #{
            method: "send",
            description: "Send an email",
        }
    ];
    info: ProviderInfo = #{
        url: "https://emailservice.com/",
        docs: "https://emailservice.com/docs/",
        icon: "https://emailservice.com/favicon.ico",
        friendly_name: "Email Service",
    };
}

/** Email Output */
model EmailOutput {
    /** Whether the email was sent successfully */
    success: boolean;
} 