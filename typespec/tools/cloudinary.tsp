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

alias CloudinaryMethod =
    | /** Upload media to Cloudinary */
      "media_upload"
    | /** Edit media in Cloudinary */
      "media_edit";

/** Arguments for Cloudinary media upload */
model CloudinaryUploadArguments {
    /** The URL of the file upload */
    file: string;

    /** Return base64 encoded file */
    return_base64: boolean = false;

    /** Optional public ID for the uploaded file */
    public_id?: string;

    /** Optional upload parameters */
    upload_params?: Record<unknown>;
}

/** Arguments for Cloudinary media edit */
model CloudinaryEditArguments {
    /** The file Public ID in Cloudinary */
    public_id: string;

    /** The transformation to apply to the file */
    transformation: Array<Record<unknown>>;

    /** Return base64 encoded file */
    return_base64: boolean = false;
}

/** Base Cloudinary integration definition */
model BaseCloudinaryIntegrationDef extends BaseIntegrationDef {
    provider: "cloudinary" = "cloudinary";
    setup?: CloudinarySetup;
    method?: CloudinaryMethod;
}

/** Cloudinary upload integration definition */
model CloudinaryUploadIntegrationDef extends BaseCloudinaryIntegrationDef {
    method: "media_upload" = "media_upload";
    arguments?: CloudinaryUploadArguments;
}

/** Cloudinary edit integration definition */
model CloudinaryEditIntegrationDef extends BaseCloudinaryIntegrationDef {
    method: "media_edit" = "media_edit";
    arguments?: CloudinaryEditArguments;
}

alias CloudinaryIntegrationDef = CloudinaryUploadIntegrationDef | CloudinaryEditIntegrationDef;

/** Output for Cloudinary upload */
model CloudinaryUploadOutput {
    /** The URL of the uploaded file */
    url: string;
    
    /** The public ID of the uploaded file */
    public_id: string;

    /** The base64 encoded file */
    base64?: string;

    /** The metadata of the uploaded file */
    metadata: Record<unknown>;
}

/** Output for Cloudinary edit */
model CloudinaryEditOutput {
    /** The transformed URL from Cloudinary */
    transformed_url: string;

    /** The base64 encoded file */
    base64?: string;
}

alias CloudinaryOutput = CloudinaryUploadOutput | CloudinaryEditOutput;

/** Cloudinary Provider Card */
model CloudinaryProviderCard extends BaseProviderCard {
    provider: "cloudinary" = "cloudinary";
    setup: CloudinarySetup;
    methods: ProviderMethod<CloudinaryUploadArguments | CloudinaryEditArguments, CloudinaryOutput>[] = #[
        #{
            method: "media_upload",
            description: "Upload media to Cloudinary",
        },
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