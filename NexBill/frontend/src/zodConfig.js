import { z } from 'zod'

// Otherwise zod tries eval() to speed up parsing, which our Content-Security-Policy
// blocks. Its own module, imported first, because schemas read this when they are built.
z.config({ jitless: true })
