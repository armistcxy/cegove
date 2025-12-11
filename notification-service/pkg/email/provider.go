package email

import "context"

// EmailProvider supplies the interface for most use cases of working with emails
type EmailProvider interface {
	SendEmail(ctx context.Context, msg *EmailMessage) (*SendResult, error)
	SendTemplateEmail(ctx context.Context, templateID string, to []string, data map[string]interface{}) (*SendResult, error)
	SendBulkEmail(ctx context.Context, messsages []EmailMessage) ([]SendResult, error)
	GetProviderName() string
}
