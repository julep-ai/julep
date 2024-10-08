import "../common";
import "../sessions";
import "../tools";

using Common;
using Sessions;
using Tools;

namespace Entries;

//
// ENTRY MODELS
//

/** Image detail level */
enum ImageDetail {
    low,
    high,
    auto,
}

/** ChatML role (system|assistant|user|function_call|function|function_response|auto) */
enum ChatMLRole {
    user,
    assistant,
    system,
    function,
    function_response,
    function_call,
    auto,
}

model ImageURL<T extends string = string> {
    /** Image URL or base64 data url (e.g. `data:image/jpeg;base64,<the base64 encoded image>`) */
    url: T;

    /** The detail level of the image */
    detail: ImageDetail = ImageDetail.auto;
}

model ChatMLTextContentPart<T extends string = string> {
    text: T;

    /** The type (fixed to 'text') */
    type: "text" = "text";
}

model ChatMLImageContentPart<T extends string = string> {
    /** The image URL */
    image_url: ImageURL;

    /** The type (fixed to 'image_url') */
    type: "image_url" = "image_url";
}

alias ChatMLContentPart<T extends string = string> = ChatMLTextContentPart<T> | ChatMLImageContentPart<T>;

model ChatMLMessage<T extends string = string> {
    /** The role of the message */
    role: ChatMLRole;

    /** The content parts of the message */
    content: T | T[] | ChatMLContentPart<T>[];

    /** Name */
    name?: string;

    /** Whether to continue this message or return a new one */
    @visibility("create")
    continue?: boolean;

    /** Tool calls generated by the model. */
    @visibility("read")
    tool_calls?: ChosenToolCall[] | null = #[];

    ...HasCreatedAtOptional;
    ...HasIdOptional;
}

@withVisibility("create")
model InputChatMLMessage<T extends string = string> {
    ...ChatMLMessage<T>;
}

alias EntryContent = ChatMLContentPart<string>[] | Tool | ChosenToolCall | string | ToolResponse;

model BaseEntry {
    role: ChatMLRole;
    name: string | null = null;
    content: EntryContent | EntryContent[];
    source: entrySource;

    tokenizer: string;
    token_count: uint16;

    /** This is the time that this event refers to. */
    @minValue(0)
    timestamp: float;
}

model Entry extends BaseEntry {
    /** This is the time it was added to the database */
    ...HasCreatedAt;
    ...HasId;
}

model Relation {
    head: uuid;
    relation: string;
    tail: uuid;
}

model History {
    entries: Entry[];
    relations: Relation[];
    session_id: Session.id;

    ...HasCreatedAt;
}
