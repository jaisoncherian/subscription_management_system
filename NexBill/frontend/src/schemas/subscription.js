import { z } from 'zod'

export const subscriptionSchema = z
  .object({
    customer_id: z.coerce.number().int().positive('Choose a customer'),
    template_id: z.coerce.number().int().positive('Choose a template'),
    start_date: z.string().optional(),
    expires_on: z.string().optional(),
    discount_id: z.string().optional(),
    notes: z.string().max(500, 'Keep notes under 500 characters').optional(),
  })
  .refine((d) => !d.start_date || !d.expires_on || d.expires_on >= d.start_date, {
    message: 'Expiry must be on or after the start date',
    path: ['expires_on'],
  })