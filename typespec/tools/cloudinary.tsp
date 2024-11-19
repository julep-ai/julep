import "../common";

using Common;

namespace Tools;

/** Setup parameters for Cloudinary integration */
model CloudinarySetup {
    /** The API key for Cloudinary */
    cloudinary_api_key: string;

    /** The API secret for Cloudinary */
    cloudinary_api_secret: string;

    /** The Cloud name for Cloudinary */
    cloudinary_cloud_name: string;

    /** Additional parameters for the Cloudinary API */
    params?: Record<unknown>;
}

/** Arguments for Cloudinary integration */
model CloudinaryFetchArguments {
    /** The file Public ID in Cloudinary */
    file: string;

    /** The transformation to apply to the file */
    transformation: Array<Record<unknown>>;
}

/** Cloudinary integration definition */
model CloudinaryIntegrationDef extends BaseIntegrationDef {
    /** The provider must be "cloudinary" */
    provider: "cloudinary" = "cloudinary";
    
    /** The specific method of the integration to call */
    method?: string;
    
    /** The setup parameters for Cloudinary */
    setup?: CloudinarySetup;
    
    /** The arguments for Cloudinary */
    arguments?: CloudinaryFetchArguments;
}

/** Cloudinary Provider Card */
model CloudinaryProviderCard extends BaseProviderCard {
    provider: "cloudinary" = "cloudinary";
    setup: CloudinarySetup;
    methods: ProviderMethod<CloudinaryFetchArguments, CloudinaryFetchOutput>[] = #[
        #{
            method: "media_edit",
            description: "Edit media in Cloudinary",
        }
    ];
    info: ProviderInfo = #{
        url: "https://cloudinary.com/",
        docs: "https://cloudinary.com/documentation/python_quickstart",
        icon: "https://cloudinary.com/favicon.ico",
        friendly_name: "Cloudinary",
    };
}

/** Cloudinary Fetch Output */
model CloudinaryFetchOutput {
    /** The transformed URL from Cloudinary */
    transformed_url: string;
}