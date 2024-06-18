import { omit } from 'lodash';
import zodToJsonSchemaImpl from 'zod-to-json-schema';
import FingerprintJS from '@fingerprintjs/fingerprintjs';
import CryptoJS from 'crypto-js';

export async function getBrowserFingerprint() {
    const fp = await FingerprintJS.load();
    const result = await fp.get();
    const userId = result.visitorId;
    return userId;
}

export function encryptData(data, key) {
    return CryptoJS.AES.encrypt(JSON.stringify(data), key).toString();
}

export function zodToJson(schema) {
    return omit(
      zodToJsonSchemaImpl(schema, { $refStrategy: 'none' }),
      '$ref',
      '$schema',
      'default',
      'definitions',
      'description',
      'markdownDescription',
    );
}

export function splitSentences(description) {
    const sentences = [];
    let currentSentence = "";
    let inURL = false;

    for (let i = 0; i < description.length; i++) {
        const char = description[i];
        currentSentence += char;

        // Check if entering a URL
        if (!inURL && description.length>(i+7) && description.substring(i, i + 7).match(/https?:\/\//)) {
            inURL = true;
        }

        // Check if exiting a URL
        if (inURL && char === ' ') {
            inURL = false;
        }

        // Check for end of sentence punctuation if not inside a URL
        if (!inURL && (char === '.' || char === '?' || char === '!')) {
            if (i + 1 < description.length && description[i + 1] === ' ') {
                sentences.push(currentSentence.trim());
                currentSentence = "";
            }
        }
    }

    // Add the last sentence if there is any leftover text
    if (currentSentence.trim().length > 0) {
        sentences.push(currentSentence.trim());
    }

    return sentences;
}