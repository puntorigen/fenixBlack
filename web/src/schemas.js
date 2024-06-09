import { z } from 'zod';

export const brandSchema = z.object({
    brand: z.object({
        name: z.string().describe('The name of the brand'),
        logo: z.string().describe('The URL of the logo image'),
        colors: z.object({
            primary: z.string().describe('The primary color for the brand'),
            secondary: z.string().describe('The secondary color for the brand'),
        }).describe('The main colors for the brand'),
        fonts: z.array(z.string()).describe('The fonts used by the brand')
    }),
    products: z.array(z.object({
         name: z.string().describe('The name of the product'),
         description: z.string().describe('The description of the product'),
         price: z.number().describe('The price of the product'),
         image: z.string().describe('The URL of the product image'),
     })).describe('The products offered by the brand')
});

export const brochureSchema = z.object({
    title: z.string().describe('Brochure title'),
    base64: z.string().describe('PDF base64')
});