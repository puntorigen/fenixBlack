import { z } from 'zod';

export const privacyPolicy = z.object({
    gdpr: z.boolean().describe('Whether the privacy policy is compliant with GDPR or not'),
    not_gdpr_reason: z.string().default('').describe(`If it's not complaint with GDPR, explain why in easy to understand terms`),
}); 

export const brandSchema = z.object({
    color_palette: z.object({
      primary_colors: z.array(z.string()).describe('HEX Primary colors used in the brand\'s visual identity with specific color codes.'),
      secondary_colors: z.array(z.string()).describe('HEX Secondary colors used in the brand\'s visual identity.'),
      tertiary_colors: z.array(z.string()).optional().describe('HEX Tertiary colors used optionally in the brand\'s visual identity.')
    }).describe('The official colors used in the brand\'s visual identity.'),
    typography: z.object({
      primary_typeface: z.string().describe('The primary font face to use'),
      secondary_typeface: z.string().describe('The secondary font face to use'),
    }).describe('Primary and secondary typefaces used in the brand\'s communications.'),
    logo_usage: z.string().describe('Rules for how the logo can be used, including sizing, spacing, what backgrounds it can appear on, and unacceptable modifications.'),
    layout_principles: z.string().describe('Guidelines on the layout for marketing materials'),
    social_media_guidelines: z.object({
      profile_layouts: z.string().describe('the design guidelines for social media profiles.'),
      hashtag_usage: z.string().describe('Recommended practices for using hashtags.'),
      tone_of_voice: z.string().describe('Tone of voice to be maintained on social media.')
    }).describe('Specific rules for branding on social media platforms.'),
    advertising_guidelines: z.string().describe('Guidelines for an LLM on creating advertisements, including the use of logos, typefaces, and color schemes, as well as the tone of the advertising content.'),
    presentation_guidelines: z.string().describe('Guidelines for an LLM on designing presentations, including slide layouts, the use of logos, color schemes, and typography.'),
    document_guidelines: z.string().describe('Guidelines for an LLM on formatting official documents, including reports, whitepapers, and proposals, focusing on layout, typography, and use of logos.'),
    landing_page_design_guidelines: z.string().describe('Guidelines for an LLM on designing landing pages that maintain brand consistency, focusing on typography, color schemes, and imagery style.')
  }); 

export const brochureSchema = z.object({
    title: z.string().describe('Brochure title'),
    base64: z.string().describe('PDF base64')
});