# Common Issues & Troubleshooting

## Login Issues

### "Invalid credentials" error
1. Verify your email address is correct
2. Try resetting your password via the "Forgot Password" link
3. Check if your account has been deactivated (contact admin)
4. Clear browser cache and cookies
5. If using SSO, check with your IT admin that your SSO account is active

### Account locked
- Accounts are locked after 5 failed login attempts
- Lock expires automatically after 30 minutes
- Contact support for immediate unlock

## Performance Issues

### Slow page loads
1. Check your internet connection speed
2. Clear browser cache
3. Try a different browser (Chrome/Firefox recommended)
4. Disable browser extensions that may interfere
5. If issues persist across multiple users, contact support with specifics

### API timeout errors
- Ensure you're not exceeding rate limits
- Check API status page for any known issues
- For large data requests, use pagination
- Consider implementing exponential backoff for retries

## Email Issues

### Not receiving notification emails
1. Check spam/junk folder
2. Verify notification preferences in Settings → Notifications
3. Check that your email provider isn't blocking our domain
4. Whitelist notifications@sentinelcx.com

### Email formatting issues
- Ensure your email client supports HTML emails
- If using Outlook, check rendering in the web version
