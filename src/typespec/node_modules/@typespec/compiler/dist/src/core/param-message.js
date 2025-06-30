export function paramMessage(strings, ...keys) {
    const template = (dict) => {
        const result = [strings[0]];
        keys.forEach((key, i) => {
            const value = dict[key];
            if (value !== undefined) {
                result.push(value);
            }
            result.push(strings[i + 1]);
        });
        return result.join("");
    };
    template.keys = keys;
    return template;
}
//# sourceMappingURL=param-message.js.map