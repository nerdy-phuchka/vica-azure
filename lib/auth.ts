import {PublicClientApplication,AuthenticationResult,InteractionRequiredAuthError} from '@azure/msal-browser';
let client:PublicClientApplication|undefined;
let boot:Promise<void>|undefined;

export async function entraToken(interactive=false):Promise<string> {
  if(!client) {
    client=new PublicClientApplication({auth:{clientId:process.env.NEXT_PUBLIC_ENTRA_CLIENT_ID||'',
      authority:`https://login.microsoftonline.com/${process.env.NEXT_PUBLIC_ENTRA_TENANT_ID}`,
      redirectUri:window.location.origin},cache:{cacheLocation:'sessionStorage'}});
    boot=(async()=>{await client!.initialize();await client!.handleRedirectPromise();})();
  }
  await boot;
  const scopes=[process.env.NEXT_PUBLIC_API_SCOPE||''];
  const accounts=client.getAllAccounts();
  if(!accounts.length) {if(interactive)await client.loginRedirect({scopes});throw new Error('Sign in with your organisation account');}
  try {return (await client.acquireTokenSilent({scopes,account:accounts[0]})).accessToken;}
  catch(error) {
    if(interactive && error instanceof InteractionRequiredAuthError)await client.acquireTokenRedirect({scopes,account:accounts[0]});
    throw error;
  }
}
