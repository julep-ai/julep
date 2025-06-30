const regex = /^(application|audio|font|example|image|message|model|multipart|text|video|x-(?:[0-9A-Za-z!#$%&'*+.^_`|~-]+))\/([0-9A-Za-z!#$%&'*+.^_`|~-]+)$/;
export function parseMimeType(mimeType) {
    const match = mimeType.match(regex);
    if (match == null) {
        return undefined;
    }
    const type = {
        type: match[1],
        ...parseSubType(match[2]),
    };
    return type;
}
function parseSubType(value) {
    if (!value.includes("+"))
        return { subtype: value };
    const [subtype, suffix] = value.split("+", 2);
    return { subtype, suffix };
}
//# sourceMappingURL=mime-type.js.map