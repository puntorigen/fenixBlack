import { omit } from 'lodash';
import zodToJsonSchemaImpl from 'zod-to-json-schema';
import FingerprintJS from '@fingerprintjs/fingerprintjs';
import CryptoJS from 'crypto-js';

export async function getBrowserFingerprint() {
    const fp = await FingerprintJS.load();
    const { visitorId } = await fp.get();
    return visitorId;
}

export function encryptData(data, key) {
    const iv = CryptoJS.lib.WordArray.random(128 / 8); // Generate a random 16-byte IV.
    const dataString = JSON.stringify(data);

    const keyWordArray = CryptoJS.enc.Base64.parse(key); // Parse the key from Base64 if stored/transmitted in Base64
    const encrypted = CryptoJS.AES.encrypt(dataString, keyWordArray, {
        iv: iv,
        mode: CryptoJS.mode.CBC,
        padding: CryptoJS.pad.Pkcs7
    }); 

    // Combine the IV and the encrypted data, then encode to Base64
    const combined = iv.concat(encrypted.ciphertext);
    const encryptedData = CryptoJS.enc.Base64.stringify(combined);
    return encryptedData;
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