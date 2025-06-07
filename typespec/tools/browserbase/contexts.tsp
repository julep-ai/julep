import "../../common";

using Common;

namespace Tools;

/** browserbase context provider */
// AIDEV-NOTE: fleshed out browserbase context models
model BrowserbaseContextIntegrationDef extends BaseBrowserbaseIntegrationDef {
    /** The specific method of the integration to call */
    method?: "create_context" = "create_context";

    /** The arguments for the method */
    arguments?: BrowserbaseContextArguments;
}

model BrowserbaseContextArguments {
    /** The Project ID. Can be found in Settings. */
    projectId: string;
}

model BrowserbaseContextOutput {
    id: string;
    uploadUrl?: url;
    publicKey?: string;
    cipherAlgorithm?: string;
    initializationVectorSize?: uint16;
}

