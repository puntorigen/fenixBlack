import { z } from 'zod';

export const privacyPolicy = z.object({
    gdpr: z.boolean().describe('Whether the privacy policy is compliant with GDPR or not'),
    not_gdpr_reason: z.string().default('').describe(`If it's not complaint with GDPR, explain why in easy to understand terms`),
}); 

export const brandSchema = z.object({
    logo: z.object({
      high_res: z.string().describe('The URL for the high-resolution format of the company logo.'),
      vector_format: z.string().describe('The URL for the vector format of the company logo.')
    }).describe('High-resolution and vector formats of the company\'s logo. Essential for ensuring brand consistency across all platforms.'),
    color_palette: z.object({
      primary_colors: z.array(z.string()).describe('Primary colors used in the brand\'s visual identity with specific color codes (e.g., HEX, RGB, CMYK).'),
      secondary_colors: z.array(z.string()).describe('Secondary colors used in the brand\'s visual identity.'),
      tertiary_colors: z.array(z.string()).optional().describe('Tertiary colors used optionally in the brand\'s visual identity.')
    }).describe('The official colors used in the brand\'s visual identity.'),
    typography: z.object({
      primary_typeface: z.object({
        url: z.string().describe('The URL of the primary typeface file.'),
        style: z.string().describe('Style and weight of the primary typeface.'),
        usage: z.string().describe('Suggested usage of the primary typeface.')
      }).describe('Primary typeface used in brand communications.'),
      secondary_typeface: z.object({
        url: z.string().describe('The URL of the secondary typeface file.'),
        style: z.string().describe('Style and weight of the secondary typeface.'),
        usage: z.string().describe('Suggested usage of the secondary typeface.')
      }).describe('Secondary typeface used in brand communications.')
    }).describe('Specifications of the primary and secondary typefaces used in the brand\'s communications.'),
    logo_usage: z.string().describe('Rules for how the logo can be used, including sizing, spacing, what backgrounds it can appear on, and unacceptable modifications.'),
    layout_principles: z.string().describe('Guidelines on the layout for marketing materials, including margins, grid use, layering of images and text, and alignment principles.'),
    design_do_and_donts: z.string().describe('Specific guidelines highlighting recommended and discouraged design practices to maintain brand integrity.'),
    email_signature_designs: z.object({
      signature_template_one: z.string().describe('The URL for the first email signature template that reflects the brand identity.'),
      signature_template_two: z.string().optional().describe('The URL for the second email signature template that reflects the brand identity.')
    }).describe('URLs for the templates of email signatures that reflect the brand identity.'),
    social_media_guidelines: z.object({
      profile_layouts: z.string().describe('The URL for the design guidelines of social media profiles.'),
      hashtag_usage: z.string().describe('Recommended practices for using hashtags.'),
      tone_of_voice: z.string().describe('Tone of voice to be maintained on social media.')
    }).describe('Specific rules for branding on social media platforms.'),
    advertising_guidelines: z.string().describe('Guidelines for creating advertisements, including the use of logos, typefaces, and color schemes, as well as the tone of the advertising content.'),
    presentation_guidelines: z.string().describe('The URL for the guidelines of designing presentations, including slide layouts, the use of logos, color schemes, and typography.'),
    document_guidelines: z.string().describe('The URL for the guidelines of formatting official documents, including reports, whitepapers, and proposals, focusing on layout, typography, and use of logos.'),
    landing_page_design_guidelines: z.string().describe('The URL for the guidelines of designing landing pages that maintain brand consistency, focusing on typography, color schemes, and imagery style.')
  });

export const brochureSchema = z.object({
    title: z.string().describe('Brochure title'),
    base64: z.string().describe('PDF base64')
});