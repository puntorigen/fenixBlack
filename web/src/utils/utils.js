import { omit } from 'lodash';
import zodToJsonSchemaImpl from 'zod-to-json-schema';

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