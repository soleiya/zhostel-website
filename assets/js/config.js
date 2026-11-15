/* Supabase project for zhostel.com.
   The anon key is public by design: Row Level Security and the database
   functions decide what it can do. */
window.SUPABASE_CONFIG = {
  url: "https://vsfuliexdlhgdlvlhqzy.supabase.co",
  anonKey: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZzZnVsaWV4ZGxoZ2RsdmxocXp5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTQ2ODI3NTIsImV4cCI6MjExMDI1ODc1Mn0.3u7UKnwarysFtOfFGXqN3lDvHiul0yVNNnwGP7m3xpw",
  fallbackEmail: "reservations@zhostel.com",
  // true once the send-contact-email Edge Function is deployed; until then contact forms open the email app.
  contactFunction: false,
};
