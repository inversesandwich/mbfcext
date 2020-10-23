// import { logger } from "utils";
// const log = logger("mbfc:utils:getDomain");

export const getDomain = (url: string) => {
    let hn, p;
    try {
        if (!url.startsWith("http")) url = "https://" + url;
        hn = new URL(url).hostname;
        if (hn) hn = hn.match(/(www[0-9]?\.)?(.+)/i)[2];
        p = new URL(url).pathname;
    } catch (e) {
        // log(e);
        // invalid domain is normal
    }
    return { domain: hn, path: p };
};
