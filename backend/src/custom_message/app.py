import json

def lambda_handler(event, context):
    trigger_source = event.get('triggerSource')
    
    # CustomMessage_SignUp or CustomMessage_ResendCode
    if trigger_source in ['CustomMessage_SignUp', 'CustomMessage_ResendCode']:
        code = event['request']['codeParameter']
        name = event['request']['userAttributes'].get('name', 'Fan')
        
        event['response']['emailSubject'] = "Your Verification Code - Global Event Platform"
        event['response']['emailMessage'] = f"""
        <html>
        <body style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #0d0d14; color: #ffffff; padding: 40px; text-align: center;">
            <div style="max-w-md mx-auto background-color: #1a1a24; border: 1px solid #333; border-radius: 12px; padding: 30px; margin: 0 auto; max-width: 500px;">
                <h2 style="color: #3b82f6; margin-bottom: 20px;">Global Event Platform</h2>
                <h3 style="color: #ffffff; font-weight: 500;">Verify your email address</h3>
                <p style="color: #a0a0b0; font-size: 15px; line-height: 1.5; margin-bottom: 30px;">
                    Hi {name},<br><br>
                    Welcome to the Global Event Platform! To complete your registration, please use the verification code below.
                </p>
                <div style="background-color: #0d0d14; border: 1px solid #2d2d3a; border-radius: 8px; padding: 20px; margin-bottom: 30px;">
                    <span style="font-size: 32px; font-weight: bold; letter-spacing: 6px; color: #ffffff;">{code}</span>
                </div>
                <p style="color: #666; font-size: 12px;">
                    If you didn't request this email, you can safely ignore it.
                </p>
            </div>
        </body>
        </html>
        """
        
    elif trigger_source == 'CustomMessage_ForgotPassword':
        code = event['request']['codeParameter']
        name = event['request']['userAttributes'].get('name', 'Fan')
        
        event['response']['emailSubject'] = "Reset Your Password - Global Event Platform"
        event['response']['emailMessage'] = f"""
        <html>
        <body style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #0d0d14; color: #ffffff; padding: 40px; text-align: center;">
            <div style="max-w-md mx-auto background-color: #1a1a24; border: 1px solid #333; border-radius: 12px; padding: 30px; margin: 0 auto; max-width: 500px;">
                <h2 style="color: #3b82f6; margin-bottom: 20px;">Global Event Platform</h2>
                <h3 style="color: #ffffff; font-weight: 500;">Password Reset Request</h3>
                <p style="color: #a0a0b0; font-size: 15px; line-height: 1.5; margin-bottom: 30px;">
                    Hi {name},<br><br>
                    We received a request to reset your password. Use the code below to proceed:
                </p>
                <div style="background-color: #0d0d14; border: 1px solid #2d2d3a; border-radius: 8px; padding: 20px; margin-bottom: 30px;">
                    <span style="font-size: 32px; font-weight: bold; letter-spacing: 6px; color: #ffffff;">{code}</span>
                </div>
                <p style="color: #666; font-size: 12px;">
                    If you didn't request a password reset, you can safely ignore this email.
                </p>
            </div>
        </body>
        </html>
        """
        
    return event
