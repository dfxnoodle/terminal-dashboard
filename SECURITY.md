# Security Policy

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please follow these steps:

1. **Do NOT** create a public issue
2. Email the maintainers directly with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Security Best Practices

### For Users

1. **Environment Variables**: Never commit `.env` files or expose API credentials
2. **Network Security**: Ensure your Odoo instance is properly secured
3. **Updates**: Keep dependencies up to date
4. **Access Control**: Limit access to sensitive endpoints

### For Developers

1. **Input Validation**: Always validate and sanitize user inputs
2. **Authentication**: Implement proper authentication mechanisms
3. **HTTPS**: Use HTTPS in production environments
4. **Dependencies**: Regularly audit and update dependencies
5. **Error Handling**: Don't expose sensitive information in error messages

## Common Security Considerations

### Odoo API Access
- Use dedicated API users with minimal required permissions
- Regularly rotate API keys
- Monitor API usage for suspicious activity

### Environment Configuration
- Use strong, unique API keys
- Limit network access to required ports only
- Implement proper logging and monitoring

## Vulnerability Response

We take security seriously and will:

1. Acknowledge receipt of vulnerability reports within 48 hours
2. Provide an initial assessment within 5 business days
3. Work on fixes with appropriate urgency based on severity
4. Credit security researchers (if desired) in our security advisories

## Contact

For security-related concerns, please contact the project maintainers directly rather than using public channels.
