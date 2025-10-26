/**
 * Configuration Example for Alert Call Nurse Edge Function
 * 
 * Copy this to Supabase Dashboard > Edge Functions > Secrets
 * or set via Supabase CLI
 */

export const CONFIG_EXAMPLE = {
  // Supabase Configuration
  SUPABASE_URL: 'https://your-project.supabase.co',
  SUPABASE_SERVICE_ROLE_KEY: 'your-service-role-key',

  // LiveKit SIP Configuration
  // Get these from: https://cloud.livekit.io/projects/YOUR_PROJECT/settings
  LIVEKIT_API_URL: 'https://haven-livekit.livekit.cloud',
  LIVEKIT_API_KEY: 'APIxxxxxxxxxxx',
  LIVEKIT_API_SECRET: 'your-api-secret',
  LIVEKIT_SIP_TRUNK_ID: 'ST_xxxxxxxxxxxxx',

  // Nurse Contact
  NURSE_PHONE_NUMBER: '14085948710',

  // Edge Function URL (for database trigger)
  // Format: https://PROJECT_REF.supabase.co/functions/v1/alert-call-nurse
  EDGE_FUNCTION_URL: 'http://localhost:54321/functions/v1/alert-call-nurse'
}

/**
 * To set these via Supabase CLI:
 * 
 * supabase secrets set LIVEKIT_API_KEY=APIxxxxxxxxxxx
 * supabase secrets set LIVEKIT_API_SECRET=your-secret
 * supabase secrets set LIVEKIT_SIP_TRUNK_ID=ST_xxxxx
 * supabase secrets set NURSE_PHONE_NUMBER=14085948710
 */
