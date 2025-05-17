import "../common";
import "./integrations.tsp";

using Common;

namespace Tools;

/** Setup parameters for Mailgun integration */
model MailgunSetup {
    /** The API key for the Mailgun integration */
    api_key: string;
}

alias MailgunMethod = "send_email";

/** Arguments for mailgun.send_email method */
model MailgunSendEmailArguments {
    /** The email address to send the email to */
    to: string;

    /** The email address to send the email from */
    from: string;

    /** The subject of the email */
    subject: string;

    /** The body of the email */
    body: string;

    /** Optional carbon copy recipients (comma-separated email addresses) */
    cc?: string;

    /** Optional blind carbon copy recipients (comma-separated email addresses) */
    bcc?: string;
}

alias MailgunArguments = MailgunSendEmailArguments;

/** Mailgun integration definition */
model MailgunIntegrationDef extends BaseIntegrationDef {
    /** The provider must be "mailgun" */
    provider: "mailgun" = "mailgun";
    
    /** The specific method of the integration to call */
    method?: MailgunMethod;
    
    /** The setup parameters for Mailgun */
    setup?: MailgunSetup;
    
    /** The arguments for mailgun methods */
    arguments?: MailgunArguments;
}

/** Mailgun Provider Card */
model MailgunProviderCard extends BaseProviderCard {
    provider: "mailgun" = "mailgun";
    setup: MailgunSetup;
    methods: ProviderMethod<MailgunSendEmailArguments, MailgunSendEmailOutput>[] = #[
        #{
            method: "send_email",
            description: "Send an email using Mailgun",
        }
    ];
    info: ProviderInfo = #{
        url: "https://www.mailgun.com/",
        docs: "https://documentation.mailgun.com/",
        icon: "https://mailgun.com/favicon.ico",
        friendly_name: "Mailgun",
    };
}

/** mailgun.send_email method Output */
model MailgunSendEmailOutput {
    /** Whether the email was sent successfully */
    success: boolean;

    /** The error message if the email was not sent successfully */
    error?: string;
}
