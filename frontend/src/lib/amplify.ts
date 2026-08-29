import { Amplify } from 'aws-amplify'

export function configureAmplify() {
  const userPoolId = import.meta.env.VITE_COGNITO_USER_POOL_ID
  const userPoolClientId = import.meta.env.VITE_COGNITO_CLIENT_ID

  if (userPoolId && userPoolClientId) {
    Amplify.configure({
      Auth: {
        Cognito: {
          userPoolId,
          userPoolClientId,
          loginWith: {
            email: true,
            username: true,
          }
        }
      }
    })
  } else {
    console.warn('Amplify is not configured because Cognito env vars are missing.')
  }
}
