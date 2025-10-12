# Auto-Logout Issue Fix

## Problem
When auto-refresh is enabled, the dashboard automatically logs users out after approximately 25 minutes, even though the JWT token has a 30-minute lifespan.

## Root Cause

### Timeline of Events:
1. **T=0**: User logs in, receives JWT token valid for 30 minutes
2. **T=25 min**: Token has 5 minutes remaining before expiration
3. **Auto-refresh triggers** (runs every 60 seconds)
4. **Token check detects "expiring soon"** (< 5 minutes remaining)
5. **System immediately logs out** instead of refreshing the token
6. **User is redirected to login page**

### Code Issue:
The `api.js` request interceptor was using `isTokenExpired()` which checked if the token expires within 5 minutes, treating "expiring soon" the same as "already expired":

```javascript
// OLD CODE - PROBLEMATIC
if (token && this.isTokenExpired(token)) {
  // Immediately logs out when token has < 5 minutes left
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  window.location.href = '/login'
}
```

## Solution

### Changes Made:

1. **Split token expiration checks into two functions:**
   - `isTokenExpired()`: Checks if token has ACTUALLY expired (current time >= expiration)
   - `isTokenExpiringSoon()`: Checks if token expires within 5 minutes

2. **Implement automatic token refresh:**
   - When a token is expiring soon (< 5 minutes), automatically attempt to refresh it
   - Only log out if the token has ACTUALLY expired
   - Continue using current token if refresh fails (let backend decide validity)

3. **Updated request interceptor flow:**
   ```javascript
   // Check if token has ACTUALLY expired
   if (token && this.isTokenExpired(token)) {
     // Only now do we logout
     logout and redirect
   }
   
   // Check if token is expiring SOON
   if (token && this.isTokenExpiringSoon(token)) {
     // Try to refresh automatically
     try {
       await authStore.refreshToken()
       // Use new token for request
     } catch {
       // Continue with current token
     }
   }
   ```

## Benefits

1. **Seamless user experience**: Users stay logged in without interruption
2. **Automatic token renewal**: Tokens are refreshed before expiration
3. **No data loss**: Auto-refresh continues working without logout
4. **Graceful degradation**: If refresh fails, system continues with current token
5. **Security maintained**: Tokens still expire after 30 minutes if not refreshed

## Testing

To verify the fix:
1. Enable auto-refresh on the dashboard
2. Wait for 25+ minutes
3. Verify that:
   - User remains logged in
   - Token is automatically refreshed
   - Dashboard data continues to update
   - No unexpected logouts occur

## Configuration

- **Token Lifetime**: 30 minutes (configured in backend)
- **Refresh Trigger**: 5 minutes before expiration
- **Auto-refresh Interval**: 60 seconds
- **Expected Behavior**: Token should auto-refresh around the 25-minute mark

## Files Modified

1. `frontend/src/services/api.js`:
   - Split `isTokenExpired()` into two functions
   - Updated request interceptor to auto-refresh
   - Fixed `isCurrentTokenExpiring()` to use new function

2. `frontend/src/views/Dashboard.vue`:
   - No changes needed (already had token refresh logic)

## Notes

- The backend `/api/auth/refresh-token` endpoint was already implemented
- The auth store `refreshToken()` method was already available
- This fix leverages existing infrastructure to solve the auto-logout issue
