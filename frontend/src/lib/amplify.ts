import { Amplify } from 'aws-amplify'

export function configureAmplify() {
  const userPoolId = import.meta.env.VITE_COGNITO_USER_POOL_ID
  const userPoolClientId = import.meta.env.VITE_COGNITO_CLIENT_ID
  const oauthDomain = import.meta.env.VITE_COGNITO_OAUTH_DOMAIN
  const redirectSignIn = import.meta.env.VITE_COGNITO_REDIRECT_SIGN_IN ?? window.location.origin
  const redirectSignOut = import.meta.env.VITE_COGNITO_REDIRECT_SIGN_OUT ?? window.location.origin

  if (userPoolId && userPoolClientId) {
    Amplify.configure({
      Auth: {
        Cognito: {
          userPoolId,
          userPoolClientId,
          loginWith: {
            email: true,
            username: true,
            ...(oauthDomain
              ? {
                  oauth: {
                    domain: oauthDomain,
                    scopes: ['email', 'openid', 'profile'],
                    redirectSignIn: [redirectSignIn],
                    redirectSignOut: [redirectSignOut],
                    responseType: 'code',
                  },
                }
              : {}),
          }
        }
      }
    })
  } else {
    console.warn('Amplify is not configured because Cognito env vars are missing.')
  }
}
